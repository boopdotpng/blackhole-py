from __future__ import annotations

from mixins.cb import CbMixin
from mixins.flow import FirmwareFlowMixin
from mixins.noc import NocMixin
from mixins.rv import RiscvMemoryMixin
from mixins.tensix import TensixSetupMixin


class FirmwareLibMixin(
  FirmwareFlowMixin,
  NocMixin,
  CbMixin,
  TensixSetupMixin,
  RiscvMemoryMixin,
):
  """Composable firmware helper library for asm.py builders."""
