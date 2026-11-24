import math
from typing import Any
import numpy as np
import hw
from .ops import verify
from .uop import DType, KernelArg, Ops, Space, UOp, dtypes


def _round_bf16(arr: np.ndarray) -> np.ndarray:
  f32 = np.asarray(arr, dtype=np.float32)
  u = f32.view(np.uint32).astype(np.uint64)
  r = ((u + 0x7FFF + ((u >> 16) & 1)) & ~np.uint64(0xFFFF)).astype(np.uint32)
  return r.view(np.float32)


# Exact Blackhole SFPARECIP 128-entry LUT (from ttsim/src/tensix.cpp:approx_recip).
_ARECIP_LUT = np.array([
  127, 125, 123, 121, 119, 117, 116, 114, 112, 110, 109, 107, 105, 104, 102, 100, 99,
  97, 96, 94, 93, 91, 90, 88, 87, 85, 84, 83, 81, 80, 79, 77, 76, 75, 74, 72, 71, 70,
  69, 68, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48,
  47, 46, 45, 44, 43, 42, 41, 40, 40, 39, 38, 37, 36, 35, 35, 34, 33, 32, 31, 31, 30,
  29, 28, 28, 27, 26, 25, 25, 24, 23, 23, 22, 21, 21, 20, 19, 19, 18, 17, 17, 16, 15,
  15, 14, 14, 13, 12, 12, 11, 11, 10, 9, 9, 8, 8, 7, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1,
  1, 0,
], dtype=np.uint32)


def _eval_sfpu_prim(prim, vals: list[Any], out_dt: DType) -> Any:
  p = prim.op
  if p == "ARECIP":
    u = np.asarray(vals[0], dtype=np.float32).view(np.uint32)
    sgn, mag = u & np.uint32(0x80000000), u & np.uint32(0x7FFFFFFF)
    exp = (mag >> np.uint32(23)).astype(np.int32)
    idx = (mag >> np.uint32(16)) & np.uint32(0x7F)
    mid = ((np.uint32(253) - exp.astype(np.uint32)) << np.uint32(23)) | (_ARECIP_LUT[idx] << np.uint32(16))
    res = np.where(mag < np.uint32(0x800000), np.uint32(0x7F800000), np.where(mag < np.uint32(0x7E800000), mid, np.uint32(0)))
    return (sgn | res).view(np.float32)
  if p == "EXEXP":
    u = np.asarray(vals[0], dtype=np.float32).view(np.uint32)
    exp = ((u >> np.uint32(23)) & np.uint32(0xFF)).astype(np.int32)
    return exp if (prim.mod & 1) else (exp - np.int32(127))
  if p == "EXMAN":
    u = np.asarray(vals[0], dtype=np.float32).view(np.uint32)
    hidden = np.uint32(0 if (prim.mod & 1) else (1 << 23))
    return (u & np.uint32(0x7FFFFF)) | hidden
  if p == "SETEXP":
    if prim.mod & 1:
      c = np.asarray(vals[0], dtype=np.float32 if np.asarray(vals[0]).dtype.kind == "f" else np.uint32).view(np.uint32)
      out = (c & np.uint32(0x807FFFFF)) | (np.uint32(prim.imm & 0xFF) << np.uint32(23))
      return out.view(np.float32)
    b = np.asarray(vals[0], dtype=np.float32 if np.asarray(vals[0]).dtype.kind == "f" else np.int32).view(np.uint32)
    c = np.asarray(vals[1], dtype=np.float32).view(np.uint32)
    exp = ((b >> np.uint32(23)) & np.uint32(0xFF)) if (prim.mod & 2) else (b & np.uint32(0xFF))
    return ((c & np.uint32(0x807FFFFF)) | (exp << np.uint32(23))).view(np.float32)
  if p == "SHFT_VAR":
    x = np.asarray(vals[0], dtype=np.uint32)
    s = np.asarray(vals[1], dtype=np.int32)
    pos = (s & np.int32(31)).astype(np.uint32)
    neg = ((-s) & np.int32(31)).astype(np.uint32)
    return np.where(s >= 0, x << pos, x >> neg).astype(np.uint32)
  if p == "CAST_TC2SM":
    c = np.asarray(vals[0], dtype=np.int32).view(np.uint32)
    sgn = c & np.uint32(0x80000000)
    return np.where(sgn != 0, sgn | ((~c + np.uint32(1)) & np.uint32(0x7FFFFFFF)), c).view(np.int32)
  if p == "CAST_SM2F":
    c = np.asarray(vals[0], dtype=np.int32).view(np.uint32)
    mag = (c & np.uint32(0x7FFFFFFF)).astype(np.float32)
    return np.where((c & np.uint32(0x80000000)) != 0, -mag, mag).astype(np.float32)
  raise NotImplementedError(f"eval not implemented for SfpuPrim {p!r}")


def _cast_value(val: Any, dt: DType) -> Any:
  if isinstance(val, np.ndarray):
    if dt is dtypes.bf16: return _round_bf16(val)
    if dt is dtypes.fp32: return val.astype(np.float32)
    if dt is dtypes.i32:  return val.astype(np.int32)
    if dt is dtypes.u32:  return val.astype(np.uint32)
    if dt is dtypes.u8:   return val.astype(np.uint8)
    if dt is dtypes.bool: return val.astype(np.bool_)
    return val.astype(np.float32)
  if dt is dtypes.bool: return bool(val)
  if dt.is_int: return int(val)
  if dt is dtypes.bf16: return float(_round_bf16(np.float32(val)))
  if dt.is_float: return float(np.float32(val))
  return val


def _tile_view(arr: np.ndarray, shape: tuple[int, int] = (32, 32)) -> np.ndarray:
  th, tw = shape
  if arr.ndim >= 2 and arr.shape[-2:] == (th, tw):
    return arr.reshape(-1, th, tw)
  if arr.size % (th * tw) == 0:
    return arr.reshape(-1, th, tw)
  raise ValueError(f"array of shape {arr.shape} cannot be viewed as {shape} tiles")


_FP_IDX = np.arange(32, dtype=np.int32)[:, None]
_LN_IDX = np.arange(32, dtype=np.int32)[None, :]
_FP_ROW = ((_FP_IDX // 8) // 2) * 16 + ((_FP_IDX % 8) // 2) * 4 + (_LN_IDX // 8)
_FP_COL = ((_FP_IDX // 8) % 2) * 16 + (_LN_IDX % 8) * 2 + (_FP_IDX % 2)
_TILE_LANE = (np.arange(32, dtype=np.int32)[:, None] % 4) * 8 + (np.arange(32, dtype=np.int32)[None, :] % 16) // 2


def _tile_to_footprints(tile: np.ndarray) -> np.ndarray:
  return tile[_FP_ROW, _FP_COL]


def _footprints_to_tile(fps: np.ndarray) -> np.ndarray:
  out = np.empty((32, 32), dtype=fps.dtype)
  out[_FP_ROW, _FP_COL] = fps
  return out


def _bcast_lreg_to_tile(lreg: np.ndarray) -> np.ndarray:
  return lreg[_TILE_LANE]


def _reduce_lanes_np(v: np.ndarray, op: Ops, scope: str) -> np.ndarray:
  def fold(a: np.ndarray, axis: int) -> np.ndarray:
    match op:
      case Ops.ADD: return np.broadcast_to(a.sum(axis=axis, keepdims=True), a.shape).copy()
      case Ops.MAX: return np.broadcast_to(a.max(axis=axis, keepdims=True), a.shape).copy()
      case Ops.MIN: return np.broadcast_to(a.min(axis=axis, keepdims=True), a.shape).copy()
      case _: raise ValueError(f"unsupported lane reduce op {op}")
  if v.ndim == 1:
    return fold(v, 0) if scope == "all" else fold(v.reshape(4, 8), -1).reshape(32)
  fps = _tile_to_footprints(v)
  reduced = fold(fps, -1) if scope == "all" else fold(fps.reshape(32, 4, 8), -1).reshape(32, 32)
  return _footprints_to_tile(reduced)


def _init_carry_val(val: Any, space: Space, dt: DType) -> Any:
  if space is Space.DST:
    if isinstance(val, np.ndarray) and val.shape == (32, 32): return _cast_value(val.copy(), dt)
    if isinstance(val, np.ndarray) and val.shape == (32,): return _cast_value(_bcast_lreg_to_tile(val), dt)
    return _cast_value(np.full((32, 32), val, dtype=np.float32 if dt.is_float else np.int32), dt)
  if space is Space.LREG:
    if isinstance(val, np.ndarray) and val.shape == (32,): return _cast_value(val.copy(), dt)
    return _cast_value(np.full((32,), val, dtype=np.float32 if dt.is_float else np.int32), dt)
  return _cast_value(val.copy() if isinstance(val, np.ndarray) else val, dt)




# writes outputs into `buffers` in place
def evaluate(
  sink: UOp,
  buffers: dict[str, np.ndarray],
  *,
  cores: int | None = None,
  check: bool = True,
) -> dict[str, np.ndarray]:
  if check: verify(sink)
  if cores is None:
    if not isinstance(sink.arg, KernelArg): raise ValueError("evaluate needs cores= for a sink without a KernelArg")
    cores = sink.arg.cores
  workers = [divmod(i, hw.WORKER_ROWS) for i in range(cores)]  # column-major (x, y), as firmware numbers them
  coord_to_id = {xy: i for i, xy in enumerate(workers)}
  core_allocs: list[dict[UOp, Any]] = [{} for _ in workers]

  def eval_node(u: UOp, cid: int, env: dict[UOp, Any], cache: dict[UOp, Any]) -> Any:
    if u in env: return env[u]
    if u in cache: return cache[u]
    op, src, arg = u.op, u.src, u.arg

    match op:
      case Ops.CONST:
        res = arg
      case Ops.SPECIAL:
        x, y = workers[cid]
        match arg:
          case "core_id": res = cid
          case "core_x": res = x
          case "core_y": res = y
          case _: raise ValueError(f"unknown SPECIAL {arg!r}")
      case Ops.BUFFER | Ops.ALLOC:
        res = u
      case Ops.SINK:
        for s in src: eval_node(s, cid, env, cache)
        res = None
      case Ops.BARRIER:
        res = None
      case Ops.AFTER:
        for dep in src[1:]: eval_node(dep, cid, env, cache)
        res = eval_node(src[0], cid, env, cache)
      case Ops.IF:
        cond = bool(eval_node(src[0], cid, env, cache))
        if cond: res = eval_node(src[1], cid, env, cache)
        elif len(src) == 3: res = eval_node(src[2], cid, env, cache)
        else: res = None
      case Ops.END:
        ranges = src[1:]
        bounds = [int(eval_node(r.src[0], cid, env, cache)) for r in ranges]
        def run_loops(idx: int, cur_env: dict[UOp, Any]):
          if idx == len(ranges):
            eval_node(src[0], cid, cur_env, {})
            return
          r = ranges[idx]
          for i in range(bounds[idx]):
            nxt_env = dict(cur_env)
            nxt_env[r] = i
            run_loops(idx + 1, nxt_env)
        run_loops(0, env)
        res = None
      case Ops.REDUCE:
        ranges = src[1:]
        bounds = [int(eval_node(r.src[0], cid, env, cache)) for r in ranges]
        acc = None
        def _comb(a, b):
          match arg.op:
            case Ops.ADD: return a + b
            case Ops.MUL: return a * b
            case Ops.MAX: return np.maximum(a, b) if isinstance(a, np.ndarray) else max(a, b)
          return np.minimum(a, b) if isinstance(a, np.ndarray) else min(a, b)
        def run_red(idx: int, cur_env: dict[UOp, Any]):
          nonlocal acc
          if idx == len(ranges):
            v = eval_node(src[0], cid, cur_env, {})
            if arg.space is Space.LREG and isinstance(v, np.ndarray) and v.ndim == 2:
              for fp_vec in _tile_to_footprints(v):
                acc = fp_vec.copy() if acc is None else _comb(acc, fp_vec)
            else:
              acc = (v.copy() if isinstance(v, np.ndarray) else v) if acc is None else _comb(acc, v)
            return
          r = ranges[idx]
          for i in range(bounds[idx]):
            nxt_env = dict(cur_env)
            nxt_env[r] = i
            run_red(idx + 1, nxt_env)
        run_red(0, env)
        if acc is None:
          init = {Ops.ADD: 0.0, Ops.MUL: 1.0, Ops.MAX: -math.inf, Ops.MIN: math.inf}[arg.op]
          if arg.space in (Space.DST, Space.L1): acc = np.full((32, 32), init, dtype=np.float32)
          elif arg.space is Space.LREG: acc = np.full((32,), init, dtype=np.float32)
          else: acc = _cast_value(init, u.dtype)
        res = _cast_value(acc, u.dtype)
      case Ops.LOOP:
        r = src[0]
        carries = src[1::2]
        nexts = src[2::2]
        bound = int(eval_node(r.src[0], cid, env, cache))
        state = [_init_carry_val(eval_node(c.src[0], cid, env, cache), c.space, c.dtype) for c in carries]
        has_fp_sweep = any(c.space is Space.LREG and n.space is Space.DST for c, n in zip(carries, nexts))
        for i in range(bound):
          iter_env = {**env, r: i}
          if has_fp_sweep:
            # Footprint-sweep mode: evaluate outer tile leaves once, then step 32 footprints in hardware order.
            carry_set = set(carries)
            tile_cache: dict[UOp, Any] = {}
            fp_tiles: dict[UOp, np.ndarray] = {}
            # Pre-evaluate every DST/LREG node that does NOT depend on any carry in this loop.
            dep_on_carry: dict[UOp, bool] = {}
            for node in UOp.sink(*nexts).toposort():
              dep_on_carry[node] = (node in carry_set) or any(dep_on_carry.get(s, False) for s in node.src)
            frontier = {s for n in UOp.sink(*nexts).toposort() if dep_on_carry[n] for s in n.src
                        if not dep_on_carry.get(s, False) and s.space is Space.DST}
            for leaf in frontier:
              fp_tiles[leaf] = _tile_to_footprints(eval_node(leaf, cid, iter_env, tile_cache))
            dst_state_fps = {idx: _tile_to_footprints(state[idx]) for idx, c in enumerate(carries) if c.space is Space.DST}
            lreg_state = {idx: state[idx].copy() for idx, c in enumerate(carries) if c.space is Space.LREG}
            scalar_state = {idx: state[idx] for idx, c in enumerate(carries) if c.space not in (Space.DST, Space.LREG)}
            new_dst_fps = {idx: np.empty_like(fps) for idx, fps in dst_state_fps.items()}
            for fp in range(32):
              fp_env = {**iter_env, **{leaf: fps[fp] for leaf, fps in fp_tiles.items()}}
              for idx, c in enumerate(carries):
                if idx in lreg_state: fp_env[c] = lreg_state[idx]
                elif idx in dst_state_fps: fp_env[c] = dst_state_fps[idx][fp]
                else: fp_env[c] = scalar_state[idx]
              fp_cache: dict[UOp, Any] = {}
              nxt_vals = [eval_node(n, cid, fp_env, fp_cache) for n in nexts]
              for idx, (c, nv) in enumerate(zip(carries, nxt_vals)):
                if idx in lreg_state: lreg_state[idx] = _init_carry_val(nv, Space.LREG, c.dtype)
                elif idx in dst_state_fps: new_dst_fps[idx][fp] = _init_carry_val(nv, Space.LREG, c.dtype)
                else: scalar_state[idx] = _cast_value(nv, c.dtype)
            for idx, c in enumerate(carries):
              if idx in lreg_state: state[idx] = lreg_state[idx]
              elif idx in new_dst_fps: state[idx] = _footprints_to_tile(new_dst_fps[idx])
              else: state[idx] = scalar_state[idx]
          else:
            nxt_env = {**iter_env, **{c: (v.copy() if isinstance(v, np.ndarray) else v) for c, v in zip(carries, state)}}
            iter_cache: dict[UOp, Any] = {}
            state = [_init_carry_val(eval_node(n, cid, nxt_env, iter_cache), c.space, c.dtype) for c, n in zip(carries, nexts)]
        res = tuple(state)
      case Ops.GET:
        res = eval_node(src[0], cid, env, cache)[arg]
      case Ops.LOAD:
        if len(src) == 3 and not bool(eval_node(src[2], cid, env, cache)):
          res = np.zeros((32, 32), dtype=np.float32) if u.space in (Space.DST, Space.L1) else _cast_value(0, u.dtype)
        else:
          target = src[0]
          idx = int(eval_node(src[1], cid, env, cache)) if len(src) >= 2 else None
          if target.op is Ops.ALLOC:
            slot = core_allocs[cid].get(target)
            if slot is None:
              slot = _cast_value(0, target.dtype) if target.space is Space.SCALAR else np.zeros(target.arg.shape, dtype=np.float32)
              core_allocs[cid][target] = slot
            res = slot[idx] if idx is not None else (slot.copy() if isinstance(slot, np.ndarray) else slot)
          else:
            arr = buffers[target.arg.name]
            val = arr.reshape(-1)[0 if idx is None else idx]
            res = _cast_value(val.item() if hasattr(val, "item") else val, u.dtype)
      case Ops.STORE:
        if len(src) == 4 and not bool(eval_node(src[3], cid, env, cache)):
          res = None
        else:
          target = src[0]
          if len(src) == 2: idx, val = None, eval_node(src[1], cid, env, cache)
          else: idx, val = int(eval_node(src[1], cid, env, cache)), eval_node(src[2], cid, env, cache)
          if target.op is Ops.ALLOC:
            if idx is None:
              core_allocs[cid][target] = val.copy() if isinstance(val, np.ndarray) else val
            else:
              slot = core_allocs[cid].setdefault(target, np.zeros(target.arg.shape, dtype=np.float32))
              slot[idx] = val
          else:
            arr = buffers[target.arg.name]
            arr.reshape(-1)[0 if idx is None else idx] = val
          res = None
      case Ops.NOC_READ:
        if len(src) == 3 and not bool(eval_node(src[2], cid, env, cache)):
          shape = (32, 32) if arg.tiles == 1 else (arg.tiles, 32, 32)
          res = _cast_value(np.zeros(shape, dtype=np.float32), u.dtype)
        else:
          buf_uop, off_uop = src[0], src[1]
          off = int(eval_node(off_uop, cid, env, cache))
          tiles = _tile_view(buffers[buf_uop.arg.name])
          chunk = tiles[off] if arg.tiles == 1 else tiles[off : off + arg.tiles]
          res = _cast_value(chunk.copy(), u.dtype)
      case Ops.NOC_WRITE:
        if len(src) == 4 and not bool(eval_node(src[3], cid, env, cache)):
          res = None
        else:
          buf_uop, off_uop, val_uop = src[0], src[1], src[2]
          off = int(eval_node(off_uop, cid, env, cache))
          val = eval_node(val_uop, cid, env, cache)
          arr = buffers[buf_uop.arg.name]
          if val_uop.space is Space.SCALAR:
            arr.reshape(-1)[off] = val
          else:
            tiles = _tile_view(arr)
            v = _cast_value(val, buf_uop.dtype)
            if arg.tiles == 1: tiles[off] = v
            else: tiles[off : off + arg.tiles] = v
          res = None
      case Ops.NOC_MCAST:
        val_uop, sender_uop = src
        sender_val = int(eval_node(sender_uop, cid, env, cache))
        x, y = workers[cid]
        match arg.rect:
          case "col": sender_cid = coord_to_id[(x, sender_val)]
          case "row": sender_cid = coord_to_id[(sender_val, y)]
          case _: sender_cid = sender_val
        res = eval_node(val_uop, sender_cid, env, {})
      case Ops.NOC_GATHER | Ops.NOC_ALLGATHER:
        val_uop = src[0]
        x, y = workers[cid]
        match arg.group:
          case "row": peers = [i for i, (px, py) in enumerate(workers) if py == y]
          case "col": peers = [i for i, (px, py) in enumerate(workers) if px == x]
          case "all": peers = list(range(len(workers)))
          case _: peers = list(arg.group)
        res = np.stack([eval_node(val_uop, p, env, {}) for p in peers], axis=0)
      case Ops.UNPACK:
        v = eval_node(src[0], cid, env, cache)
        if arg.transpose: v = v.T
        res = _cast_value(v.copy(), u.dtype)
      case Ops.MVMUL:
        b = eval_node(src[0], cid, env, cache).astype(np.float32)
        a = eval_node(src[1], cid, env, cache).astype(np.float32)
        res = _cast_value(b @ a, u.dtype)
      case Ops.PACK:
        res = _cast_value(eval_node(src[0], cid, env, cache), u.dtype)
      case Ops.LANE_ID:
        row, col = np.indices((32, 32), dtype=np.int32)
        res = _cast_value((row % 4) * 8 + (col % 16) // 2, u.dtype)
      case Ops.REDUCE_ROW:
        v = eval_node(src[0], cid, env, cache)
        r = v.sum(axis=-1, keepdims=True) if arg is Ops.ADD else v.max(axis=-1, keepdims=True)
        res = _cast_value(np.broadcast_to(r, v.shape).copy(), u.dtype)
      case Ops.REDUCE_LANES:
        v = eval_node(src[0], cid, env, cache)
        red_op, scope = arg
        res = _cast_value(_reduce_lanes_np(np.asarray(v), red_op, scope), u.dtype)
      case Ops.ARGMAX:
        v = eval_node(src[0], cid, env, cache)
        idx = np.argmax(v, axis=-1, keepdims=True).astype(np.int32)
        res = np.broadcast_to(idx, v.shape).copy()
      case Ops.CAST:
        res = _cast_value(eval_node(src[0], cid, env, cache), u.dtype)
      case Ops.BITCAST:
        v = eval_node(src[0], cid, env, cache)
        np_dt = {dtypes.fp32: np.float32, dtypes.i32: np.int32, dtypes.u32: np.uint32}[u.dtype]
        res = np.asarray(v).view(np_dt)
        if not isinstance(v, np.ndarray): res = res.item()
      case Ops.SFPU:
        vals = [eval_node(s, cid, env, cache) for s in src]
        if any(isinstance(v, np.ndarray) and v.ndim == 2 for v in vals):
          vals = [_bcast_lreg_to_tile(v) if (isinstance(v, np.ndarray) and v.shape == (32,)) else v for v in vals]
        res = _cast_value(_eval_sfpu_prim(arg, vals, u.dtype), u.dtype)
      case Ops.REPLAY | Ops.MOP:
        raise NotImplementedError("REPLAY/MOP escape hatches hold raw Tensix words and cannot be functionally evaluated in Python")
      case _:
        vals = [eval_node(s, cid, env, cache) for s in src]
        # Broadcast (32,) LREG operands into (32, 32) DST operands by exact Blackhole SFPU lane.
        if any(isinstance(v, np.ndarray) and v.ndim == 2 for v in vals):
          vals = [_bcast_lreg_to_tile(v) if (isinstance(v, np.ndarray) and v.shape == (32,)) else v for v in vals]
        is_vec = any(isinstance(v, np.ndarray) for v in vals)
        match op:
          case Ops.ADD: out = vals[0] + vals[1]
          case Ops.SUB: out = vals[0] - vals[1]
          case Ops.MUL: out = vals[0] * vals[1]
          case Ops.MULACC:
            neg_ab, neg_c = arg if isinstance(arg, tuple) else (False, False)
            ab = -(vals[0] * vals[1]) if neg_ab else (vals[0] * vals[1])
            c = -vals[2] if neg_c else vals[2]
            out = ab + c
          case Ops.DIV: out = (vals[0] / vals[1]) if u.dtype.is_float else (vals[0] // vals[1])
          case Ops.MOD: out = vals[0] % vals[1]
          case Ops.MAX: out = np.maximum(vals[0], vals[1]) if is_vec else max(vals[0], vals[1])
          case Ops.MIN: out = np.minimum(vals[0], vals[1]) if is_vec else min(vals[0], vals[1])
          case Ops.NEG: out = -vals[0]
          case Ops.ABS: out = np.abs(vals[0]) if is_vec else abs(vals[0])
          case Ops.NOT: out = (np.logical_not(vals[0]) if u.dtype is dtypes.bool else np.bitwise_not(vals[0])) if is_vec else ((not vals[0]) if u.dtype is dtypes.bool else ~vals[0])
          case Ops.EXP2: out = np.exp2(vals[0]) if is_vec else math.exp2(vals[0])
          case Ops.LOG2: out = np.log2(vals[0]) if is_vec else math.log2(vals[0])
          case Ops.SIN: out = np.sin(vals[0]) if is_vec else math.sin(vals[0])
          case Ops.SQRT: out = np.sqrt(vals[0]) if is_vec else math.sqrt(vals[0])
          case Ops.RSQRT: out = (1.0 / np.sqrt(vals[0])) if is_vec else (1.0 / math.sqrt(vals[0]))
          case Ops.RECIP: out = (1.0 / vals[0]) if is_vec else (1.0 / vals[0])
          case Ops.CMPLT: out = vals[0] < vals[1]
          case Ops.CMPEQ: out = vals[0] == vals[1]
          case Ops.CMPNE: out = vals[0] != vals[1]
          case Ops.WHERE: out = np.where(vals[0], vals[1], vals[2]) if is_vec else (vals[1] if vals[0] else vals[2])
          case Ops.AND: out = (np.logical_and(vals[0], vals[1]) if u.dtype is dtypes.bool else np.bitwise_and(vals[0], vals[1])) if is_vec else ((vals[0] and vals[1]) if u.dtype is dtypes.bool else (vals[0] & vals[1]))
          case Ops.OR: out = (np.logical_or(vals[0], vals[1]) if u.dtype is dtypes.bool else np.bitwise_or(vals[0], vals[1])) if is_vec else ((vals[0] or vals[1]) if u.dtype is dtypes.bool else (vals[0] | vals[1]))
          case Ops.XOR: out = (np.logical_xor(vals[0], vals[1]) if u.dtype is dtypes.bool else np.bitwise_xor(vals[0], vals[1])) if is_vec else ((vals[0] != vals[1]) if u.dtype is dtypes.bool else (vals[0] ^ vals[1]))
          case Ops.SHL: out = vals[0] << vals[1]
          case Ops.SHR: out = vals[0] >> vals[1]
          case _: raise NotImplementedError(f"eval not implemented for {op}")
        res = _cast_value(out, u.dtype)

    if op not in (Ops.LOAD, Ops.STORE, Ops.NOC_WRITE, Ops.END, Ops.SINK, Ops.BARRIER, Ops.AFTER):
      cache[u] = res
    return res

  stages: list[list[UOp]] = [[]]
  if sink.op is Ops.SINK:
    for eff in sink.src:
      if eff.op is Ops.BARRIER: stages.append([])
      else: stages[-1].append(eff)
  else:
    stages[0].append(sink)

  for stage in stages:
    if not stage: continue
    for cid in range(len(workers)):
      cache: dict[UOp, Any] = {}
      for eff in stage:
        eval_node(eff, cid, {}, cache)

  return buffers
