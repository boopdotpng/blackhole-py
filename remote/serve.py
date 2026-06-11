#!/usr/bin/env python3
from __future__ import annotations

import argparse, contextlib, json, os, pickle, socket, struct, time
from dataclasses import asdict

os.environ["BLACKHOLE_REMOTE_SERVER"] = "1"

from pcie import NocOrdering, PCIDevice, TLBWindow  # noqa: E402
from remote.remote_pcie import REQ, RESP, PORT, Cmd, jpack, layout_fix  # noqa: E402
from program import DevMsgs, GoMsg, McastMmioWrite32, McastWrite, PollL1Byte, Run, UnicastWrite, mcast_rects  # noqa: E402
from ttk.addrs import Dram, align_down  # noqa: E402
from ttk.tensix import TensixL1  # noqa: E402

devices: dict[int, PCIDevice] = {}
maps: dict[int, object] = {}
next_dev = 1
next_map = 1


def resp(r0=0, r1=0, status=0): return struct.pack(RESP, status, r0, r1)
def err(e: Exception):
  data = str(e).encode()
  return resp(len(data), 0, 1) + data


def _recv(conn: socket.socket, n: int) -> bytes:
  data = b""
  while len(data) < n and (chunk := conn.recv(n - len(data), socket.MSG_WAITALL)):
    data += chunk
  if len(data) != n: raise ConnectionError("client disconnected")
  return data


def _add_map(mm) -> tuple[int, int]:
  global next_map
  h = next_map
  next_map += 1
  maps[h] = mm
  return h, len(mm)


def _open(index: int, use_vfio: bool):
  global next_dev
  dev_id = next_dev
  next_dev += 1
  dev = PCIDevice(index=index, use_vfio=use_vfio)
  devices[dev_id] = dev
  return dev_id, dev


def _first_core(commands):
  for cmd in commands:
    match cmd:
      case UnicastWrite(cores=cores) | Run(cores=cores):
        if cores: return cores[0]
      case McastWrite(rects=rects) | McastMmioWrite32(rects=rects):
        if rects: return (rects[0][0], rects[0][2])
      case PollL1Byte(core=core):
        return core
  return None


def _run_ir(dev: PCIDevice, commands):
  start = _first_core(commands)
  if start is None:
    return
  with TLBWindow(dev, start=start) as win:
    for cmd in commands:
      match cmd:
        case UnicastWrite(cores=cores, addr=addr, data=data):
          for core, blob in zip(cores, data):
            win.target(core)
            win.write(addr, blob)
        case McastWrite(rects=rects, addr=addr, data=data):
          for x0, x1, y0, y1 in rects:
            win.target((x0, y0), (x1, y1))
            win.write(addr, data)
        case McastMmioWrite32(rects=rects, addr=addr, value=value):
          mmio_base, _ = align_down(addr, TLBWindow.SIZE_2M)
          for x0, x1, y0, y1 in rects:
            win.target((x0, y0), (x1, y1), addr=mmio_base)
            win.write(addr - mmio_base, struct.pack("<I", value & 0xFFFFFFFF))
        case PollL1Byte(core=core, addr=addr, value=value, timeout_s=timeout_s):
          win.target(core)
          deadline = time.perf_counter() + timeout_s
          while win.read(addr, 1)[0] != value:
            if time.perf_counter() > deadline:
              dump = getattr(dev, "dump_t_state", None)
              if dump is not None: dump()
              raise TimeoutError(f"timeout waiting for L1[0x{addr:x}] == 0x{value:02x} on core {core}")
            time.sleep(0.001)
        case Run(cores=cores):
          go = GoMsg()
          go.bits.signal = DevMsgs.RUN_MSG_GO
          go_blob = struct.pack("<I", go.all)
          timeout_s = float(os.environ.get("BLACKHOLE_RUN_TIMEOUT_S", "10.0"))
          for x0, x1, y0, y1 in mcast_rects(cores):
            win.target((x0, y0), (x1, y1))
            win.write(TensixL1.GO_MSG, go_blob)
          for core in cores:
            win.target(core)
            deadline = time.perf_counter() + timeout_s
            while win.read(TensixL1.GO_MSG + 3, 1)[0] != DevMsgs.RUN_MSG_DONE:
              if time.perf_counter() > deadline:
                dump = getattr(dev, "dump_t_state", None)
                if dump is not None: dump()
                raise TimeoutError(f"timeout waiting for core {core}")
              time.sleep(0.001)


def _dram_barrier(win: TLBWindow, bank_tiles):
  for flag in Dram.BARRIER_FLAGS:
    for _, x, y in bank_tiles:
      win.target((x, y))
      win.write(Dram.BARRIER_BASE, struct.pack("<I", flag))
      while struct.unpack("<I", win.read(Dram.BARRIER_BASE, 4))[0] != flag:
        pass


def _dram_write(dev: PCIDevice, bank_tiles, buf, data: bytes):
  assert len(data) <= buf.size
  with TLBWindow(dev, start=bank_tiles[0][1:], size=TLBWindow.SIZE_4G, wc=True) as win:
    view, ps, nb = memoryview(data), buf.page_size, len(bank_tiles)
    n_pages = (len(data) + ps - 1) // ps
    for bi, (_, x, y) in enumerate(bank_tiles):
      bank_data = b"".join(bytes(view[p * ps : p * ps + ps]) for p in range(bi, n_pages, nb))
      if not bank_data: continue
      win.target((x, y), mode=NocOrdering.POSTED)
      win.write(buf.addr, bank_data)
    _dram_barrier(win, bank_tiles)


def _dram_read(dev: PCIDevice, bank_tiles, buf) -> bytes:
  with TLBWindow(dev, start=bank_tiles[0][1:], size=TLBWindow.SIZE_4G, wc=True) as win:
    result, ps, nb = bytearray(buf.size), buf.page_size, len(bank_tiles)
    n_pages = (buf.size + ps - 1) // ps
    for bi, (_, x, y) in enumerate(bank_tiles):
      bank_pages = list(range(bi, n_pages, nb))
      if not bank_pages: continue
      win.target((x, y), mode=NocOrdering.RELAXED)
      bank_data = win.read(buf.addr, len(bank_pages) * ps)
      for i, p in enumerate(bank_pages):
        n = min(ps, buf.size - p * ps)
        result[p * ps : p * ps + n] = bank_data[i * ps : i * ps + n]
    return bytes(result)


def handle(conn: socket.socket, cmd: int, dev_id: int, handle: int, arg0: int, arg1: int, arg2: int):
  cmd = Cmd(cmd)
  if cmd == Cmd.LIST:
    data = "\n".join(PCIDevice.list_devices()).encode()
    return conn.sendall(resp(len(data), len(data.splitlines())) + data)
  if cmd == Cmd.OPEN:
    new_id, dev = _open(arg0, bool(arg1))
    data = jpack({"dev_id": new_id, "sysfs": dev.sysfs, "bdf": dev.bdf})
    return conn.sendall(resp(len(data), getattr(dev, "_bar4_4g_count", 0)) + data)
  if cmd == Cmd.RESET_INDEX:
    PCIDevice.reset_index(arg0)
    return conn.sendall(resp())
  if cmd == Cmd.RESET_BDF:
    PCIDevice.reset_bdf(_recv(conn, arg0).decode())
    return conn.sendall(resp())

  dev = devices[dev_id]
  if cmd == Cmd.CLOSE:
    for h, mm in list(maps.items()):
      with contextlib.suppress(Exception): mm.close()
      maps.pop(h, None)
    devices.pop(dev_id, None).close()
    return conn.sendall(resp())
  if cmd == Cmd.ALLOC_TLB: return conn.sendall(resp(dev.alloc_tlb(arg0)))
  if cmd == Cmd.FREE_TLB:
    dev.free_tlb(arg0); return conn.sendall(resp())
  if cmd == Cmd.CONFIG_TLB:
    addr, xs, ys, xe, ye, noc, mcast, ordering, linked, static_vc = struct.unpack("<QBBBBBBBBB", _recv(conn, 17))
    dev.configure_tlb(arg0, addr, xs, ys, xe, ye, noc=noc, mcast=mcast, ordering=ordering, linked=linked, static_vc=static_vc)
    return conn.sendall(resp())
  if cmd == Cmd.MAP_TLB: return conn.sendall(resp(*_add_map(dev.tlb_window(arg0, wc=bool(arg1)))))
  if cmd == Cmd.MAP_BAR4: return conn.sendall(resp(*_add_map(dev.map_bar4_window(arg0, arg1))))
  if cmd == Cmd.MAP_READ: return conn.sendall(resp(arg1) + maps[handle].read(arg0, arg1))
  if cmd == Cmd.MAP_WRITE:
    maps[handle].write(arg0, _recv(conn, arg1)); return conn.sendall(resp())
  if cmd == Cmd.MAP_CLOSE:
    mm = maps.pop(handle, None)
    if mm is not None: mm.close()
    return conn.sendall(resp())
  if cmd == Cmd.FLUSH:
    flush = getattr(maps[handle], "flush", None)
    if flush is not None: flush(arg0, arg1)
    return conn.sendall(resp())
  if cmd == Cmd.TELEMETRY_LAYOUT:
    data = jpack(dev.telemetry_layout())
    return conn.sendall(resp(len(data)) + data)
  if cmd == Cmd.TELEMETRY_TAG:
    req = json.loads(_recv(conn, arg0).decode())
    val = dev.telemetry_tag(layout_fix(req["layout"]), req["tag"])
    return conn.sendall(resp(0 if val is None else val, int(val is not None)))
  if cmd == Cmd.BOARD_INFO:
    req = json.loads(_recv(conn, arg0).decode())
    data = jpack(asdict(dev.board_info(layout_fix(req.get("layout")), req.get("fast_dispatch", False))))
    return conn.sendall(resp(len(data)) + data)
  if cmd == Cmd.ARC_READ: return conn.sendall(resp(dev.read_arc_apb32(arg0)))
  if cmd == Cmd.ARC_WRITE:
    dev.write_arc_apb32(arg0, arg1); return conn.sendall(resp())
  if cmd == Cmd.ARC_MSG:
    timeout_ms = struct.unpack("<I", _recv(conn, 4))[0]
    return conn.sendall(resp(dev.arc_msg(arg0, arg0=arg1, arg1=arg2, timeout_ms=timeout_ms)))
  if cmd == Cmd.POWER:
    dev.set_power_state(bool(arg0)); return conn.sendall(resp())
  if cmd == Cmd.RUN_IR:
    _run_ir(dev, pickle.loads(_recv(conn, arg0)))
    return conn.sendall(resp())
  if cmd == Cmd.DRAM_WRITE:
    bank_tiles, buf, data = pickle.loads(_recv(conn, arg0))
    _dram_write(dev, bank_tiles, buf, data)
    return conn.sendall(resp())
  if cmd == Cmd.DRAM_READ:
    bank_tiles, buf = pickle.loads(_recv(conn, arg0))
    data = _dram_read(dev, bank_tiles, buf)
    return conn.sendall(resp(len(data)) + data)
  raise RuntimeError(f"unknown remote command {cmd}")


def serve_conn(conn: socket.socket):
  while True:
    hdr = conn.recv(struct.calcsize(REQ), socket.MSG_WAITALL)
    if len(hdr) != struct.calcsize(REQ): raise ConnectionError("client disconnected")
    try: handle(conn, *struct.unpack(REQ, hdr))
    except ConnectionError: raise
    except Exception as e:
      if os.environ.get("REMOTE_LOG") == "1": print(f"remote error: {e}")
      conn.sendall(err(e))


def main():
  ap = argparse.ArgumentParser(description="raw TCP remote PCIe bridge for blackhole-py")
  ap.add_argument("port", nargs="?", type=int, default=PORT)
  ap.add_argument("--host", default="0.0.0.0")
  args = ap.parse_args()
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server.bind((args.host, args.port))
  server.listen(1)
  print(f"blackhole remote PCIe listening on {args.host}:{args.port}")
  try:
    while True:
      conn, addr = server.accept()
      conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      try: serve_conn(conn)
      except ConnectionError: print(f"remote PCIe disconnected: {addr}")
  except KeyboardInterrupt:
    print("\nblackhole remote PCIe stopped")


if __name__ == "__main__":
  main()
