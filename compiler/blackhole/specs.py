from dataclasses import dataclass
from enum import Enum
from ..dtype import DType, dtypes


class Space(Enum):
  DRAM = "dram"
  L1 = "l1"
  SRCA = "srca"
  SRCB = "srcb"
  DST = "dst"
  LREG = "lreg"
  GPR = "gpr"


@dataclass(frozen=True)
class DstZero:
  role: str = "trisc1"


@dataclass(frozen=True)
class MoveToDst:
  dst_slot: int
  role: str = "trisc1"


@dataclass(frozen=True)
class SfpLoadOp:
  dst_slot: int
  sub_row: int = 0
  fmt: str = "fp32"
  role: str = "trisc1"


@dataclass(frozen=True)
class SfpStoreOp:
  dst_slot: int
  sub_row: int = 0
  fmt: str = "fp32"
  role: str = "trisc1"


@dataclass(frozen=True)
class SfpReduceLanes:
  op: str
  role: str = "trisc1"


@dataclass(frozen=True)
class SfpReduceRows:
  op: str
  role: str = "trisc1"


@dataclass(frozen=True)
class SfpBroadcastRows:
  role: str = "trisc1"


@dataclass(frozen=True)
class UnpackOp:
  target: Space
  cb_id: int
  src_dtype: DType = dtypes.fp32
  dst_dtype: DType = dtypes.fp32
  faces: int = 1
  rows: int = 8
  transpose: bool = False
  dst_slot: int = 0
  role: str = "trisc0"
  face_stride: int = 0  # L1 byte stride; zero selects contiguous faces


@dataclass(frozen=True)
class PackOp:
  cb_id: int
  dst_dtype: DType = dtypes.fp32
  blocks: int = 1
  dst_slot: int = 0
  untilize: bool = False
  role: str = "trisc2"


@dataclass(frozen=True)
class SemOp:
  kind: str
  sem_id: int
  role: str


@dataclass(frozen=True)
class StallOp:
  engine: str
  role: str


@dataclass(frozen=True)
class FpuOp:
  op: str
  m_blocks: int = 1
  n_blocks: int = 1
  k_faces: int = 1
  fidelity: int = 3
  dst_slot: int = 0
  src_dtype: DType = dtypes.bf16
  accumulate: bool = False
  role: str = "trisc1"


@dataclass(frozen=True)
class NocRead:
  param_slot: int
  cb_id: int
  nbytes: int
  tid: int = 0
  role: str = "brisc"


@dataclass(frozen=True)
class NocGather:
  param_slot: int
  cb_id: int
  itemsize: int
  index_layouts: tuple[tuple[int, int, int, int, int], ...] = ()  # slot, elements, rows, columns, itemsize
  lanes: int = 128
  tid: int = 0
  role: str = "brisc"


@dataclass(frozen=True)
class IndexTile:
  cb_id: int
  role: str = "brisc"


@dataclass(frozen=True)
class NocWrite:
  param_slot: int
  cb_id: int
  nbytes: int
  tid: int = 1
  role: str = "ncrisc"
  blocks: tuple[int, int] = (1, 1)
  shape_faces: tuple[int, int] = (1, 1)


@dataclass(frozen=True)
class NocMcastRead:
  param_slot: int
  cb_id: int
  axis: str
  gcols: int
  grows: int
  blocks: int
  strip_bytes: int
  strip_stride: int
  slot_stride: int
  ctrl_id: int
  total_slabs: int
  nslots: int = 2
  tid_read: int = 0
  tid_mcast: int = 2
  role: str = "brisc"


@dataclass(frozen=True)
class NocMcastForward:
  stream: NocMcastRead
  role: str = "ncrisc"


@dataclass(frozen=True)
class McastWait:
  ctrl_id: int
  nslots: int = 2
  role: str = "trisc0"


@dataclass(frozen=True)
class McastConsumed:
  ctrl_id: int
  role: str = "trisc0"


@dataclass(frozen=True)
class McastRelease:
  stream: NocMcastRead
  role: str = "ncrisc"


@dataclass(frozen=True)
class NocScatter:
  param_slot: int
  cb_id: int
  itemsize: int
  tid: int = 1
  role: str = "ncrisc"


@dataclass(frozen=True)
class NocWait:
  tid: int
  acked: bool
  role: str


@dataclass(frozen=True)
class CbOp:
  kind: str
  cb_id: int
  role: str
