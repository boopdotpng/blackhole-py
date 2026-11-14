"""Hardware regression for repeated CALLs: python test_graph.py --device 1."""
import argparse, struct
import fw
from ops_blackhole import BlackholeComputeQueue, BlackholeDevice, BlackholeGraph, BlackholeSignal


def check_repeated_call(device):
  dev = BlackholeDevice(f"BLACKHOLE:{device}")
  try:
    count, packets = 270, 131  # cross GRAPH_CHUNK, with 32 bytes of padding between graph instances
    host = dev.alloc_host(count * 64)
    signal = BlackholeSignal(dev, host)
    q, patches = BlackholeComputeQueue(), []
    for value in range(1, packets + 1):
      patches += [(len(q._q) + 8, 64), (len(q._q) + 16, 1000)]
      q.signal(signal, value)
    # Cross the low address word's rollover without allocating/uploading 4 GiB.
    dev.allocator.dram_top = (1 << 32) - fw.RING_SIZE
    graph = BlackholeGraph(dev, q, count, patches)
    assert graph.size % 64 == 32
    before = dev.compute_queue.put_value
    graph(3, 257)
    assert (dev.compute_queue.put_value - before) & 0xFFFFFFFF == 2 * fw.PACKET
    for i in range(count):
      value = struct.unpack_from("<Q", dev.sysmem.mem, host + i * 64)[0]
      assert value == (1000 * i + packets if 3 <= i < 260 else 0), (i, value)
    graph(269)  # single-instance decode uses the same CALL format
    assert struct.unpack_from("<Q", dev.sysmem.mem, host + 269 * 64)[0] == 269000 + packets
    # Old callers with b=0 still execute once.
    BlackholeComputeQueue().q(fw.Op.CALL, graph.addr, 0, graph.size).signal(dev.timeline_signal, dev.next_timeline()).submit(dev)
    dev.synchronize()
    assert signal.value == packets
  finally:
    dev.close()


if __name__ == "__main__":
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument("--device", type=int, default=0)
  check_repeated_call(ap.parse_args().device)
  print("repeated CALL: passed")
