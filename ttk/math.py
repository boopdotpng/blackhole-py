"""Intent-level TRISC1 math configuration."""
from dataclasses import dataclass

from ttk.tensix import Cfg, MopCfg, Tensix, TensixState


@dataclass
class MathState:
  src_a_format: int = 5
  src_b_format: int = 5
  dst_format: int = 5
  fp32_dest: bool = False
  mop_cfg: MopCfg | None = None


class Math:
  pipe = 1

  def __init__(self, kernel=None, *, state: TensixState | None = None):
    self.k = kernel
    self.tensix = Tensix(kernel, self.pipe, state) if kernel is not None else None
    self.state = MathState()

  @property
  def mop(self):
    if self.tensix is None: raise RuntimeError("math is not attached to a kernel")
    return self.tensix.mop

  def configure_operands(self, *, src_a=5, src_b=5, destination=5, fp32_dest=False):
    self.state = MathState(
      int(src_a), int(src_b), int(destination), bool(fp32_dest), self.state.mop_cfg,
    )
    if self.tensix is not None:
      # ALU format fields are shared CFG state; these values are the Blackhole
      # format nibbles used by ALU_FORMAT_SPEC_REG.
      self.tensix.write_cfg(Cfg.ALU_FORMAT_SPEC_REG,
        (int(src_a) & 0xF) | ((int(src_b) & 0xF) << 8) | ((int(destination) & 0xF) << 16))
      self.tensix.write_cfg(Cfg.ALU_ACC_CTRL, 0x60 if fp32_dest else 0)
    return self

  def configure(self, *, src_a=5, src_b=5, destination=5, fp32_dest=False):
    return self.configure_operands(src_a=src_a, src_b=src_b, destination=destination, fp32_dest=fp32_dest)

  def set_reload_format(self, format):
    return self.configure_operands(src_a=format, src_b=format,
      destination=self.state.dst_format, fp32_dest=self.state.fp32_dest)

  def set_fp32_dest(self, enabled: bool):
    return self.configure_operands(src_a=self.state.src_a_format, src_b=self.state.src_b_format,
      destination=self.state.dst_format, fp32_dest=enabled)

  def configure_mop(self, cfg: MopCfg):
    if self.tensix is None: raise RuntimeError("Math is not attached to a kernel")
    if not isinstance(cfg, MopCfg):
      raise TypeError("math MOP configuration must be a MopCfg")
    self.state.mop_cfg = cfg
    self.tensix.mop.configure(cfg)
    return self

  def run_mop(self, *, cfg: MopCfg | None = None, repeat: int = 1):
    """Configure and execute a named math MOP program."""
    if self.tensix is None: raise RuntimeError("Math is not attached to a kernel")
    if repeat < 1: raise ValueError("repeat must be positive")
    if cfg is not None: self.configure_mop(cfg)
    elif self.state.mop_cfg is None:
      raise RuntimeError("math MOP is not configured")
    return self.tensix.mop.run(repeat=repeat)
