#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness
import numpy as np
import struct
import argparse
from device import Device
from program import Program, Dtype
from asm import KernelBase
from ttk.math import Math
from ttk.pack import Pack
from ttk.sfpu import sfpu_load_fp32_const
from ttk.tensix import MopCfg, TensixStall, TensixWait, TensixSem, Tensix
from dsl import (
    TTNOP, TTSFPNOP, TTSFPLOADI, TTSFPSTORE, TTSETRWC, TTPACR, TTSEMINIT,
    TTSEMPOST, TTSEMWAIT, TTSEMGET, TTSTALLWAIT, t1, t2, zero, s0, s1, t0, t3, TTZEROACC, TTDMANOP, TTSETADCXY, TTSETADCZW
)

OUT_CB = 16
PACK_MOP_CFG = MopCfg(
  loop_outer=4, loop_inner=4,
  template=[
    TTNOP(), TTNOP(), TTNOP(),
    TTPACR(),
    TTNOP(),
    TTPACR(AddrMode=1, Last=1),
    TTPACR(AddrMode=2),
  ],
)

def build_trisc1(fmt: str, sfpu_fmt_val: int) -> KernelBase:
    class TriscKernel(KernelBase, Tensix): pass
    fw = TriscKernel()
    fw.math = Math(fw)
    fw.data = {"dest_offset_id": 0xFFB00080}
    fw.math.init(dtype=Dtype.Float16_b, mop_cfg=MopCfg(loop_outer=1, loop_inner=1, template=[TTNOP()]))
    
    fw.emit(TTSEMINIT(sem_sel=TensixSem.mask(TensixSem.MATH_PACK), init_value=0, max_value=2))
    
    fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.SFPU))
    fw.tensix_sync(1, tmp=t1)

    # Seed LReg 0 to 7
    values = (0.0, 1.0, -1.0, 2.0, 0.5, -0.5, 16.0, -16.0)
    if fmt == "rawbits":
        rawbits = (0x00000000, 0x3F800000, 0xBF800000, 0x12345678, 0xDEADBEEF, 0x80000001, 0x7FC01234, 0xCAFEBABE)
        for lreg, value in enumerate(rawbits):
            fw.emit(TTSFPLOADI(lreg, 8, value >> 16))
            fw.emit(TTSFPNOP())
            fw.emit(TTSFPLOADI(lreg, 10, value & 0xFFFF))
            fw.emit(TTSFPNOP())
    else:
        for lreg, value in enumerate(values):
            sfpu_load_fp32_const(fw, lreg, value)

    # store to Dest
    fw.emit(TTSETRWC(0, 0, 0, 0, 0, 15))
    for lreg in range(8):
        fw.emit(TTSFPSTORE(lreg, sfpu_fmt_val, 7, lreg * 4))
    fw.emit(TTSFPNOP())
    fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.SFPU))
    fw.tensix_sync(1, tmp=t1)

    # Commit to pack
    fw.emit(TTSTALLWAIT(TensixStall.SYNC, TensixWait.MATH | TensixWait.SFPU))
    fw.emit(TTSEMPOST(TensixSem.mask(TensixSem.MATH_PACK)))
    fw.tensix_sync(1)
    
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(fw.data["dest_offset_id"], t2)

    return fw.ret()

def build_trisc2(dtype: Dtype, fp32_dest: bool) -> KernelBase:
    class TriscKernel(KernelBase, Tensix): pass
    fw = TriscKernel()
    fw.pack = Pack(fw)
    fw.data = {"dest_offset_id": 0xFFB00080, "cb_interface": 0xFFB10000}
    fw.pack.init(dtype=dtype, out_cb=OUT_CB, mop_cfg=PACK_MOP_CFG, fp32_dest=fp32_dest)
    
    fw.emit(TTSEMWAIT(
        TensixStall.TDMA,
        TensixSem.mask(TensixSem.MATH_PACK),
        0, # STALL_ON_ZERO
    ))
    
    fw.cb_reserve_back(fw.data["cb_interface"], OUT_CB, 1)
    fw.cb_write_ptr(fw.data["cb_interface"], OUT_CB, out=s0)
    
    # packer offset setup
    fw.cb_iface(fw.data["cb_interface"], OUT_CB, out=t6)
    fw.lw(s4, t6, 8)
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.li(t2, 0)
    pack_offset_ready = fw._new_label("pack_offset_ready")
    fw.beq(t1, zero, pack_offset_ready)
    fw.li(t2, 512)
    fw.label(pack_offset_ready)
    fw.write32(0xFFB12140, t2) # DEST_TARGET_REG_CFG_PACK_SEC0
    fw.write32(0xFFB12144, t2)
    fw.write32(0xFFB12148, t2)
    fw.write32(0xFFB1214C, t2)
    
    fw.mv(s3, s0)
    fw.addi(s0, s3, -1)

    # Pack 1 tile
    fw.emit(TTSETADCXY(4, 0, 0, 0, 0, 11))
    fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 15))
    fw.mop_sync(2, tmp=t1)
    fw.write_mop_cfg(PACK_MOP_CFG, 2)
    fw.emit(TTNOP())
    fw.emit(TTNOP())
    fw.emit(TTNOP())
    fw.mop_run(1, 2) # run MOP
    fw.mop_sync(2, tmp=t1)
    fw.emit(TTSETADCZW(4, 0, 0, 0, 0, 5))
    
    fw.cb_push_back(fw.data["cb_interface"], OUT_CB, 1, tensix_received=True)
    fw.emit(TTSTALLWAIT(TensixStall.THCON, TensixWait.PACK0))
    
    fw.read32(t1, fw.data["dest_offset_id"])
    fw.andi(t2, t1, 1)
    # ZEROACC + dest parity
    fw.li(t3, TTZEROACC(2, 0, 0, 1).raw_word()) 
    fw.add(t2, t2, t3)
    fw.write32(0xFFB12028, t2) # INSTRN_BUF_BASE
    
    fw.emit(TTSEMGET(TensixSem.mask(TensixSem.MATH_PACK)))
    
    fw.li(t2, 1)
    fw.sub(t2, t2, t1)
    fw.write32(fw.data["dest_offset_id"], t2)
    fw.emit(TTDMANOP())
    fw.emit(TTDMANOP())
    
    return fw.ret()

def run_pack(device: Device, core, fmt: str) -> bytes:
    # Set formats based on requested format
    # SFPU_FMT: FP32 = 3, INT32 = 4
    if fmt == "fp32":
        sfpu_fmt_val = 3
        packer_dtype = Dtype.Float32
        fp32_dest = True
        tile_bytes = 1024 * 4
    elif fmt == "int32":
        sfpu_fmt_val = 4
        packer_dtype = Dtype.Int32
        fp32_dest = True # Need to read 32-bit from dest for Int32 as well
        tile_bytes = 1024 * 4
    elif fmt == "rawbits":
        # Usually RAW32 (7) but use INT32 (4) to pack it correctly
        sfpu_fmt_val = 4 
        packer_dtype = Dtype.UInt32
        fp32_dest = True
        tile_bytes = 1024 * 4
    else:
        raise ValueError(fmt)

    empty = KernelBase().ret()
    trisc1 = build_trisc1(fmt, sfpu_fmt_val)
    trisc2 = build_trisc2(packer_dtype, fp32_dest)
    trisc2.rta(lambda _x, _y: [])
    
    prog = Program(
        brisc=empty,
        ncrisc=empty,
        trisc0=empty,
        trisc1=trisc1,
        trisc2=trisc2,
        cbs=[(OUT_CB, tile_bytes, 2)],
        semaphores=2,
        num_cores=1,
    )
    
    device.run(prog)
    
    # Read L1 where CB 16 is
    # In Program layout, CB 16 is the first one, starts at 0x210000 
    # (actually we should look up the address in the device or use fixed 0x210000)
    with harness.device_window(device, core) as win:
        # Assuming CB 16 starts at 0x210000 and the first tile is written there
        # but there is a 16-byte tile header prepended by the packer!
        # A tile in Float32 is 4096 bytes data + 16 bytes header = 4112 bytes
        # Wait, the CB layout has tile header at the beginning of the CB buffer.
        # Let's read the whole thing: 4112 bytes
        blob = win.read(0x210000, tile_bytes + 32)
        
    return blob

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fmt", choices=["fp32", "int32", "rawbits"], default="fp32")
    args = parser.parse_args()
    with harness.open_device() as device:
        core = device.cores[0]
        blob = run_pack(device, core, args.fmt)
    
    print(f"Read {len(blob)} bytes from L1.")
    # Skip the 16-byte tile header to read the 1024 elements
    header = blob[:16]
    data = blob[16:16+4096]
    words = np.frombuffer(data, dtype="<u4")
    print("Tile header:", header.hex())
    print("First 32 words:")
    for i in range(32):
        print(f"{words[i]:08x}")
    
if __name__ == "__main__":
    main()
