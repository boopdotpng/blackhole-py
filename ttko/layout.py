"""Device-side tile layout conversion for legacy kernels.

Host transfers retain row-major bytes. A BRISC kernel permutes elements in L1;
readback uses separate DRAM storage so observing a buffer never changes it.
"""
from dataclasses import replace

from ttko import DType
from ttko.program import Buffer, Const, Program
from ttko.asm import Cond
from ttko.isa import R


def convert(source, target, *, inverse=False):
  if source.physical_tiles != target.physical_tiles or source.dtype != target.dtype:
    raise ValueError('layout conversion requires matching physical storage')
  total = source.physical_tiles
  cores = source.cores
  # Global bindings use physical page indices, independent of logical sharding.
  src = replace(source, name='layout_source', global_address=True)
  dst = replace(target, name='layout_target', global_address=True)
  start = Const('layout_start', tuple(total * i // len(cores) for i in range(len(cores))))
  count = Const('layout_count', tuple(total * (i + 1) // len(cores) - total * i // len(cores) for i in range(len(cores))))
  p = Program(cores, src, dst, start, count)
  k = p.brisc
  noc = k.noc_at(0)
  source_l1 = p.l1(source.tile_size, 16)
  target_l1 = p.l1(source.tile_size, 16)
  tile, remaining = k.reg(2)
  k.read(tile, p.param_addr(start)); k.read(remaining, p.param_addr(count))
  with k.loop(Cond(remaining, '!=', 0)):
    noc.read_tile(src, tile, source_l1)
    # Permute 16-element row fragments. Each fragment is contiguous in both
    # layouts; only the device computes its source/destination addresses.
    with k.scope():
      fragment, source_ptr, target_ptr, value, scratch = k.reg(5)
      k.li(fragment, 0)
      with k.loop(Cond(fragment, '<u', 64)):
        # Row-major fragment f: row=f//2, half=f%2.
        # Face-major fragment: (row//16)*32 + half*16 + row%16.
        k.andi(scratch, fragment, 32)
        k.andi(target_ptr, fragment, 1); k.slli(target_ptr, target_ptr, 4)
        k.add(target_ptr, target_ptr, scratch)
        k.andi(scratch, fragment, 30); k.srli(scratch, scratch, 1)
        k.add(target_ptr, target_ptr, scratch)
        shift = (16 * source.dtype.itemsize).bit_length() - 1
        k.slli(source_ptr, fragment, shift); k.slli(target_ptr, target_ptr, shift)
        if inverse: source_ptr, target_ptr = target_ptr, source_ptr
        k.li(scratch, source_l1); k.add(source_ptr, source_ptr, scratch)
        k.li(scratch, target_l1); k.add(target_ptr, target_ptr, scratch)
        for offset in range(0, 16 * source.dtype.itemsize, 4):
          k.lw(value, source_ptr, offset); k.sw(value, target_ptr, offset)
        if inverse: source_ptr, target_ptr = target_ptr, source_ptr
        k.addi(fragment, fragment, 1)
    k.fence()
    with k.scope():
      address, coordinate = noc._dram_tile(dst, tile)
      noc.write(target_l1, address, coordinate, source.tile_size, posted=False)
    k.addi(tile, tile, 1); k.addi(remaining, remaining, -1)
  return p


def write_tiled(device, buffer, data):
  device._write_physical(buffer, buffer.pad_data(data))
  return device.queue(convert(buffer, buffer), report=False)


def queue_read_tiled(device, buffer):
  from ttko.device import Readback
  scratch = getattr(device, '_layout_readback_buffers', None)
  if scratch is None:
    scratch = device._layout_readback_buffers = {}
  if buffer not in scratch:
    address = device.dram.allocator.alloc(((buffer.physical_tiles + buffer.banks - 1) // buffer.banks) * buffer.tile_size)
    scratch[buffer] = replace(buffer, name=buffer.name + '_readback', addr=address)
  target = scratch[buffer]
  device.queue(convert(buffer, target, inverse=True), report=False)
  offset = device._staging_next
  program = device._dram_copy_program(target, write=False, offset=offset)
  readback = Readback(device, buffer, offset)
  device._staging_next += buffer.size
  device.read_queue.append((program, None, readback, False))
  return readback
