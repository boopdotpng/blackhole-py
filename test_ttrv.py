"""ttrv front end tests: python test_ttrv.py (or pytest). No hardware needed."""
import pathlib
from ttrv.parse import Error, parse, show, Assign, Op, Block, Name
from ttrv.expand import expand

EXAMPLE = pathlib.Path(__file__).parent / "kernels/o.ttrv"

def prog(src, **defines): return expand(parse(src, "t.ttrv"), defines)

def fails(src, id, **defines):
  try: prog(src, **defines)
  except Error as e:
    assert e.id == id, f"expected {id}, got {e.id}: {e}"
    return e
  raise AssertionError(f"expected error {id}")

def test_example_round_trip():
  decls = parse(EXAMPLE.read_text(), str(EXAMPLE))
  text = show(decls)
  assert show(parse(text)) == text

def test_example_expands():
  p = expand(parse(EXAMPLE.read_text(), str(EXAMPLE)))
  assert p.grid == 88 and p.consts["DIM"] == 2048 and list(p.params) == ["context", "matrix", "output", "residual"]
  assert p.cbs["weights"].type.count == 1024
  # brisc reads first, count, lo; not lead
  pre = [a.targets[0].id for a in p.fns["brisc"].body if isinstance(a, Assign) and any(a is s for s in p.shared)]
  assert pre == ["first", "lo"]
  assert [a.targets[0].id for a in p.fns["ncrisc"].body[:2]] == ["first", "lead"]
  assert p.fns["trisc1"].body[0].targets[0].id == "first"   # loop count needs count
  assert [type(s).__name__ for s in p.templates["dot_face"].body] == ["Label"] * 3

def test_expand_D():
  p = expand(parse(EXAMPLE.read_text()), {"EMBED_TILES": "4"})
  assert p.consts["DIM"] == 4096
  fails("grid 1\nconst A = 1", "define.unknown", B="2")

def test_syntax():
  p = prog("""
grid 4
const A = 0x10 + 0b1_0   // 18
l1 buf: u32[A * 2], align=128
fn brisc() {
  x = 1; y = x << 2
  if x == 1 && y != 0 { x += 1 } else if y { x = 3 } else {
    x = 4
  }
  buf[x] = y
  noc.wait
  t = noc.read buf,
    remote(1, 2, buf), n=4
  noc.wait t
}""")
  assert p.consts["A"] == 18 and p.l1["buf"].type.count == 36
  body = p.fns["brisc"].body
  assert isinstance(body[-2], Assign) and isinstance(body[-2].value, Op) and len(body[-2].value.args) == 3

def test_folding():
  p = prog("grid 8\nconst A = -7 / 2\nconst B = -7 % 2\nconst C = ~31\nconst D = grid.size * bf16.tile\nconst E = u32(-1)")
  assert p.consts == {"A": -3, "B": -1, "C": 0xFFFFFFE0, "D": 8 * 2048, "E": 0xFFFFFFFF}
  fails("grid 1\nconst A = 1 << 32", "const.shift")
  fails("grid 1\nconst A = 0x8000_0000 * 2", "const.range")
  fails("grid 1\nconst A = 1 / 0", "const.div0")
  fails("grid 1\nconst A = bfp8.size", "type.size")
  fails("grid 1\nfn brisc() { repeat core.x { fence } }", "const.required")

def test_file_level_if():
  src = "grid 1\nconst BIG = 0\nif BIG { const N = 8 } else { const N = 4 }"
  assert prog(src).consts["N"] == 4
  assert prog(src, BIG="1").consts["N"] == 8

def test_repeat_and_const_if():
  p = prog("grid 1\nfn trisc1() { repeat i in 1..3 { if i == 2 { sfp.nop } else { sfp.mov l0, l1 } }; repeat 0 { sfp.nop } }")
  b = p.fns["trisc1"].body
  # each repeat copy is a Block; a constant if splices its branch into it with no Block of its own (spec §3)
  assert len(b) == 2 and all(isinstance(s, Block) for s in b)
  assert b[0].body[0].name == "mov" and b[1].body[0].name == "nop"

def test_const_if_splices():
  p = prog("grid 1\nconst F = 1\nfn brisc() { if F { x = 2 } else { y = 3 }; z = x + 1 }")
  b = p.fns["brisc"].body
  assert [type(s).__name__ for s in b] == ["Assign", "Assign"] and b[0].targets[0].id == "x"
  p = prog("const F = 1\nif F { grid 96\ntype W = e4m3 } else { grid 88\ntype W = bf16 }\nparam m: W[]\ncb c: W[16], pages=1")
  assert p.grid == 96 and p.params["m"].type.name == "e4m3" and p.cbs["c"].type.name == "e4m3"
  assert prog("grid 1\ntype W = bf16\nconst S = W.size", W="fp32").consts["S"] == 4

def test_params():
  p = prog("grid 1\nparam a: bf16[]\nparam h: u32[], host\nparam pos: u32\nshared { blocks = pos / 32 + 1 }\nfn trisc1() { x = blocks }")
  assert not p.params["pos"].type.buf and p.params["a"].type.buf
  fails("grid 1\nparam a: bf16", "param.type")
  fails("grid 1\nparam n: u32 in 0..8", "parse.syntax")

def test_macro_hygiene():
  p = prog("""
grid 1
cb q: u32[16], pages=2
macro put(q, v) { p = cb.reserve q; p[0] = v; cb.push q }
fn brisc() { p = 5; put!(q, p); put!(q, p + 1) }""")
  b = p.fns["brisc"].body
  m1, m2 = b[1], b[2]
  assert m1.macro == "put" and m1.body[0].targets[0].id != "p" and m1.body[0].targets[0].id != m2.body[0].targets[0].id
  assert m1.body[1].value == Name("p", m1.body[1].value.loc)   # the argument still means the caller's p
  assert m1.body[0].loc.via and m1.body[0].loc.via[0].line == 5
  fails("grid 1\nmacro m() { m!() }\nfn brisc() { m!() }", "macro.recursive")
  fails("grid 1\nmacro m() { break }\nfn brisc() { loop { m!(); break } }", "loop.outside")
  fails("grid 1\nmacro m() { return }\nfn brisc() { m!() }", "macro.return")
  fails("grid 1\nmacro m(a) { a = 1 }\nfn brisc() { m!(3) }", "assign.const")

def test_shared():
  fails("grid 2\nshared { a = core.x }\nfn f() { return a }\nfn brisc() { x = f() }", "shared.entry")
  fails("grid 2\nl1 b: u32[4]\nshared { a = b[0] }", "shared.uniform")
  fails("grid 2\nshared { a = 1 }\nfn brisc() { a = 2 }", "name.shadow")
  p = prog("grid 2\nshared { a = core.x\n b = a + 1\n c = 7 }\nfn brisc() { x = b }\nfn ncrisc() { }")
  assert [s.targets[0].id for s in p.fns["brisc"].body[:2]] == ["a", "b"] and p.fns["ncrisc"].body == []

def test_scopes_and_calls():
  fails("grid 1\nfn brisc() { if 1 == core.x { y = 1 }\n z = y }", "name.unknown")
  fails("grid 1\nfn brisc() { for i in 0..4 { i = 2 } }", "assign.for")
  fails("grid 1\nconst N = 1\nfn brisc() { N = 2 }", "assign.const")
  fails("grid 1\nfn brisc() { loop { fence } }", "loop.exit")
  fails("grid 1\nfn brisc() { break }", "loop.outside")
  fails("grid 1\nfn f(a) { return a, a }\nfn brisc() { x = f(1) }", "call.results")
  fails("grid 1\nfn f(a) { return a }\nfn brisc() { x = f(1) + 1 }", "call.expr")
  fails("grid 1\nfn f() { g() }\nfn g() { f() }\nfn brisc() { f() }", "call.cycle")
  fails("grid 1\nfn f() { if core.x { return 1 }\n return }", "return.count")
  p = prog("grid 1\nfn f(a: i32, p: bf16*) { return a, a }\nfn brisc() { x, y = f(i32(1), 0) }")
  assert p.fns["f"].nret == 2 and p.calls["brisc"] == ["f"]

def test_templates():
  fails("grid 1\nmop m, outer=1 { math.elwadd }", "template.label")
  fails("grid 1\nreplay r { a: sfp.nop }", "parse.syntax")
  fails("grid 1\nmop m, outer=1 { loop0: x = 1 }", "template.stmt")
  fails("grid 1\nfn brisc() { a: fence }", "parse.syntax")
  p = prog("grid 1\nmacro two() { loop0: sfp.nop; loop1: sfp.nop }\nmop m, outer=2 { two!() }\nreplay r { repeat 3 { sfp.nop } }")
  assert [s.label for s in p.templates["m"].body] == ["loop0", "loop1"] and len(p.templates["r"].body) == 3

def test_decl_errors():
  fails("const A = 1", "grid.missing")
  fails("grid 1\ngrid 2", "grid.dup")
  fails("grid 1\nconst A = 1\nl1 A: u8[4]", "name.dup")
  fails("grid 1\nl1 math: u8[4]", "name.reserved")
  fails("grid 1\nsem a = math_pack\nsem b = math_pack", "sem.alias")
  fails("grid 1\nl1 x: bfp8[10]", "type.bfp")
  fails("grid 1\nfn brisc() { noc.read x, n=1, n=2 }", "arg.dup")

def test_lex_errors():
  for src, id in (("grid 1 $", "lex.char"), ("grid 1 /* x", "lex.comment"), ("grid 12ab", "lex.number"),
                  ("grid 1\nfn brisc() {", "parse.unclosed")):
    try: parse(src)
    except Error as e: assert e.id == id, (src, e)
    else: raise AssertionError(src)

def test_build_projection():
  from ttrv import build
  import fw
  for tiles in (2,4):
    kernel=build(EXAMPLE.read_text(),{"EMBED_TILES":tiles},str(EXAMPLE))
    assert list(kernel.images)==list(fw.ROLES)
    for role,image in kernel.images.items():
      assert image.endswith(fw.ret(role)) and len(image)<=fw.CODE_SIZE[role]
      assert str(EXAMPLE) in kernel.listing[role]
    assert kernel.manifest["storage"]["weights"]["pages"]==tiles*2
    assert kernel.manifest["storage"]["dot"]["consumer"]=="ncrisc"
    assert kernel.manifest["params"]["residual"]["slot"]==3
  emb = pathlib.Path(__file__).parent / "kernels/embedding.ttrv"
  kernel = build(emb.read_text(), {}, str(emb))
  assert kernel.manifest["params"]["token_pos"] == dict(slot=4, kind="int", type="u32")  # 8-byte aligned for STORE
  blob = bytearray(kernel.args_size)
  kernel.bind(blob, 0, dict(token_pos=77))
  assert blob[16:24] == (77).to_bytes(8, "little")

def test_native_unpack_face():
  from ttrv import build, isa
  ops = "unpack.face a, next_l1_face, dvalid; unpack.face b, next_l1_face, dvalid"
  image = build("grid 1\nfn trisc0() { " + ops + " }").images["trisc0"]
  # Exported gate UNPACR words for SrcA and SrcB. Each face is exactly one slot.
  words = (0x420080c1, 0x428080c1)
  assert b"".join(isa.inline(w).to_bytes(4, "little") for w in words) in image
  src = "grid 1\nmop pair, outer=4, inner=1 { start: " + ops.replace("; ", "; loop0: ") + " }"
  kernel = build(src + "\nfn trisc0() { mop.load pair; mop.run pair }")
  assert kernel.listing["trisc0"].count("  MOP ") == 1

def test_backend_checks():
  from ttrv import build
  replay="replay r { sfp.nop }\n"
  fixtures=[
    (replay+"fn trisc1(){ if core.x { replay.load r }; replay.run r }","state.required"),
    (replay+"fn f(){ replay.run r }\nfn trisc1(){ f() }","state.required"),
    ("fn f(){ if core.x { return core.y } }\nfn brisc(){ x=f() }","state.required"),
    ("fn trisc0(){ unpack.face a|b }","unpack.face"),
    ("fn trisc0(){ unpack.face b, ctx=2 }","arg.range"),
    ("mop m { loop0: unpack.move a, core.x }\nfn trisc0(){ mop.load m }","template.body"),
    ("fn brisc(){ sfp.nop }","op.role"),
    ("l1 a: u32[16]\nparam b: u32[]\nfn trisc1(){ noc.read a, b[0], n=1, wait }","op.role"),
    ("fn trisc1(){ math.addrmod s, slot=0, dst+=2 }","math.addrmod"),
    ("fn trisc1(){ math.rwc reset, dst+=1 }","math.rwc"),
    ("l1 x: u32[1]\nfn brisc(){ y=x[1] }","index.bounds"),
    ("l1 x: u32[4]\nfn brisc(){ t=noc.read x, remote(0,0,x), n=4 }","noc.pending"),
    ("sem s = math_pack, max=3\nfn trisc1(){ sem.inc s }","state.required"),
    ("fn trisc1(){ sfp.mov l8,l0 }","arg.enum"),
    ("fn trisc0(){ unpack.move b, core.x, ctx=2 }","arg.range"),
    ("l1 x: fp32[500000]","storage.overflow"),
    ("fn brisc(){ x=i32(1); x=u32(2) }","type.assign"),
  ]
  for src,id in fixtures:
    try: build("grid 1\n"+src)
    except Error as e: assert e.id==id,(src,e)
    else: raise AssertionError(src)
  build("grid 1\nmop m, mask { repeat 4 { a: sfp.nop } }\nfn trisc1(){ mop.load m; mop.run m, mask=0, n=4 }")
  build("grid 1\n"+replay+"fn f(){ replay.run r }\nfn trisc1(){ replay.load r; f() }")

def test_branch_relaxation():
  from ttrv import build
  from ttrv.isa import rv_decode
  import struct
  image=build("grid 1\nfn brisc(){ if core.x { repeat 1050 { fence } } }").images["brisc"]
  instructions=[rv_decode(w) for w, in struct.iter_unpack("<I",image)]
  j=next(i for i,(op,_) in enumerate(instructions) if op=="bne")
  assert instructions[j][1]["imm"]==8
  assert instructions[j+1][0]=="jal" and instructions[j+1][1]["imm"]>4096

if __name__ == "__main__":
  for k, f in list(globals().items()):
    if k.startswith("test_"): f(); print("ok", k)
