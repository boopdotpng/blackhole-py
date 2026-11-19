"""Compile-time iteration, module loading, and NoC addressing in the model kernels."""

import pytest

from ttrv import Error, build
from ttrv.parse import parse, show


def test_relative_include_diamond_and_cycle(tmp_path):
  (tmp_path / "ops").mkdir()
  shared = tmp_path / "ops" / "shared.ttrv"
  shared.write_text("const WIDTH = 4")
  (tmp_path / "ops" / "left.ttrv").write_text("include shared")
  (tmp_path / "right.ttrv").write_text("include ops/shared")
  source = "include ../right\ninclude left\ngrid WIDTH"
  root = tmp_path / "ops" / "root.ttrv"
  root.write_text(source)
  assert build(source, file=str(root)).manifest["grid"] == 4
  shared.write_text("include root")
  with pytest.raises(Error, match="include.cycle"):
    parse(source, str(root))


def test_const_offsets_expand_without_runtime_lookup():
  source = """grid 1
const OFFSETS = [0, dst.face + 2, 2, 2]
l1 words: u32[32]
fn brisc() {
  repeat offset in OFFSETS { words[offset] = offset }
  words[0] = OFFSETS[1]
}
"""
  manual = source[:source.index("fn brisc")] + """fn brisc() {
    words[0] = 0
    words[18] = 18
    words[2] = 2
    words[2] = 2
    words[0] = 18
  }"""
  assert build(show(parse(source))).images == build(manual).images
  with pytest.raises(Error, match="const.index"):
    build(source.replace("OFFSETS[1]", "OFFSETS[4]"))
  with pytest.raises(Error, match="const.required"):
    build(source.replace("OFFSETS[1]", "OFFSETS[core.id]"))


def test_noc_group_preserves_completion_checks():
  source = """grid 1
param input: u32[]
l1 words: u32[1024]
fn brisc() {
  reads = noc.group read
  if core.id { noc.read words, input[0], n=1024, tid=reads }
  noc.wait reads
}"""
  build(source)
  with pytest.raises(Error, match="noc.pending"):
    build(source.replace("noc.wait reads", ""))
  with pytest.raises(Error, match="noc.kind"):
    build(source.replace("noc.group read", "noc.group write"))


@pytest.mark.parametrize("fmt", ["bfp4", "bfp8"])
def test_tile_address_on_packed_dram(fmt):
  source = f"""grid 1
param weights: {fmt}[], tiles_per_page=3
l1 data: {fmt}[1024]
fn brisc() {{ noc.read data, tileptr(weights, core.id), n=1024, wait }}
"""
  assert build(source).images == build(source.replace("tileptr(weights, core.id)", "weights[core.id]")).images


def test_tile_read_checks_alignment_for_runtime_index():
  with pytest.raises(Error, match="pointer.align"):
    build("""grid 1
param weights: bf16[]
l1 data: bf16[2048]
fn brisc() { noc.read data + 1, tileptr(weights, core.id), n=1024, wait }
""")
