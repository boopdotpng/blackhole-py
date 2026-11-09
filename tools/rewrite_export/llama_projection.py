"""Rewrite projection adapter, derived from blackhole-py/examples/llama3/kernels.py (projection and its helpers).

Upstream specializes a projection per core: rows owned, DRAM port phase and first bank are compiled in, so 88 cores
get up to 9 images per RISC in scattered groups and a launch needs ~140 multicasts. Here they are per-core launch
parameters, read at runtime from the per-core table the exporter places next to each core's shard addresses, so
every core reading on the same NoC runs one image. Imported by the offline exporter in blackhole-py's namespace; no
device is opened here. Keep the math in sync with the upstream generator.
"""
from dataclasses import dataclass
from examples.llama3.kernels import (
  Buffer, CB, Const, DType, Dst, FP8_ACTIVATION, Fpu, LReg, LaneConfig, LoopTemplate, Pack, Program, R, Sem, SemWait,
  Stall, TT, UnpackTarget, _add_constant, _dense_offset, _dot_accumulate, _dot_finalize, _dot_row, _load_scale,
  _rms_setup_apply_macro, _rmsnorm, _round_fp8_program, _scale_constants, _scale_input, _sfpu_mul, _swiglu_math,
  _tile_offset, _zero_l1_words, sem_wait, specialize,
)
from pcie import dram_port
from ttko.noc import NoC
from ttko.registers import TensixL1


@dataclass(frozen=True)
class RuntimePort:
  """A DRAM port read at runtime from the L1 word at ``address`` (a per-core launch parameter), so cores that use
  different ports share one image. Bank b goes through endpoint (port + b) % ports, as with an integer port."""
  address: int


class RuntimePortNoC(NoC):
  """A NoC whose DRAM port is a RuntimePort. Only DRAM lookups inside subroutines are supported: they embed every
  port's bank table and pick a row at runtime, where a build-time port would embed one."""
  def dram_endpoint(self, endpoints, bank): raise ValueError("a runtime DRAM port has no build-time endpoint")

  def _dram_tile_inline(self, param, tile):
    k, buffer = self.k, param
    endpoints = buffer.dram_endpoints
    if len(endpoints) != buffer.banks:
      raise ValueError(f"buffer uses {buffer.banks} DRAM banks but has {len(endpoints)} endpoints")
    if not k._sub_stack: raise ValueError("a runtime DRAM port needs a subroutine (physical registers)")
    base = k.reg()
    k.read(base, TensixL1.PARAM_BASE + k.param_slots[param] * 4)
    address, coordinate, bank, banks, scale, rotation = k.reg(6, exclude=(tile, base))
    # Program binding moves the base to this core's shard and stores the
    # shard's first DRAM bank in the aligned address's low bits.
    k.andi(rotation, base, 7); k.andi(base, base, -8)
    if isinstance(tile, R): k.add(address, tile, rotation)
    else: k.li(address, tile); k.add(address, address, rotation)
    count = len(endpoints)
    if count & (count - 1) == 0:
      k.andi(bank, address, count - 1); k.srli(address, address, count.bit_length() - 1)
    else:
      k.li(banks, count)
      k.remu(bank, address, banks); k.divu(address, address, banks)
    if buffer.tile_size & (buffer.tile_size - 1) == 0:
      k.slli(address, address, buffer.tile_size.bit_length() - 1)
    else:
      k.li(scale, buffer.tile_size); k.mul(address, address, scale)
    k.add(address, address, base)
    bank_table(self, coordinate, endpoints, exclude=(address, bank))
    k.slli(bank, bank, 1); k.add(coordinate, coordinate, bank); k.lhu(coordinate, coordinate)
    return address, coordinate


def noc_at(k, index, port):
  """k.noc_at, or a RuntimePortNoC for a runtime port."""
  if isinstance(port, RuntimePort):
    if k.role not in ("brisc", "ncrisc"): raise RuntimeError(f"{k.role} cannot access a NoC")
    return RuntimePortNoC(k, index, port)
  return k.noc_at(index, port)


def bank_table(noc, pointer, endpoints, exclude=()):
  """pointer = address of this core's bank -> NoC coordinate halfword table, embedded after the current subroutine.
  With a runtime port the table holds one row of banks per port and pointer selects the row."""
  k, count = noc.k, len(endpoints)
  runtime = isinstance(noc.port, RuntimePort)
  if runtime:
    ports = {len(bank) for bank in endpoints}
    if len(ports) != 1: raise ValueError("a runtime DRAM port needs the same number of ports on every bank")
    coordinates = [noc.coordinate(*dram_port(endpoints[bank], noc.index, port, bank))
                   for port in range(ports.pop()) for bank in range(count)]
  else:
    coordinates = [noc.coordinate(*noc.dram_endpoint(endpoints, bank)) for bank in range(count)]
  table = k.embed(coordinates[index] | (coordinates[index + 1] if index + 1 < len(coordinates) else 0) << 16
                  for index in range(0, len(coordinates), 2))
  k.la(pointer, table)
  if runtime:
    with k.scope():
      port, row = k.reg(2, exclude=(pointer, *exclude))
      k.read(port, noc.port.address)
      k.li(row, 2 * count)
      k.mul(port, port, row)
      k.add(pointer, pointer, port)
  return pointer


def projection(cfg, x, projections, *, norm_weight=None, swiglu_output=None,
               residual=None, dense_output=None, rotate_ports=True):
  """Build y_i = W_i @ x for 1-3 weights that share one input (Q/K/V, gate/up).

    x               dense input vector [input_dim]
    projections     ((weight, compact_output), ...), weight = [rows, input_dim]
    norm_weight     RMSNorm gamma: x is normalized first (qkv, gate, lm)
    swiglu_output   dense silu(y_0) * y_1 (gate/up)
    residual        with dense_output: dense_output = residual + y_0 (o, down)
    rotate_ports    read weights over all three DRAM ports per bank
  """
  if dense_output is not None and residual is None:
    raise ValueError("a dense projection output requires a residual input")
  weights = tuple(weight for weight, _ in projections)
  rotate = rotate_ports and all(len(endpoints) >= 3 for weight in weights for endpoints in weight.dram_endpoints)
  # What differs between cores (rows owned, DRAM port, first bank) is a per-core launch parameter, so every core
  # that reads over the same NoC runs one image: one multicast per role instead of one per core group. Only the
  # read NoC is built in, and that splits the chip spatially (rotate=False), so it stays a couple of rectangles.
  cores = weights[0].cores
  return specialize(
    lambda read_noc: _projection_program(
      cfg, x, projections, read_noc, rotate, norm_weight=norm_weight, swiglu_output=swiglu_output,
      residual=residual, dense_output=dense_output,
    ),
    cores, tuple(_projection_read_noc(cfg, core, rotate) for core in cores),
  )


def _projection_read_noc(cfg, core, rotate):
  """The NoC a projection core reads on; writes use the other one.

  The writer uses the other NoC so its transaction IDs cannot collide with
  the reader's. Never mix the two policies inside one program: spatially
  split NoCs with rotated ports hung both p150a cards. Programs run one
  after another, so mixing policies across programs is fine. Rotated ports
  read on NoC0 everywhere; core i reads bank b through port (i + b) % 3.
  """
  return 0 if rotate else int(core[0] >= cfg.noc_split_x)


def _first_bank(weight, index):
  """The DRAM bank holding core ``index``'s first weight page (8 banks), else None."""
  if weight.banks != 8: return None
  page_tiles = getattr(weight, "page_tiles", 1)
  first = weight.item_starts[index] * (weight.tiles_per_item // page_tiles) if weight.global_address else weight.tile_starts[index]
  return first % weight.banks


def _read_rows(k, p, projections, rows):
  """rows = how many rows this core owns across ``projections`` (per-core launch parameters)."""
  k.read(rows, p.param_addr(projections[0][2]))
  for _, _, count in projections[1:]:
    with k.scope():
      more = k.reg(exclude=rows)
      k.read(more, p.param_addr(count))
      k.add(rows, rows, more)
  return rows


def _projection_program(cfg, x, projections, read_noc, rotate, *, norm_weight,
                        swiglu_output, residual, dense_output):
  """The projection program for every core reading on ``read_noc``. ``projections`` is ((weight, output), ...)."""
  write_noc = 1 - read_noc
  cores = projections[0][0].cores
  # Per-core launch parameters: rows owned per weight, DRAM port phase, and the first weight bank where row_start
  # does not already give it. From here on ``projections`` is ((weight, output, rows), ...).
  projections = tuple((weight, output, Const(f"{weight.name}_rows", weight.item_counts)) for weight, output in projections)
  port_phase = Const("dram_port", tuple(index % 3 for index in range(len(cores)))) if rotate else None
  weight_dtype = projections[0][0].dtype
  fp8 = weight_dtype.is_fp8
  if any(weight.tilized != x.tilized for weight, _, _ in projections):
    raise ValueError("projection weights and activation must have the same element order")
  if norm_weight is not None and norm_weight.tilized != x.tilized:
    raise ValueError("projection norm and activation must have the same element order")
  input_dim = x.shape[1]
  input_tiles = input_dim // 1024

  # Launch parameters. Weights are global buffers; row_start tells each core
  # where its rows begin. The O projection reads x through this flat view.
  row_starts = tuple(
    Const(f"{weight.name}_row_start", weight.item_starts)
    if weight.global_address and len(weight.cores) > 1 else None
    for weight, _, _ in projections
  )
  first_banks = tuple(
    Const(f"{weight.name}_first_bank", tuple(_first_bank(weight, index) for index in range(len(cores))))
    if row_start is None and weight.banks == 8 else None
    for (weight, _, _), row_start in zip(projections, row_starts)
  )
  token = Buffer(
    f"{x.name}_decode_token", x.addr, x.dtype, (input_dim,), None,
    (x.cores[0],), x.banks, global_address=True,
    tilized=x.tilized, dram_endpoints=x.dram_endpoints,
  )
  scatter_output = swiglu_output if swiglu_output is not None else dense_output
  p = Program(
    projections[0][0].cores, token,
    *(parameter for (weight, output, _), row_start in zip(projections, row_starts)
      for parameter in ((weight, output) if row_start is None else (weight, output, row_start))),
    # FP8: per-layer scales arrive as SFPU load-immediate instruction words.
    *(_scale_constants("input_scale", 1.) if fp8 else ()),
    *(param for i in range(len(projections)) for param in (_scale_constants(f"output_scale_{i}", 1/256) if fp8 else ())),
    *((scatter_output, Const("dense_start", projections[0][0].item_starts)) if scatter_output is not None else ()),
    *((residual,) if residual is not None else ()),
    *((norm_weight,) if norm_weight is not None else ()),
    *(rows for _, _, rows in projections),
    *((port_phase,) if port_phase is not None else ()),
    *(bank for bank in first_banks if bank is not None),
    fp32_dst=True,
  )
  port = RuntimePort(p.param_addr(port_phase)) if port_phase is not None else None

  # L1 working memory.
  weight_cb = p.cb(weight_dtype, depth=(16 if fp8 else 2) * input_tiles)   # BRISC -> TRISC0: weight rows
  scalar_dtype = projections[0][1].dtype
  scalar_cb = p.cb(scalar_dtype, depth=2)                                  # TRISC2 -> NCRISC: one dot product
  operand_dtype = FP8_ACTIVATION if fp8 else DType.BF16                    # format of x as the FPU sees it
  convert_input = operand_dtype.is_fp8 and not token.dtype.is_fp8          # FP8: quantize x without RMSNorm
  # x after RMSNorm / FP8 quantization. Without either, x is copied raw to token_l1.
  normalized_cb = p.cb(operand_dtype, depth=input_tiles) if norm_weight is not None or convert_input else None
  token_l1 = normalized_cb.addr if normalized_cb is not None else p.l1(input_tiles * token.tile_size, alignment=16)
  # This core's rows of each output, gathered into one tile ("compact").
  compact_cbs = tuple(p.cb(output.dtype, depth=output.tiles_per_item) for _, output, _ in projections)

  # Step 1 (all cores): bring x into token_l1, normalized and/or quantized.
  # BRISC's DRAM reads are collected here and issued together below.
  input_reads, input_publications = [], []
  if norm_weight is None and convert_input:
    # FP8: x * input_scale, rounded to E4M3 (O and down projections).
    incoming = p.cb(token.dtype, depth=input_tiles)
    CB.reserve_back(p.brisc, incoming, input_tiles)
    input_reads.extend((token, tile, incoming.addr + tile * token.tile_size) for tile in range(input_tiles))
    input_publications.append((incoming, input_tiles))
    for _ in p.trisc0.range(input_tiles): p.unpack.move(incoming, UnpackTarget.SRCA)
    for _ in p.trisc1.range(input_tiles):
      p.fpu.copy_a_tiles(dst_tiles=(0,))
      _scale_input(p, (0,))
      p.sfpu.map(_round_fp8_program(), tile=0).publish()
    for _ in p.trisc2.range(input_tiles): p.pack.move(normalized_cb, tile=0)
  elif norm_weight is None:
    # Raw x straight into token_l1 (BF16 O and down projections).
    input_reads.extend((token, tile, token_l1 + tile * token.tile_size) for tile in range(input_tiles))
  else:
    # RMSNorm: x and gamma -> Dst, normalized on the SFPU, packed to normalized_cb.
    if input_dim != cfg.embed_dim: raise ValueError(f"fused RMSNorm requires a {cfg.embed_dim}-element token")
    operands = p.cb(DType.BF16, depth=2 * cfg.embed_tiles)   # x tiles, then gamma tiles
    CB.reserve_back(p.brisc, operands, 2 * cfg.embed_tiles)
    for index, buffer in enumerate((token, norm_weight)):
      input_reads.extend((buffer, tile, operands.addr + (index * cfg.embed_tiles + tile) * operands.tile_size)
                         for tile in range(cfg.embed_tiles))
    input_publications.append((operands, 2 * cfg.embed_tiles))
    p.unpack.move(operands, UnpackTarget.SRCA)
    for _ in p.trisc0.range(2 * cfg.embed_tiles - 1): p.unpack.move(operands, UnpackTarget.SRCA, configure_format=False)
    _rms_setup_apply_macro(p.sfpu)
    p.fpu.copy_a_tiles(dst_tiles=range(2 * cfg.embed_tiles))
    _rmsnorm(cfg, p.sfpu, fp8=operand_dtype.is_fp8,
             scale=(lambda: _scale_input(p, range(cfg.embed_tiles))) if operand_dtype.is_fp8 else None)
    p.pack.move_tiles(normalized_cb, tiles=tuple(range(cfg.embed_tiles)))
  if residual is not None:
    residual_l1 = p.l1(residual.tiles * residual.tile_size, alignment=16)
    input_reads.extend((residual, tile, residual_l1 + tile * residual.tile_size) for tile in range(residual.tiles))
  # BRISC: x, gamma, and residual reads are independent. Publish the input
  # CBs after a single completion barrier, then stream weights immediately.
  if input_reads:
    with noc_at(p.brisc, read_noc, port).transaction() as transaction:
      for buffer, tile, target in input_reads:
        with p.brisc.scope():
          address, coordinate = noc_at(p.brisc, read_noc, port)._dram_tile(buffer, tile)
          transaction.read(address, coordinate, target, buffer.tile_size)
  for cb, count in input_publications: CB.push_back(p.brisc, cb, count)

  # Step 3 (BRISC): stream this core's weight rows into weight_cb.
  _projection_read_weights(p, projections, row_starts, first_banks, (read_noc, port), weight_cb, input_tiles)

  # Step 4 (TRISC0): for every row, unpack (weight tile -> SrcA, x tile -> SrcB).
  # The unpacker needs the converted x; the DRAM reader can run ahead.
  if normalized_cb is not None: CB.wait_front(p.trisc0, normalized_cb, input_tiles)
  p.unpack.prepare_l1_pair_formats(weight_cb.dtype, operand_dtype)
  # Every row of every projection unpacks the same way: one loop over all rows.
  with p.trisc0.scope():
    for _ in p.trisc0.range(_read_rows(p.trisc0, p, projections, p.trisc0.reg())):
      with p.trisc0.scope():
        address, step = p.trisc0.reg(2)
        p.trisc0.li(address, token_l1)
        p.trisc0.li(step, 1024 * operand_dtype.itemsize)
        for _ in p.trisc0.range(input_tiles):
          p.unpack.move_l1_pair(weight_cb, address, configure_format=False, source_b_dtype=operand_dtype)
          p.trisc0.add(address, address, step)

  # Step 5 (TRISC1): elementwise multiply on the FPU, sum on the SFPU -> one scalar per row.
  _projection_dot_math(cfg, p, projections, input_tiles)

  # Step 6 (TRISC2): pack each row's scalar into scalar_cb.
  p.pack._configure(scalar_cb, True, True)
  with p.trisc2.scope():
    for _ in p.trisc2.range(_read_rows(p.trisc2, p, projections, p.trisc2.reg())):
      sem_wait(p.trisc2, Sem.MATH_PACK, SemWait.STALL_ON_ZERO, Stall.TDMA)
      p.pack._move_acquired(scalar_cb, 0, True, configure=False)
      p.pack._release_dst()

  # Step 7 (NCRISC): place each scalar at its row's slot in the compact tile.
  # Without an epilogue, write the compact tile to this core's DRAM shard.
  for compact_cb, (_, output, local_rows) in zip(compact_cbs, projections):
    compact_l1 = compact_cb.addr
    _zero_l1_words(p.ncrisc, compact_l1, output.tiles_per_item * output.tile_size // 4)
    with p.ncrisc.scope():
      count = p.ncrisc.reg()
      p.ncrisc.read(count, p.param_addr(local_rows))
      for local_row in p.ncrisc.range(count):
        CB.wait_front(p.ncrisc, scalar_cb)
        with p.ncrisc.scope():
          source, value, byte_offset, target = p.ncrisc.reg(4, exclude=local_row)
          CB.get_read_ptr(p.ncrisc, scalar_cb, source)
          p.ncrisc.read(value, source, bytes=scalar_dtype.itemsize)
          _tile_offset(p.ncrisc, local_row, byte_offset, scalar_dtype)
          p.ncrisc.li(target, compact_l1)
          p.ncrisc.add(target, target, byte_offset)
          p.ncrisc.write(target, value, bytes=scalar_dtype.itemsize)
        CB.pop_front(p.ncrisc, scalar_cb)
    if scatter_output is not None:
      CB.push_back(p.ncrisc, compact_cb)       # handed to the epilogue below
      continue
    for tile in range(output.tiles_per_item):
      with p.ncrisc.scope():
        target_address, target_coordinate = noc_at(p.ncrisc, write_noc, port)._dram_tile(output, tile)
        noc_at(p.ncrisc, write_noc, port).write(
          compact_l1 + tile * output.tile_size, target_address, target_coordinate,
          output.tile_size, posted=False,
        )

  # Step 8, epilogue A (gate/up): hidden = silu(gate) * up, scattered dense.
  if swiglu_output is not None:
    output_cb = p.cb(swiglu_output.dtype, depth=1)
    for cb in compact_cbs: p.unpack.move(cb, UnpackTarget.SRCA)
    _swiglu_math(cfg, p, fp8=swiglu_output.dtype.is_fp8)
    p.pack.move(output_cb, tile=0)
    _scatter_dense(p, output_cb, swiglu_output, projections[0][2], read_noc=write_noc, port=port)

  # Step 8, epilogue B (o/down): x_out = residual + y, scattered dense.
  elif residual is not None:
    residual_cb = p.cb(DType.BF16, depth=1)
    output_cb = p.cb(DType.BF16, depth=1)
    # NCRISC gathers this core's residual features into the compact layout.
    # The reader finishes residual DMA before delivering any projection row;
    # consuming all scalar rows above makes that L1 data safe to read here.
    with p.ncrisc.scope():
      start, count = p.ncrisc.reg(2)
      p.ncrisc.read(start, p.param_addr(p.param("dense_start")))
      p.ncrisc.read(count, p.param_addr(projections[0][2]))
      for index in p.ncrisc.range(count):
        with p.ncrisc.scope():
          feature, src, dst, value = p.ncrisc.reg(4, exclude=(start, index))
          p.ncrisc.add(feature, start, index)
          _dense_offset(p.ncrisc, residual, feature, src)
          _add_constant(p.ncrisc, src, residual_l1)
          p.ncrisc.read(value, src, bytes=2)
          _tile_offset(p.ncrisc, index, dst)
          _add_constant(p.ncrisc, dst, residual_cb.addr)
          p.ncrisc.write(dst, value, bytes=2)
    CB.push_back(p.ncrisc, residual_cb)
    p.unpack.move_pair(compact_cbs[0], residual_cb)
    # Match the original residual kernel's BF16 destination arithmetic.
    Fpu(p.trisc1, Dst(False)).binary("add", dst_tile=0).publish()
    Pack(p.trisc2, Dst(False)).move(output_cb, tile=0)
    _scatter_dense(p, output_cb, dense_output, projections[0][2], read_noc=write_noc, port=port)
  return p


def _projection_read_weights(p, projections, row_starts, first_banks, route, weight_cb, input_tiles):
  """BRISC: push this core's weight rows, one full row (input_tiles tiles) at a time.

  Weights are stored row-major and interleaved page by page across the DRAM
  banks: 8 banks walk (address, bank) from row_start, or from ``first_bank``
  when there is none; other bank counts use the generic tile-at-a-time reader.
  """
  read_noc, port = route
  for (weight, _, rows), row_start, first_bank in zip(projections, row_starts, first_banks):
    page_tiles = getattr(weight, "page_tiles", 1)
    row_pages = input_tiles // page_tiles
    with p.brisc.scope():
      local_rows = p.brisc.reg()
      p.brisc.read(local_rows, p.param_addr(rows))
      if weight.banks != 8:
        for local_row in p.brisc.range(local_rows):
          source_row = local_row
          if row_start is not None:
            source_row = p.brisc.reg(exclude=local_row)
            p.brisc.read(source_row, p.param_addr(row_start))
            p.brisc.add(source_row, source_row, local_row)
          with p.brisc.scope():
            first, scale = p.brisc.reg(2, exclude=source_row)
            p.brisc.li(scale, input_tiles)
            p.brisc.mul(first, source_row, scale)
            # One tile at a time bounds register use for the 14-tile MLP input.
            for index in range(input_tiles):
              with p.brisc.scope():
                tile = p.brisc.reg(exclude=first)
                p.brisc.addi(tile, first, index)
                noc_at(p.brisc, read_noc, port).read_tiles_into_cb(weight, (tile,), weight_cb)
      else:
        # This core's weight pages are consecutive interleaved pages: walk
        # (address within bank, bank) at runtime and look the bank's NoC
        # coordinate up in a table, one shared loop for every row.
        noc = noc_at(p.brisc, read_noc, port)
        banks, page = weight.banks, weight.tile_size
        with p.brisc.scope():
          base, bank = p.brisc.reg(2)
          p.brisc.read(base, p.param_addr(weight))
          p.brisc.andi(base, base, -8)
          if row_start is not None:
            with p.brisc.scope():
              start, divisor = p.brisc.reg(2, exclude=(base, bank))
              p.brisc.read(start, p.param_addr(row_start))
              p.brisc.li(divisor, row_pages)
              p.brisc.mul(start, start, divisor)          # first global page
              p.brisc.andi(bank, start, banks - 1)
              p.brisc.srli(start, start, banks.bit_length() - 1)
              p.brisc.slli(start, start, page.bit_length() - 1)
              p.brisc.add(base, base, start)
          else:
            p.brisc.read(bank, p.param_addr(first_bank))
          for _ in p.brisc.range(local_rows):
            CB.reserve_back(p.brisc, weight_cb, input_tiles)
            with noc.transaction() as transaction, p.brisc.scope():
              target = p.brisc.reg(exclude=(base, bank))
              CB.get_write_ptr(p.brisc, weight_cb, target)
              body = _read_pages_body(noc, transaction.tid, weight.dram_endpoints, page)
              transaction._remote_pending = True
              p.brisc.call(p.brisc.subroutine(
                ("read_pages", noc.index, noc.port, transaction.tid, tuple(weight.dram_endpoints), page),
                body, 4), base, bank, target, row_pages, results=(base, bank))
            CB.push_back(p.brisc, weight_cb, input_tiles)


def _read_pages_body(noc, tid, endpoints, page):
  """Shared BRISC loop: read ``count`` consecutive interleaved DRAM pages into
  consecutive L1 pages; returns the advanced (address, bank)."""
  k, banks = noc.k, len(endpoints)
  def body(address, bank, target, count):
    with k.scope():
      pointer, coordinate, step = k.reg(3)
      bank_table(noc, pointer, endpoints, exclude=(address, bank, target, count))
      loop, same_bank = k._new_label("read_pages"), k._new_label("read_pages_bank")
      k.label(loop)
      k.slli(coordinate, bank, 1)
      k.add(coordinate, coordinate, pointer)
      k.lhu(coordinate, coordinate)
      noc._read_inline(tid, address, coordinate, target, page, 0)
      k.li(step, page)
      k.add(target, target, step)
      k.addi(bank, bank, 1)
      k.li(coordinate, banks)
      k.bne(bank, coordinate, same_bank)
      k.li(bank, 0)
      k.add(address, address, step)
      k.label(same_bank)
      k.addi(count, count, -1)
      k.bne(count, R.ZERO, loop)
    return address, bank
  return body


def _projection_dot_math(cfg, p, projections, input_tiles):
  """TRISC1: for each row, multiply weight and x tiles, then sum all products.

  The FPU multiplies a (weight, x) tile pair elementwise into Dst tile 0. The
  SFPU then adds those 1024 FP32 products into 32 running lane sums (L7).
  After the last input tile, _dot_finalize reduces the 32 lanes to one value.
  The FPU and SFPU share Dst tile 0 throughout. The multiply MOP stays
  resident; the SFPU is driven by direct replay so the two engines do not
  rewrite their shared MOP configuration for every tile.
  """
  fpu, sfpu = p.fpu, p.sfpu
  fpu._configure_dst(0)
  sfpu._configure_dst(0, LaneConfig())
  fpu._set_addr_mod(0, srca=8, srcb=8, dest=8)
  fpu._set_addr_mod(1)
  fpu._set_addr_mod(2, srca_clear=True, srcb_clear=True,
                    dest_carry=True, fidelity_increment=1)
  fpu._set_addr_mod(3, srca_clear=True, srcb_clear=True, dest=8,
                    dest_carry_to_carry=True, fidelity_clear=True)
  # One MOP run multiplies one 16x16 face (BF16: 2 fidelity phases).
  fpu._mop.configure(LoopTemplate(
    outer=1 if projections[0][0].dtype is DType.FP8 else 2, inner=2, loop=TT.TTELWMUL(0, 0, 0, 0, 0),
    last=TT.TTELWMUL(3, 0, 0, 3, 0),
    outer_last=TT.TTELWMUL(0, 0, 0, 2, 0),
  ))
  accumulate = _dot_accumulate(reset=False)
  replay_start, replay_body = sfpu._prepare(accumulate)
  assert replay_start is not None
  finalize = _dot_finalize()
  for projection_index, (_, _, rows) in enumerate(projections):
    with p.trisc1.scope():
      local_rows = p.trisc1.reg()
      p.trisc1.read(local_rows, p.param_addr(rows))
      for local_row in p.trisc1.range(local_rows):
        # One shared body per row: every projection and row runs the same code.
        p.trisc1.outline(("projection_dot_row", input_tiles, replay_start, len(replay_body), finalize.words),
                         lambda: _dot_row(p, input_tiles, replay_start, len(replay_body), finalize))
        if projections[0][0].dtype.is_fp8:
          # FP8: undo the per-tensor weight/input quantization, y *= scale.
          _load_scale(p, f"output_scale_{projection_index}")
          words = []
          _sfpu_mul(words, LReg.L0, LReg.L6, LReg.L0)
          for word in words: sfpu._issue(word)
        for word in finalize.words[-2:]: sfpu._issue(word)
        sfpu.publish()


def _scatter_dense(p, cb, output, rows, *, read_noc=0, port=None):
  """NCRISC: write this core's ``rows`` (a per-core Const) compact values into the dense output vector.

  The values sit in tilized order in ``cb``. They are first rearranged in L1
  at the same byte offsets they have in DRAM, then written as runs of at most
  16 values (one face row), so every NoC write is contiguous and aligned.
  ``read_noc`` is the NoC used for these writes.
  """
  k = p.ncrisc
  size = output.dtype.itemsize
  shift = size.bit_length() - 1
  noc = noc_at(k, read_noc, port)
  dense = p.l1(output.tiles * output.tile_size, alignment=16)
  CB.wait_front(k, cb)
  with k.scope():
    start, source, count = k.reg(3)
    k.read(start, p.param_addr(p.param("dense_start")))
    k.read(count, p.param_addr(rows))
    CB.get_read_ptr(k, cb, source)
    for index in k.range(count):
      with k.scope():
        feature, src, dst, value = k.reg(4, exclude=(start, source, index))
        k.add(feature, start, index)
        _tile_offset(k, index, src, output.dtype)
        k.add(src, source, src)
        k.read(value, src, bytes=size)
        _dense_offset(k, output, feature, dst)
        _add_constant(k, dst, dense)
        k.write(dst, value, bytes=size)
    with noc.transaction() as transaction:
      with k.scope():
        feature, end = k.reg(2, exclude=start)
        k.mv(feature, start)
        k.read(end, p.param_addr(rows))
        k.add(end, end, start)
        loop = k._new_label("dense_scatter")
        k.label(loop)
        with k.scope():
          tile, offset, length, limit, src, dst = k.reg(6, exclude=(feature, end))
          k.srli(tile, feature, 10)
          address, coordinate = noc._dram_tile(output, tile)
          _dense_offset(k, output, feature, offset)
          k.li(src, dense)
          k.add(src, src, offset)
          if output.tile_size <= 2048:
            k.andi(offset, offset, output.tile_size - 1)
          else:
            k.slli(offset, offset, 20)
            k.srli(offset, offset, 20)
          k.add(dst, address, offset)
          k.andi(length, feature, 15)
          k.li(limit, 16)
          k.sub(length, limit, length)
          k.sub(limit, end, feature)
          enough = k._new_label("dense_chunk")
          k.bgeu(limit, length, enough)
          k.mv(length, limit)
          k.label(enough)
          k.add(feature, feature, length)
          k.slli(length, length, shift)
          transaction.write(src, dst, coordinate, length, posted=False)
        k.bltu(feature, end, loop)
  CB.pop_front(k, cb)
