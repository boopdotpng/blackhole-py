"""Export blackhole-py's Llama 3 decode kernels to kernels/llama3-<model>/ for llama3.py. Rerun after changing the
kernel generators in blackhole-py/examples/llama3/kernels.py or the L1 layout in fw/abi.h.

  ../.venv/bin/python tools/rewrite_export/export_llama3.py [--model 1b|8b-bf16|8b-fp8|all] [--rewrite ../blackhole-py-rewrite]

Runs blackhole-py's builders offline (no device) in its own import namespace: its cq/device/st clash with ours, so
nothing from this repo is imported. Writes, per program, one <role>[.vN].bin per distinct kernel image (minus the final
return jal, which llama1b.py links) with an annotated <role>[.vN].S listing, plus manifest.json and the RoPE tables.

How the old kernels are adapted to this runtime:
  cores       projections use an 11 x 8 block of workers (one multicast rectangle); argmax keeps
              its compact original core group, reading projection shards from DRAM
  argmax      reducer mailboxes persist outside kernel scratch and are rearmed locally, with no launch clears
  projections llama_projection.py: rows owned, DRAM port and first bank are per-core params rather than
              compiled in, so every core reading on one NoC runs the same image (one multicast per role)
  params      uniform words (same on every core) live at L1_PARAM_BASE + 4i and travel with each EXEC; per-core words
              (row starts, rows, DRAM port, shard addresses, core index) live in a resident per-core table at
              STATIC + 0x40k + 4j.
              The generators read params at PARAM_BASE + 4*slot, so PARAM_BASE is set to 0 and slot = address / 4.
  variants    where specialize() still gives cores different images (down's NoC0/NoC1 halves), each EXEC sends every
              core its own image; cores sharing one are grouped into multicast rectangles.
  8B          split attention is not exported: one attention kernel serves every position. FP8 per-layer scales
              are uniform words resolved into each launch at export.
  DRAM        blackhole-py puts tile t of a buffer in bank t % 8 at addr + (t // 8) * tile. With addr page-aligned and
              the same bank order as fw/noc.c, that is exactly dram(8 * addr, tile) here, so the DMA engine interleaves.
"""
import argparse, json, os, re, shutil, sys
from pathlib import Path

BHPY = Path(__file__).resolve().parents[2]  # this checkout
ap = argparse.ArgumentParser()
ap.add_argument("--rewrite", type=Path, default=BHPY.parent / "blackhole-py-rewrite",
                help="the blackhole-py-rewrite checkout: its fw/ ABI is read, its kernels/llama1b written")
ap.add_argument("--model", choices=("1b", "8b-bf16", "8b-fp8", "all"), default="all")
args = ap.parse_args()
REWRITE = args.rewrite.resolve()
if args.model == "all":
  import subprocess
  for m in ("1b", "8b-bf16", "8b-fp8"):
    subprocess.run([sys.executable, __file__, "--model", m, "--rewrite", str(REWRITE)], check=True)
  sys.exit()
MODEL, DTYPE = (args.model.split("-") + ["bf16"])[:2]
OUT = REWRITE / "kernels" / f"llama3-{args.model}"
os.chdir(BHPY)  # its config resolves weights/ relative to the checkout
sys.path[:0] = [str(BHPY), str(BHPY / "tools" / "viewer")]

import decode
import program as prog_mod
from program import Buffer, Dram, TensorProgram, _param_values, _param_word
from pcie import P100_WORKER_CORES, P150_DRAM_ENDPOINTS
from firmware.consts import TensixL1, Firmware, KERNEL_ROLES
from examples.llama3.config import Llama3Config
from examples.llama3 import runtime as rt
from llama_argmax import argmax, MAILBOX_BASE
import llama_projection

rt.kernels.argmax = argmax
rt.kernels.projection = llama_projection.projection
Llama3Config.split_attention = property(lambda self: False)  # one attention kernel for every position

ABI = (REWRITE / "fw" / "abi.h").read_text()
BANKS = [(int(x), int(y)) for x, y in re.findall(r"(\d+) \| (\d+) << 6", (REWRITE / "fw" / "noc.c").read_text())[:8]]
assert [e[0] for e in P150_DRAM_ENDPOINTS] == BANKS, "blackhole-py's DRAM bank order differs from fw/noc.c"
Dram.START = Dram.ALIGNMENT = 4096  # every buffer page-aligned in each bank, for any page size up to 4096
L1_PARAM_BASE = int(re.search(r"#define L1_PARAM_BASE\s+(0x[0-9A-Fa-f]+)", ABI).group(1), 16)
STATIC, ENTRY = 0x8000, 0x8400  # resident per-core tables, between DATA_BASE and the resident kernels at 0x12000
DYNAMIC = ("token_pos", "write_pos", "write_token", "start_pos", "kv_blocks", "valid_columns", "argmax_host_address")

slot_plan = {}       # param-name tuple -> {name: absolute L1 address}
program_index = {}   # param-name tuple -> k
_orig_init = TensorProgram.__init__
def _init(self, cores, *parameters, **kw):  # every specialize() variant of a program shares its slot plan
  _orig_init(self, cores, *parameters, **kw)
  if (key := tuple(p.name for p in parameters)) in slot_plan:
    for p in parameters: self._param_slots[p] = slot_plan[key][p.name] // 4
TensorProgram.__init__ = _init

class FakeCQ: noc, live = 0, 0
# The rewrite's workers on the smallest supported card (12 Tensix columns): all of x 1-7, 10-14, y 2-11 but the CQ
# and DMA service cores at the top of the rightmost column.
WORKERS = {(x, y) for x in (*range(1, 8), *range(10, 15)) for y in range(2, 12)} - {(14, 2), (14, 3)}
def block(n):
  """n workers forming one rectangle, row-major: the squarest w x h block, topmost first, from the leftmost column, so
  a launch to them is a single multicast (columns 8 and 9 are not Tensix and fall inside it)."""
  xs = sorted({x for x, _ in WORKERS})
  for h in sorted((h for h in range(1, 11) if n % h == 0 and n // h <= len(xs)), key=lambda h: abs(n // h - h)):
    for y0 in range(2, 13 - h):
      cores = [(x, y) for y in range(y0, y0 + h) for x in xs[:n // h]]
      if set(cores) <= WORKERS: return tuple(cores)
  raise ValueError(f"no rectangle of {n} workers")

class FakeDev:  # what Llama3Decode needs from a device to build programs and record one token's launches
  def __init__(self, n):
    cores = block(n)
    self.dram, self.cq, self.program_queue = Dram(8, cores, P150_DRAM_ENDPOINTS), FakeCQ(), []
  def queue(self, program, params=None): self.program_queue.append((program, params or {}))
  def capture_trace(self, names):
    q, self.program_queue = self.program_queue, []
    return q

SCALES = {}
if DTYPE == "fp8":  # FP8: per-projection input and weight scales, folded into each launch's uniform words
  import numpy as np
  from st import Safetensor
  ckpt = Safetensor(Llama3Config.create(MODEL, DTYPE).checkpoint)
  SCALES = {n: float(np.frombuffer(ckpt.load(n)[1], dtype="<f4")[0]) for n in ckpt.tensors
            if n.endswith((".input_scale", ".weight_scale"))}

def build():
  r = rt.Llama3Decode.__new__(rt.Llama3Decode)
  r.cfg = Llama3Config.create(MODEL, DTYPE)
  r.device = FakeDev(r.cfg.projection_cores)  # linspace over exactly N cores takes all N
  r.published_fp8, r.checkpoint_scales = bool(SCALES), SCALES
  r._allocate(); r._create_programs(); r._capture_decode_trace()
  return r
def key_of(p): return tuple(p.params)

# pass 1: which params differ between cores
r = build()
for p in r.programs.values():
  key = key_of(p)
  vary = {n for n, param in p.params.items() if len({_param_word(v) for v in _param_values(param, p.cores)}) > 1}
  k = program_index.setdefault(key, len(program_index))
  u, s = [n for n in p.params if n not in vary], [n for n in p.params if n in vary]
  assert len(u) <= 16 and len(s) <= 16, (key, u, s)
  slot_plan[key] = {**{n: L1_PARAM_BASE + 4 * i for i, n in enumerate(u)}, **{n: STATIC + 0x40 * k + 4 * j for j, n in enumerate(s)}}
assert len(program_index) == len(r.programs), "two programs share a param-name tuple"

# pass 2: rebuild with the remapped slots
TensixL1.PARAM_BASE = prog_mod.PARAM_BASE = 0
r = build()
cfg = r.cfg

def jal_target(word, pc):
  imm = (word >> 31 & 1) << 20 | (word >> 12 & 0xFF) << 12 | (word >> 20 & 1) << 11 | (word >> 21 & 0x3FF) << 1
  return pc + (imm - (1 << 21) if imm >> 20 else imm)

def listing(name, role, image, cores, plan):
  names = {a: n for n, a in plan.items()}
  lines = [f"# llama3 {args.model} decode: {name}, {role}. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.",
           f"# cores ({len(cores)}): {' '.join(f'{x},{y}' for x, y in cores)}",
           "# params: " + ", ".join(f"{a:#x}={n}" for a, n in sorted(names.items())),
           f"#   {L1_PARAM_BASE:#x}.. uniform, sent with every EXEC; {STATIC:#x}.. this core's resident per-core table",
           "# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.", ""]
  for row in decode.disassemble(image, 0):
    lines += [f"{label}:" for label in row["labels"]]
    ann = list(row["annotations"])
    if row.get("address") in names: ann.insert(0, f"param {names[row['address']]}")
    text = f"  {row['pc']:5x}: {row['word']:08x}  {row['op']:<12s} {row.get('operands', '')}"
    lines.append(text + (f"  # {'; '.join(ann)}" if ann else ""))
  lines.append(f"  {len(image):5x}:           j FW_{role.upper()}+4   # return to firmware, linked at install")
  return "\n".join(lines) + "\n"

out = OUT
for d in out.glob("*"):
  if d.is_dir(): shutil.rmtree(d)
out.mkdir(parents=True, exist_ok=True)

programs = {}
for name, p in r.programs.items():
  key = key_of(p); plan = slot_plan[key]; kernels = p.lower()
  uniform = [n for n in p.params if plan[n] < STATIC]
  static = [n for n in p.params if plan[n] >= STATIC]
  files, per_core = {role: [] for role in KERNEL_ROLES}, []
  images = {}  # (role, image) -> variant index
  for at, core in enumerate(p.cores):
    variant = []
    for role in KERNEL_ROLES:
      img = bytes(kernels[core].get(role, prog_mod.RETURN_KERNEL[role]))
      last = int.from_bytes(img[-4:], "little")
      assert last & 0x7F == 0x6F and jal_target(last, TensixL1.WORKER_TEXT_BASE[role] + len(img) - 4) == Firmware.TEXT[role][0], \
        f"{name}/{role}: image does not end in the firmware return"
      img = img[:-4]
      if not img: variant.append(-1); continue  # no kernel: entry points straight at the return
      if (role, img) not in images:
        images[role, img] = len(files[role]); files[role].append(img)
      variant.append(images[role, img])
    per_core.append(dict(core=core, variants=variant,
                         params=[_param_word(_param_values(p.params[n], p.cores)[at]) for n in static]))
  (out / name).mkdir()
  for role, imgs in files.items():
    for v, img in enumerate(imgs):
      stem = role if len(imgs) == 1 else f"{role}.v{v}"
      files[role][v] = f"{name}/{stem}.bin"
      (out / name / f"{stem}.bin").write_bytes(img)
      cores = [c["core"] for c in per_core if c["variants"][KERNEL_ROLES.index(role)] == v]
      (out / name / f"{stem}.S").write_text(listing(name, role, img, cores, plan))
  pre = []  # any remaining per-launch L1 writes (argmax uses persistent mailboxes instead)
  for w in p.launch:
    assert type(w).__name__ == "UnicastWrite", f"{name}: unsupported launch command {w}"
    for core, data in zip(w.cores, w.data if len(w.data) == len(w.cores) else w.data * len(w.cores)):
      pre.append(dict(core=core, addr=w.addr, data=bytes(data).hex()))
  programs[name] = dict(k=program_index[key], cores=p.cores, uniform=uniform, static=static, files=files,
                        per_core=per_core, pre=pre)

def launch_list(trace):  # one token: [program, uniform words], a name where the word changes per token
  launches = []
  for p, overrides in trace:
    resolved = {}
    for key, value in overrides.items():
      param = p.params[key] if isinstance(key, str) else key
      assert param in p.params.values(), f"override {key} matches no param"
      resolved[param] = value
    name = next(n for n, q in r.programs.items() if q is p)
    words = []
    for n in programs[name]["uniform"]:
      if n in DYNAMIC: words.append(n); continue
      vals = {_param_word(v) for v in _param_values(p.params[n], p.cores, resolved.get(p.params[n]))}
      assert len(vals) == 1, (name, n)
      words.append(vals.pop())
    for param in resolved:
      assert slot_plan[key_of(p)][param.name] < STATIC or param.name in DYNAMIC, f"{name}: per-core param {param.name} is overridden"
    launches.append([name, words])
  return launches
launches = launch_list(r.decode_trace)

def buf(b, kind, src=None):
  assert b.addr % b.tile_size == 0 and list(b.dram_endpoints) == list(P150_DRAM_ENDPOINTS), b.name
  return dict(name=b.name, addr=b.addr, tile=b.tile_size, size=b.size, kind=kind, src=src)
cos, sin = rt.rope_table(cfg)
(out / "rope_cos.bf16").write_bytes(rt._bf16_rne_bytes(cos))
(out / "rope_sin.bf16").write_bytes(rt._bf16_rne_bytes(sin))
store = lambda b: r._weight_upload_buffers.get(b, b)  # FP8 views -> their paged storage
uploads = [buf(r.embedding_weight, "tensor", "model.embed_tokens.weight"),
           *([buf(r.lm_storage, "tensor", "lm_head.weight")] if r.lm_storage is not r.embedding_weight else []),
           buf(r.cos, "file", "rope_cos.bf16"), buf(r.sin, "file", "rope_sin.bf16")]
for i, layer in enumerate(r.layers):
  for n, t in rt.LAYER_NORMS.items(): uploads.append(buf(store(layer["weights"][n]), "tensor", f"model.layers.{i}.{t}"))
  for n, (t, _) in rt.LAYER_PROJECTIONS.items(): uploads.append(buf(store(layer["weights"][n]), "tensor", f"model.layers.{i}.{t}"))
  uploads += [buf(layer["key_cache"], "zeros"), buf(layer["value_cache"], "zeros")]
uploads.append(buf(r.final_norm, "tensor", "model.norm.weight"))

manifest = dict(
  source="blackhole-py/examples/llama3", checkpoint=cfg.checkpoint,
  roles=list(KERNEL_ROLES), static_base=STATIC, entry_base=ENTRY, l1_param_base=L1_PARAM_BASE,
  dram_top=r.device.dram.allocator.next, kv_block=cfg.kv_block, max_tokens=cfg.max_tokens, eos=list(cfg.eos_token_ids),
  model=args.model, programs=programs, launches=launches,
  uploads=uploads, history=buf(r.token_history, "history"),
  persistent=[dict(name="argmax_partials", core=programs["argmax"]["cores"][0], addr=MAILBOX_BASE,
                   size=16 * len(programs["argmax"]["cores"]))],
  buffers={b.name: buf(b, "buffer") for b in vars(r).values() if isinstance(b, Buffer)})
(out / "manifest.json").write_text(json.dumps(manifest, indent=1))

print(f"{out}: {len(programs)} programs, {len(launches)} launches/token, L1_PARAM_BASE {L1_PARAM_BASE:#x}")
for name, p in programs.items():
  print(f"  {name:10s} cores={len(p['cores']):3d} uniform={len(p['uniform']):2d} static={len(p['static']):2d} "
        f"variants={max(map(len, p['files'].values()))}")
