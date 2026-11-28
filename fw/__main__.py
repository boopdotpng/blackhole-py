# python3 -m fw [dir]: the firmware tinygrad's TT backend boots, one L1 image per core type and DRAM bank count.
# Each image is written at L1 address 0 and starts with the jump to its BRISC entry. The host fills in what depends on
# the card: CP_ALL_NRECTS/CP_ALL_RECTS for the CP, LEADER_COORD, NUM_WORKERS and GRID_COLS_L1 for a worker.
import hashlib, struct, sys
from pathlib import Path
import fw
from hw import isa

def image(*parts: tuple[int, bytes]) -> bytes:
  out = bytearray(max(base + len(code) for base, code in parts))
  for base, code in parts: out[base:base + len(code)] = code
  out[:4] = struct.pack("<I", isa.jal(imm=parts[0][0]))
  return bytes(out)

def images(banks: int) -> dict[str, bytes]:
  dma, (worker, pcs) = fw.dma_images(banks), fw.worker_images(banks)
  header = bytearray(fw.WORKER_FW_BASE)
  struct.pack_into("<I", header, fw.DRAM_BANKS_L1, banks)
  struct.pack_into("<4I", header, fw.ROLE_PC, *(pcs[r] for r in fw.ROLES[1:]))
  return {"dma": image((fw.DMA_BRISC_BASE, dma[0]), (fw.DMA_NCRISC_BASE, dma[1])), "cp": image((fw.CP_BRISC_BASE, fw.cp_image(banks))),
          "worker": image((pcs["brisc"], worker), (0, bytes(header)))}

if __name__ == "__main__":
  out = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
  out.mkdir(parents=True, exist_ok=True)
  for banks in (7, 8):
    for name, blob in images(banks).items():
      (out / f"{name}_b{banks}.bin").write_bytes(blob)
      print(f"{hashlib.sha256(blob).hexdigest()}  {name}_b{banks}.bin  {len(blob)}")
