"""Allocation-explicit raw external movement and individual local CB primitives."""
from dataclasses import dataclass

from asm import Asm
from fw.consts import TensixL1
from tests.movement import noc


@dataclass(frozen=True)
class Transfer:
  coordinate: int
  l1_address: int
  elements: int = 128
  element_bytes: int = 2
  offset_bytes: int = 0
  stride_bytes: int = 0
  noc_index: int = 0
  command_slot: int = 1
  tid: int = 3

  def __post_init__(self):
    if self.element_bytes not in (2, 4) or type(self.elements) is not int or self.elements <= 0 or self.elements % 128:
      raise ValueError('require positive whole BF16/FP32 blocks')
    for value in (self.l1_address, self.offset_bytes, self.stride_bytes):
      if type(value) is not int or value < 0 or value % 32:
        raise ValueError('addresses/offsets/strides must be nonnegative multiples of 32 bytes')
    if self.stride_bytes and self.stride_bytes < self.block_bytes:
      raise ValueError('external blocks must not overlap')
    if self.l1_address < TensixL1.DATA_BUFFER_SPACE_BASE or self.l1_address + self.size > TensixL1.DATA_BUFFER_SPACE_END - 32:
      raise ValueError('owned L1 must fit data arena, excluding profiler reservation')
    self.config  # Validate NoC fields using stable shared adapter.

  @property
  def block_bytes(self): return 128 * self.element_bytes
  @property
  def size(self): return self.elements * self.element_bytes
  @property
  def config(self):
    return noc.InterleavedConfig((self.coordinate,), self.l1_address, 1,
                                self.block_bytes, self.noc_index,
                                command_slot=self.command_slot, tid=self.tid,
                                standalone=True)


def _transfer(k: Asm, spec: Transfer, external_address, *, write, serial=False):
  """external_address is a register holding an aligned single-bank base.

  Caller owns the selected NIU command slot/TID. Complete-operation interval
  includes all command setup/address calculation/drains. serial=True retains
  a per-block-drained baseline; default batches this bounded block sequence.
  """
  if k.role not in ('brisc', 'ncrisc'):
    raise ValueError('NoC issuer must be BRISC or NCRISC')
  if spec.elements // 128 > 128:
    raise ValueError('bounded request batch is limited to 128 blocks')
  config = spec.config
  niu, command, remote, local_address, count, coordinate = k.reg(6)
  k.li(niu, config.niu); k.li(command, config.command)
  noc._wait_command_ready(k, command)
  noc._wait_zero(k, niu, noc.STATUS + noc.REQUESTS_OUTSTANDING + config.tid * 4)
  if write: noc._wait_zero(k, niu, noc.STATUS + noc.WRITES_OUTGOING + config.tid * 4)
  noc._initialize_command(k, command, noc._control(config, write=write), config.tid)
  local = noc._local_coordinate(k, config)
  k.li(coordinate, spec.coordinate)
  k.li(count, spec.block_bytes)
  for block in range(spec.elements // 128):
    k.li(remote, spec.offset_bytes + block * (spec.stride_bytes or spec.block_bytes))
    k.add(remote, external_address, remote)
    k.li(local_address, spec.l1_address + block * spec.block_bytes)
    noc._submit(k, command,
                source_address=local_address if write else remote,
                source_coordinate=local if write else coordinate,
                target_address=remote if write else local_address,
                target_coordinate=coordinate if write else local,
                byte_count=count)
    if serial:
      noc._wait_command_ready(k, command)
      if write: noc._wait_zero(k, niu, noc.STATUS + noc.WRITES_OUTGOING + config.tid * 4)
      noc._wait_zero(k, niu, noc.STATUS + noc.REQUESTS_OUTSTANDING + config.tid * 4)
  noc._wait_command_ready(k, command)
  if write: noc._wait_zero(k, niu, noc.STATUS + noc.WRITES_OUTGOING + config.tid * 4)
  noc._wait_zero(k, niu, noc.STATUS + noc.REQUESTS_OUTSTANDING + config.tid * 4)
  return k


def read_from(k, spec, external_address, *, serial=False):
  return _transfer(k, spec, external_address, write=False, serial=serial)


def write_to(k, spec, external_address, *, serial=False):
  return _transfer(k, spec, external_address, write=True, serial=serial)


def cb_action(k, config, action, count=1):
  """One individual credit primitive; preserves all other physical CB slots."""
  if action not in ('reserve', 'publish', 'wait', 'release'):
    raise ValueError('unknown CB action')
  if type(count) is not int or not 1 <= count <= config.depth:
    raise ValueError('credit count must fit CB capacity')
  producer = action in ('reserve', 'publish')
  counter, amount, pointer = k.reg(3)
  k.li(pointer, noc._cb_counter(config, received=producer))
  k.lhu(counter, pointer); k.li(amount, count)
  if action in ('reserve', 'wait'):
    noc._wait_cb(k, config, counter, amount, producer=producer)
  else:
    noc._publish_cb(k, config, counter, amount, producer=producer)
  return k


def semaphore_action(k, semaphore, action):
  """Compute-handoff semaphore primitive with its completion fence.

  post/get saturate at 15/0. wait_ready blocks while zero; wait_space blocks
  while value >= configured maximum. Caller drains payload engines before
  post/get when required by the handoff. This adapter blocks SYNC and includes
  a dependent SYNC instruction before the RISC pipeline drain.
  """
  from isa import Tensix as TT
  from tests.movement.unpacker.unpack import pc_sync, Stall, SemWait
  if k.role not in ('trisc0', 'trisc1', 'trisc2'):
    raise ValueError('Tensix semaphore action requires a TRISC')
  if type(semaphore) is not int or not 0 <= semaphore < 8:
    raise ValueError('semaphore index must be 0..7')
  if action == 'post': k.emit(TT.TTSEMPOST(1 << semaphore))
  elif action == 'get': k.emit(TT.TTSEMGET(1 << semaphore))
  elif action in ('wait_ready', 'wait_space'):
    condition = SemWait.ON_ZERO if action == 'wait_ready' else SemWait.ON_MAX
    k.emit(TT.TTSEMWAIT(Stall.SYNC, 1 << semaphore, condition))
    # Empty semaphore mask gives a side-effect-free SYNC consumer of wait gate.
    k.emit(TT.TTSEMPOST(0))
  else: raise ValueError('unknown semaphore action')
  pc_sync(k)
  return k


def source_flag(k, bank, action):
  """Individual bank ownership handoff, for exclusive SrcA/SrcB ping-pong use.

  publish inherits configured unpacker output format and flips its bank.
  release gives the current matrix bank back and flips matrix selection.
  Waits consume the hardware condition through an explicit SYNC dependency.
  Does not initialize or touch operand storage; whole physical bank ownership
  is required, independently of allocation-scoped payload transfer ownership.
  """
  from isa import Tensix as TT
  from tests.movement.unpacker.unpack import pc_sync, Stall, Wait, stall
  if k.role not in ('trisc0', 'trisc1', 'trisc2') or bank not in (0, 1):
    raise ValueError('source flags require a TRISC and bank 0=A or 1=B')
  if action == 'publish':
    k.emit(TT.TTUNPACR_NOP(bank, 0, 0, 1, 0, 0, 0, 0, 1))
    stall(k, Stall.SYNC, Wait.UNPACK0 if bank == 0 else Wait.UNPACK1)
  elif action == 'release':
    k.emit(TT.TTCLEARDVALID(1 << bank, 0))
    stall(k, Stall.SYNC, Wait.MATH)
  elif action == 'wait_valid':
    stall(k, Stall.SYNC, Wait.SRCA_VLD if bank == 0 else Wait.SRCB_VLD)
  elif action == 'wait_free':
    stall(k, Stall.SYNC, Wait.SRCA_CLR if bank == 0 else Wait.SRCB_CLR)
  else: raise ValueError('unknown source flag action')
  k.emit(TT.TTSEMPOST(0))
  pc_sync(k)
  return k
