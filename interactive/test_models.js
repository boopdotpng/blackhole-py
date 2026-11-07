// Checks for the explorer models: every preset runs, and the cases confirmed on hardware come out as the card did.
// Run: node interactive/test_models.js
const fs = require("fs"), path = require("path"), assert = require("assert");
const T = require("./common.js"), P = require("./packer_model.js"), U = require("./unpacker_model.js");
const dir = __dirname;
let failed = 0;
function test(name, fn) { try { fn(); console.log("ok  ", name); } catch (e) { failed++; console.log("FAIL", name, "\n     ", e.message); } }
function presets(file, start) {
  const html = fs.readFileSync(path.join(dir, file), "utf8");
  return eval(html.slice(html.indexOf(start), html.indexOf("// ***** state *****")) + ";PRESETS");
}
function run(M, preset, edit = {}) {
  const c = M.defaultConfig();
  for (const [k, v] of Object.entries({...preset.cfg, ...edit})) M.setKey(c, k, v);
  const {program, errors} = T.parseProgram(preset.prog, M.OPS);
  assert.deepStrictEqual(errors, []);
  return M.simulate(c, program);
}
const BF16 = T.FORMATS[5];
const bf16At = (r, a) => T.decode(r.l1.readBits(a, 2), BF16);

// ***** formats *****
test("BF16 / FP16 / FP8 encodings", () => {
  assert.strictEqual(T.encode(1, BF16), 0x3F80);
  assert.strictEqual(T.encode(1, T.FORMATS[1]), 0x3C00);
  assert.strictEqual(T.encode(-2, T.FORMATS[10]), 0xC0);
  assert.strictEqual(T.quantize(500, T.E4M3), 448);
});
test("BFP8 block: shared exponent and exact decode", () => {
  const b = T.bfpBlock([1, 2, 3, -5], T.FORMATS[6]);
  assert.strictEqual(b.exp, 129);
  assert.deepStrictEqual(b.bits.map((x, i) => T.bfpDecode(x, b.exp, T.FORMATS[6])), [1, 2, 3, -5]);
});

// ***** packer *****
const PP = presets("packer.html", "const TILE_PACK");
const pp = name => PP.find(p => p.name.startsWith(name));
test("packer: every preset runs without errors", () => {
  for (const p of PP) { const r = run(P, p); const e = r.steps.filter(s => s.error); assert.strictEqual(e.length, 0, `${p.name}: ${e.map(s => s.error)}`); }
});
test("packer: blackhole-py tile pack writes Dest tile 0 in order as BF16", () => {
  const r = run(P, pp("Tile pack"));
  for (let i = 0; i < 1024; i++) assert.strictEqual(bf16At(r, 0x20000 + 2 * i), T.quantize(r.dest[i], BF16), `datum ${i}`);
});
test("packer: row pack gives the same bytes as tile pack", () => {
  const a = run(P, pp("Tile pack")), b = run(P, pp("Row pack"));
  for (let i = 0; i < 2048; i++) assert.strictEqual(a.l1.get(0x20000 + i), b.l1.get(0x20000 + i));
});
test("packer (hw): pack counters follow cfg_ctx", () => {
  // tests/hw/test_contexts.py::test_pack_counters_follow_cfg_ctx: kept-row spacing = reads_per_xy_plane of the PACR's context
  for (const [ctx, r0, r1] of [[0, 4, 2], [1, 4, 2], [1, 2, 4], [1, 8, 1], [1, 1, 8]]) {
    const p = pp("Pack counters");
    const prog = p.prog.replace(/ctx=1/g, `ctx=${ctx}`);
    const r = run(P, {...p, prog}, {"ctx0.reads_per_xy_plane": r0, "ctx1.reads_per_xy_plane": r1, "ctx0.l1_dest": (0x20000 >> 4) - 1});
    const base = ctx ? 0x21000 : 0x20000, kept = [];
    for (let row = 0; row < 64; row++) if (bf16At(r, base + row * 32 + 2)) kept.push(row);
    const period = ctx ? r1 : r0;
    assert.deepStrictEqual(kept, Array.from({length: 64 / period}, (_, i) => i * period), `ctx ${ctx}, ${r0}/${r1}`);
  }
});
test("packer (hw): dest_row_offset follows cfg_ctx, in rows", () => {
  const r = run(P, pp("Two contexts"));
  for (let i = 0; i < 1024; i++) assert.strictEqual(bf16At(r, 0x21000 + 2 * i), T.quantize(r.dest[1024 + i], BF16));
});
test("packer: scalar pack keeps datum [0][0] of each face only", () => {
  const r = run(P, pp("Scalar pack"), {dest_pattern: "index"});
  const nz = []; for (let i = 0; i < 1024; i++) if (bf16At(r, 0x20000 + 2 * i)) nz.push(i);
  assert.deepStrictEqual(nz, [256, 512, 768]);  // datum 0 is 0.0 in the index pattern
});
test("packer: downsample 0x5555 halves the output", () => {
  const r = run(P, pp("Downsample"));
  assert.strictEqual(r.l1.bytes.size, 1024);
  for (let i = 0; i < 512; i++) assert.strictEqual(bf16At(r, 0x20000 + 2 * i), T.quantize(r.dest[2 * i], BF16));
});
test("packer: BFP8 layout is 64 exponent bytes + 1024 datum bytes", () => {
  const r = run(P, pp("BFP8 output"));
  assert.strictEqual(r.l1.bytes.size, 1088);
});

// ***** unpacker *****
const UP = presets("unpacker.html", "const l1base");
const up = name => UP.find(p => p.name.startsWith(name));
test("unpacker: every preset runs without errors", () => {
  for (const p of UP) { const r = run(U, p); const e = r.steps.filter(s => s.error); assert.strictEqual(e.length, 0, `${p.name}: ${e.map(s => s.error)}`); }
});
test("unpacker: face-by-face tile lands in SrcA bank 0 in order", () => {
  const r = run(U, up("Tile → SrcA"));
  for (let i = 0; i < 1024; i++) assert.strictEqual(r.srcA[0].meta[i].src, i);
});
test("unpacker (hw): UNPACR cfg_ctx N reads context N's own L1 base, N = 0..7", () => {
  const r = run(U, up("Eight contexts"));
  for (let k = 0; k < 8; k++) for (let i = 0; i < 1024; i++) assert.strictEqual(r.dest.meta[k * 1024 + i].src, k * 65536 + i);
});
test("unpacker: zero-compressed tile expands back to the original", () => {
  const r = run(U, up("Zero-compressed"));
  const vals = r.buffers[0].vals;
  for (let i = 0; i < 1024; i++) assert.strictEqual(r.srcA[0].v[i], T.quantize(vals[i], BF16), `datum ${i}`);
});
test("unpacker: context counter walks 0 1 2 3, then 2 3 0 1 after two increments", () => {
  const r = run(U, up("Context counter"));
  const ctxs = r.steps.filter(s => s.ins.op === "UNPACR").map(s => +s.trace[0][1].match(/context (\d)/)[1]);
  assert.deepStrictEqual(ctxs, [0, 1, 2, 3, 2, 3, 0, 1]);
});
test("unpacker: BFP8 input decodes to the block-float values", () => {
  const r = run(U, up("BFP8 input"));
  const vals = r.buffers[0].vals;
  for (let b = 0; b < 1024; b += 16) {
    const blk = T.bfpBlock(vals.slice(b, b + 16), T.FORMATS[6]);
    for (let j = 0; j < 16; j++) assert.strictEqual(r.srcA[0].v[b + j], blk.values[j]);
  }
});

console.log(failed ? `\n${failed} failed` : "\nall passed");
process.exitCode = failed ? 1 : 0;
