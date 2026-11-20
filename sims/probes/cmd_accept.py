"""Sample CMD_CTRL once at a controlled instruction distance from a TTRV send."""

import argparse
import gzip
import json
from dataclasses import replace
import struct

from noc_burst import source
from role_cycles import Device, Kernel, build, firmware_fingerprint, fw, isa
from ttrv import hw


def sampler(role, op, delay, fenced):
  compiled = build(source(1, 64, op=op, role=role))
  image = compiled.images[role]
  words = [w for (w,) in struct.iter_unpack("<I", image)]
  writes = [
    (i, fields)
    for i, word in enumerate(words)
    for inst, fields in [isa.rv_decode(word)]
    if inst == "sw" and fields["imm"] % hw.CMD_BUF_STRIDE == hw.Cmd.CMD_CTRL
  ]
  if len(writes) != 1:
    raise ValueError("expected one TTRV command strobe")
  i, fields = writes[0]
  base, off = fields["rs1"], fields["imm"]
  val, addr = [j for j in (28, 29, 30, 31) if j != base][:2]
  rv = isa.rv
  # The fixed nonempty transfer always takes the send path. After the observation,
  # drain this marked request before returning to the firmware.
  suffix = ([rv("fence")] if fenced else []) + [rv("addi", 0, 0, imm=0)] * delay
  suffix += [
    rv("lw", val, base, imm=off),
    rv("lui", addr, imm=(fw.PROFILE_RECORD + 2048) >> 12),
    rv("sw", rs1=addr, rs2=val, imm=(fw.PROFILE_RECORD + 2048) % 4096 - 2048),
    rv("lw", val, base, imm=off),
    rv("bne", rs1=val, rs2=0, imm=-4),
  ]
  outstanding = hw.NIU[role] + hw.outstanding(1)
  suffix += [
    rv("lui", addr, imm=(outstanding + 2048) >> 12),
    rv("lw", val, addr, imm=(outstanding + 2048) % 4096 - 2048),
    rv("bne", rs1=val, rs2=0, imm=-4),
    rv("fence"),
  ]
  return replace(
    compiled, images={role: image[: 4 * (i + 1)] + struct.pack(f"<{len(suffix)}I", *suffix) + fw.ret(role)}
  )


def main():
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument("--device", type=int, default=0)
  p.add_argument("--output", required=True)
  args = p.parse_args()
  dev = Device(args.device)
  try:
    buf = dev.zeros(1024, "u32")
    with gzip.open(args.output, "xt") as out:
      for role, op in (("brisc", "read"), ("ncrisc", "write")):
        for fenced in (False, True):
          counts = []
          for delay in range(25):
            run = Kernel(dev, sampler(role, op, delay, fenced))
            samples = []
            for i in range(21):
              run(input=buf)
              dev.synchronize()
              samples.append(struct.unpack("<I", dev.dev.iface.read((1, 2), fw.PROFILE_RECORD, 4))[0])
            counts.append(sum(samples))
          rec = dict(
            card=args.device,
            firmware=firmware_fingerprint(),
            role=role,
            op=op,
            fenced=fenced,
            repetitions=21,
            busy_counts=counts,
          )
          print(json.dumps(rec), file=out, flush=True)
          print(rec, flush=True)
  finally:
    dev.close()


if __name__ == "__main__":
  main()
