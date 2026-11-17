"""Items -> bytes. Fill call placeholders, lay out labels, relax out-of-range conditional branches (+-4 KiB) into an
inverted branch over a jal until stable, encode with isa.py, append fw.ret(role), check fw.CODE_SIZE.
Only PC-relative control flow, so the image is position-independent as fw.program() requires.

Also writes the listing (source line, expansion sites, register assignments, emitted words decoded with
rv_decode/tensix_decode) and the manifest from layout."""
