#!/usr/bin/env python3
"""Local firmware assembly viewer for blackhole-py.

Run:
  python fw/view.py
"""

from __future__ import annotations

import ast
import html
import importlib
import json
import os
import re
import socket
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
FW_DIR = ROOT / "fw"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8765


@dataclass(frozen=True)
class Symbol:
  name: str
  value: int
  expr: str
  file: str
  line: int

  def to_json(self) -> dict[str, Any]:
    return {
      "name": self.name,
      "value": self.value & 0xFFFFFFFFFFFFFFFF,
      "hex": hex(self.value),
      "expr": self.expr,
      "file": self.file,
      "line": self.line,
    }


class ConstEvaluator(ast.NodeVisitor):
  def __init__(self, env: dict[str, Any]):
    self.env = env

  def visit_Constant(self, node: ast.Constant) -> Any:
    if isinstance(node.value, (int, str, bytes)):
      return node.value
    raise ValueError("unsupported constant")

  def visit_Name(self, node: ast.Name) -> Any:
    if node.id in self.env:
      return self.env[node.id]
    raise ValueError(f"unknown name {node.id}")

  def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
    value = self.visit(node.operand)
    if isinstance(node.op, ast.UAdd):
      return +value
    if isinstance(node.op, ast.USub):
      return -value
    if isinstance(node.op, ast.Invert):
      return ~value
    raise ValueError("unsupported unary op")

  def visit_BinOp(self, node: ast.BinOp) -> Any:
    left = self.visit(node.left)
    right = self.visit(node.right)
    ops = {
      ast.Add: lambda a, b: a + b,
      ast.Sub: lambda a, b: a - b,
      ast.Mult: lambda a, b: a * b,
      ast.FloorDiv: lambda a, b: a // b,
      ast.Mod: lambda a, b: a % b,
      ast.LShift: lambda a, b: a << b,
      ast.RShift: lambda a, b: a >> b,
      ast.BitOr: lambda a, b: a | b,
      ast.BitAnd: lambda a, b: a & b,
      ast.BitXor: lambda a, b: a ^ b,
    }
    for cls, fn in ops.items():
      if isinstance(node.op, cls):
        return fn(left, right)
    raise ValueError("unsupported binary op")

  def visit_List(self, node: ast.List) -> list[Any]:
    return [self.visit(elt) for elt in node.elts]

  def visit_Tuple(self, node: ast.Tuple) -> tuple[Any, ...]:
    return tuple(self.visit(elt) for elt in node.elts)

  def visit_Dict(self, node: ast.Dict) -> dict[Any, Any]:
    return {self.visit(k): self.visit(v) for k, v in zip(node.keys, node.values) if k is not None}

  def generic_visit(self, node: ast.AST) -> Any:
    raise ValueError(f"unsupported expression {type(node).__name__}")


def parse_symbols() -> tuple[list[Symbol], dict[int, list[Symbol]]]:
  env: dict[str, Any] = {}
  symbols: list[Symbol] = []
  files = [ROOT / "asm.py", ROOT / "ttk" / "hw" / "l1.py", ROOT / "ttk" / "hw" / "mmio.py"]
  files.extend(sorted(FW_DIR.glob("*.py")))

  for path in files:
    if not path.exists() or path.name == "view.py":
      continue
    try:
      tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError:
      continue
    rel = str(path.relative_to(ROOT))
    for node in tree.body:
      if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        continue
      targets = node.targets if isinstance(node, ast.Assign) else [node.target]
      names = [target.id for target in targets if isinstance(target, ast.Name) and target.id.isupper()]
      if not names:
        continue
      try:
        value = ConstEvaluator(env).visit(node.value)  # type: ignore[arg-type]
      except Exception:
        continue
      for name in names:
        env[name] = value
        if isinstance(value, int):
          expr = ast.get_source_segment(path.read_text(), node.value) or repr(value)
          symbols.append(Symbol(name, value, expr, rel, node.lineno))

  by_value: dict[int, list[Symbol]] = {}
  for sym in symbols:
    by_value.setdefault(sym.value, []).append(sym)
    by_value.setdefault(sym.value & 0xFFFFFFFF, []).append(sym)
  for value in by_value:
    by_value[value] = sorted({s.name: s for s in by_value[value]}.values(), key=lambda s: (s.file, s.line, s.name))
  return symbols, by_value


def parse_inst(text: str) -> tuple[str, list[str]]:
  m = re.match(r"([A-Za-z0-9_]+)\((.*)\)$", text.strip())
  if not m:
    return text.strip(), []
  args = []
  cur = []
  depth = 0
  for ch in m.group(2):
    if ch == "," and depth == 0:
      args.append("".join(cur).strip())
      cur = []
      continue
    if ch in "([{":
      depth += 1
    elif ch in ")]}":
      depth -= 1
    cur.append(ch)
  if cur or m.group(2).strip():
    args.append("".join(cur).strip())
  return m.group(1), args


def parse_int_arg(value: str) -> int | None:
  try:
    return int(value.replace("_", ""), 0)
  except ValueError:
    return None


def signed32(value: int) -> int:
  value &= 0xFFFFFFFF
  return value - 0x100000000 if value & 0x80000000 else value


def is_address_symbol(sym: Symbol) -> bool:
  if sym.value >= 0x1000 or sym.value < 0:
    return True
  small_address_words = (
    "ADDR", "BASE", "PTR", "PC", "STATUS", "DEBUG", "SIGNAL", "MAILBOX",
    "QUEUE",
  )
  return any(word in sym.name for word in small_address_words)


def build_comment(value: int, symbols_by_value: dict[int, list[Symbol]]) -> str:
  matches = symbols_by_value.get(value) or symbols_by_value.get(value & 0xFFFFFFFF) or []
  matches = [sym for sym in matches if is_address_symbol(sym)]
  if not matches:
    return ""
  names = ", ".join(sym.name for sym in matches[:4])
  suffix = "" if len(matches) <= 4 else f" +{len(matches) - 4}"
  return f"{names}{suffix} = 0x{value & 0xFFFFFFFF:X}"


BRANCH_OPS = {"beq", "bne", "blt", "bge", "bltu", "bgeu", "jal"}


def describe_target(pc: int, op: str, args: list[str], labels_by_addr: dict[int, list[str]]) -> tuple[str, int | None]:
  if op in BRANCH_OPS and args:
    imm = parse_int_arg(args[-1])
    if imm is None:
      return "", None
    target = pc + imm
    labels = labels_by_addr.get(target, [])
    if labels:
      return f"-> {labels[0]} (0x{target:08X})", target
    return f"-> 0x{target:08X}", target
  if op == "jalr" and len(args) >= 2:
    return "indirect jump/return", None
  return "", None


def firmware_json() -> dict[str, Any]:
  if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

  for name in list(sys.modules):
    if name == "fw" or name.startswith("fw.") or name in {"asm", "dsl"} or name.startswith("ttk."):
      sys.modules.pop(name, None)
  importlib.invalidate_caches()

  from fw import build_all  # type: ignore

  symbols, symbols_by_value = parse_symbols()
  kernels = []
  for kernel_name, kernel in build_all().items():
    labels_by_addr: dict[int, list[str]] = {}
    for label, addr in getattr(kernel, "labels", {}).items():
      labels_by_addr.setdefault(addr, []).append(label)
    for addr in labels_by_addr:
      labels_by_addr[addr].sort()

    rows = []
    pending_lui: dict[str, tuple[int, int]] = {}
    for idx, inst in enumerate(kernel.instructions()):
      pc = kernel.base + idx * 4
      word = int(inst) & 0xFFFFFFFF
      asm_text = repr(inst)
      op, args = parse_inst(asm_text)
      labels = labels_by_addr.get(pc, [])
      comment_parts: list[str] = []
      target_text, target_pc = describe_target(pc, op, args, labels_by_addr)
      if target_text:
        comment_parts.append(target_text)

      symbol_value: int | None = None
      if op == "lui" and len(args) >= 2:
        imm = parse_int_arg(args[1])
        if imm is not None:
          pending_lui[args[0]] = (imm, pc)
          symbol_value = signed32(imm)
      elif op == "addi" and len(args) >= 3:
        imm = parse_int_arg(args[2])
        if imm is not None and args[1] == "zero":
          symbol_value = imm
        elif imm is not None and args[0] == args[1] and args[0] in pending_lui:
          hi, _ = pending_lui[args[0]]
          symbol_value = signed32(hi + imm)
          pending_lui.pop(args[0], None)
      if symbol_value is not None:
        sym_comment = build_comment(symbol_value, symbols_by_value)
        if sym_comment:
          comment_parts.append(sym_comment)

      rows.append({
        "pc": pc,
        "pcHex": f"{pc:08x}",
        "word": word,
        "wordHex": f"{word:08x}",
        "asm": asm_text,
        "op": op,
        "args": args,
        "labels": labels,
        "comment": " | ".join(comment_parts),
        "targetPc": target_pc,
        "isBranch": op in BRANCH_OPS,
      })

    segments = []
    for seg in kernel.compile():
      segments.append({
        "addr": seg.addr,
        "addrHex": f"0x{seg.addr:08X}",
        "size": len(seg.data),
        "label": seg.label,
      })

    histogram: dict[str, int] = {}
    for row in rows:
      histogram[row["op"]] = histogram.get(row["op"], 0) + 1
    op_hist = sorted(histogram.items(), key=lambda kv: (-kv[1], kv[0]))

    kernels.append({
      "name": kernel_name,
      "base": kernel.base,
      "baseHex": f"0x{kernel.base:08X}",
      "instructionCount": len(rows),
      "byteCount": len(rows) * 4,
      "labels": [{"name": name, "addr": addr, "addrHex": f"0x{addr:08X}"} for name, addr in sorted(kernel.labels.items(), key=lambda item: item[1])],
      "segments": segments,
      "rows": rows,
      "opHistogram": [{"op": op, "count": count} for op, count in op_hist],
    })

  return {
    "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    "root": str(ROOT),
    "kernels": kernels,
    "symbols": [sym.to_json() for sym in sorted(symbols, key=lambda s: (s.value, s.name))],
  }


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Blackhole FW Viewer</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0e1013;
      --panel: #15181d;
      --panel2: #1c2026;
      --line: #2a313b;
      --line-soft: #20262e;
      --text: #e7ecf2;
      --muted: #8a94a3;
      --dim: #6b7585;
      --accent: #6ab6ff;
      --gold: #e9b949;
      --mint: #5cd6a4;
      --red: #ff7b72;
      --purple: #c89bff;
      --orange: #ffb074;
      --hit: rgba(233,185,73,.30);
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Inter, sans-serif;
      overflow: hidden;
    }
    button, input { font: inherit; color: inherit; }
    .app {
      display: grid;
      grid-template-columns: 16rem 1fr 18rem;
      height: 100vh;
    }
    aside, main { min-height: 0; min-width: 0; }
    main {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .left, .right {
      background: var(--panel);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .left  { border-right: 1px solid var(--line); }
    .right { border-left:  1px solid var(--line); }

    .brand {
      padding: .9rem 1rem .7rem;
      border-bottom: 1px solid var(--line);
    }
    .brand h1 { margin: 0; font-size: 1rem; font-weight: 600; letter-spacing: .01em; }
    .brand p  { margin: .25rem 0 0; color: var(--muted); font-size: .76rem; }

    .kernels { padding: .55rem; display: grid; gap: .35rem; overflow: auto; }
    .kernel {
      border: 1px solid var(--line);
      background: transparent;
      color: var(--text);
      border-radius: 6px;
      padding: .55rem .65rem;
      text-align: left;
      cursor: pointer;
      transition: background .12s, border-color .12s;
    }
    .kernel:hover { background: var(--panel2); }
    .kernel.active {
      background: var(--panel2);
      border-color: var(--accent);
      box-shadow: inset 3px 0 0 var(--accent);
    }
    .kernel strong { display: block; font-size: .88rem; font-weight: 600; }
    .kernel span   { color: var(--muted); font-size: .72rem; }

    .toolbar {
      display: grid;
      grid-template-columns: 1fr auto auto auto auto;
      gap: .5rem;
      padding: .55rem .75rem;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      align-items: center;
    }
    .search {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--line);
      color: var(--text);
      border-radius: 6px;
      padding: .5rem .65rem;
      outline: none;
    }
    .search::placeholder { color: var(--dim); }
    .search:focus { border-color: var(--accent); }
    .toggle {
      border: 1px solid var(--line);
      background: var(--panel2);
      color: var(--muted);
      border-radius: 6px;
      padding: .45rem .65rem;
      cursor: pointer;
      font-size: .78rem;
      white-space: nowrap;
    }
    .toggle:hover { color: var(--text); }
    .toggle.active { background: var(--accent); color: #06121f; border-color: var(--accent); }
    .toggle.icon { padding: .45rem .55rem; }

    .stats {
      display: flex; flex-wrap: wrap; gap: 0 1.2rem;
      padding: .35rem .9rem;
      border-bottom: 1px solid var(--line);
      color: var(--muted); font-size: .73rem;
    }
    .stats b { color: var(--text); font-weight: 600; }
    .stats .match { color: var(--gold); }

    .viewer {
      flex: 1;
      min-height: 0;
      overflow: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      font-size: 12.5px;
      line-height: 1.55;
      background: var(--bg);
    }
    table { width: 100%; border-collapse: collapse; }
    thead th {
      position: sticky; top: 0; z-index: 1;
      background: var(--panel);
      color: var(--dim);
      font-weight: 500;
      font-size: .7rem;
      text-transform: uppercase;
      letter-spacing: .06em;
      text-align: left;
      padding: .35rem .65rem;
      border-bottom: 1px solid var(--line);
    }
    tbody tr { border-bottom: 1px solid var(--line-soft); }
    tbody tr:hover  { background: rgba(106,182,255,.06); }
    tbody tr.focus  { background: rgba(106,182,255,.13); box-shadow: inset 3px 0 0 var(--accent); }
    tbody tr.target { animation: flash 1s ease-out; }
    @keyframes flash {
      0%   { background: rgba(233,185,73,.45); }
      100% { background: transparent; }
    }
    td { padding: .1rem .65rem; vertical-align: top; white-space: nowrap; }

    tr.label-row td {
      padding: .8rem .65rem .15rem;
      color: var(--gold);
      font-weight: 600;
      border-bottom: 1px dashed rgba(233,185,73,.25);
    }
    tr.label-row td span.lbl { color: var(--gold); }
    tr.label-row td span.lbl::after { content: ":"; color: var(--dim); }

    .pc { color: var(--accent); width: 6.5rem; cursor: copy; }
    .pc:hover { text-decoration: underline; }
    .word { color: var(--dim); width: 5.5rem; }
    .arrow {
      width: 1.4rem; color: var(--gold); text-align: center;
      cursor: pointer; user-select: none;
    }
    .arrow:hover { color: var(--orange); }
    .asm { color: var(--text); min-width: 22rem; white-space: pre; }
    .comment { color: var(--mint); white-space: pre-wrap; min-width: 14rem; }
    .comment.dim { color: var(--dim); }

    /* asm tokens */
    .tok-op   { font-weight: 600; }
    .op-lui, .op-auipc          { color: var(--purple); }
    .op-jal, .op-jalr           { color: var(--gold); }
    .op-beq, .op-bne, .op-blt,
    .op-bge, .op-bltu, .op-bgeu { color: var(--gold); }
    .op-lw, .op-lbu, .op-lhu,
    .op-sw, .op-sh, .op-sb      { color: var(--orange); }
    .op-ecall, .op-ebreak,
    .op-mret, .op-fence,
    .op-csrrw, .op-csrrs, .op-csrrc,
    .op-csrrwi, .op-csrrsi, .op-csrrci { color: var(--red); }
    .tok-reg  { color: #b9c4d4; }
    .tok-num  { color: #d6c89a; }
    .tok-paren, .tok-comma { color: var(--dim); }

    mark {
      background: var(--hit);
      color: inherit;
      padding: 0 .08rem;
      border-radius: 2px;
    }

    .section {
      padding: .65rem .85rem;
      border-bottom: 1px solid var(--line);
      display: flex; flex-direction: column;
      min-height: 0;
    }
    .section h2 {
      margin: 0 0 .45rem;
      font-size: .7rem;
      color: var(--dim);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .07em;
      display: flex; justify-content: space-between; align-items: baseline;
    }
    .section h2 small { font-weight: 500; color: var(--dim); }
    .scroll { overflow: auto; min-height: 0; }
    .right .section.grow { flex: 1; }

    .pill {
      border: 1px solid var(--line-soft);
      background: var(--panel2);
      border-radius: 6px;
      padding: .35rem .5rem;
      margin-bottom: .3rem;
      cursor: pointer;
      transition: border-color .12s;
    }
    .pill:hover { border-color: var(--accent); }
    .pill b { display: block; font-size: .76rem; font-weight: 600; }
    .pill span { color: var(--muted); font-size: .7rem; font-family: ui-monospace, monospace; }

    .hist { display: grid; gap: .15rem; }
    .hist .row {
      display: grid; grid-template-columns: 5rem 1fr 2.5rem;
      gap: .4rem; align-items: center;
      font-size: .73rem;
    }
    .hist .row code { color: var(--text); font-family: ui-monospace, monospace; }
    .hist .row .bar {
      height: 6px; background: var(--accent);
      border-radius: 3px; opacity: .8;
    }
    .hist .row .ct { color: var(--muted); text-align: right; }

    .empty { color: var(--muted); padding: 1rem; font-size: .82rem; }

    .help {
      position: fixed; right: 1rem; bottom: 1rem;
      background: var(--panel2);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: .75rem 1rem;
      font-size: .75rem;
      color: var(--muted);
      max-width: 22rem;
      box-shadow: 0 10px 30px rgba(0,0,0,.5);
      display: none;
      z-index: 10;
    }
    .help.show { display: block; }
    .help h3 { margin: 0 0 .4rem; color: var(--text); font-size: .8rem; }
    .help dl { display: grid; grid-template-columns: auto 1fr; gap: .1rem .8rem; margin: 0; }
    .help dt { color: var(--gold); font-family: ui-monospace, monospace; }
    .help dd { margin: 0; }

    @media (max-width: 1100px) {
      .app { grid-template-columns: 13rem 1fr; }
      .right { display: none; }
      .toolbar { grid-template-columns: 1fr auto auto; }
      .hide-small { display: none; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="left">
      <div class="brand">
        <h1>Blackhole FW</h1>
        <p>RISC-V firmware with Python-constant comments and branch hints.</p>
      </div>
      <div id="kernels" class="kernels"></div>
    </aside>

    <main>
      <div class="toolbar">
        <input id="search" class="search" placeholder="Filter — try lui, t0, 0x1c, mailbox..." autocomplete="off" spellcheck="false">
        <button id="comments" class="toggle active" title="Toggle comments (c)">Comments</button>
        <button id="labels" class="toggle active hide-small" title="Toggle labels (l)">Labels</button>
        <button id="reload" class="toggle" title="Reload (r)">↻</button>
        <button id="helpBtn" class="toggle icon" title="Shortcuts (?)">?</button>
      </div>
      <div id="stats" class="stats"></div>
      <div id="viewer" class="viewer"></div>
    </main>

    <aside class="right">
      <div class="section">
        <h2>Segments <small id="segCount"></small></h2>
        <div id="segments" class="scroll"></div>
      </div>
      <div class="section">
        <h2>Op mix <small id="opCount"></small></h2>
        <div id="histogram" class="scroll hist"></div>
      </div>
      <div class="section">
        <h2>Labels <small id="lblCount"></small></h2>
        <div id="labelList" class="scroll" style="max-height: 12rem"></div>
      </div>
      <div class="section grow">
        <h2>Symbols <small id="symCount"></small></h2>
        <div id="symbolList" class="scroll" style="flex:1"></div>
      </div>
    </aside>
  </div>

  <div id="help" class="help">
    <h3>Keyboard shortcuts</h3>
    <dl>
      <dt>/</dt><dd>focus search</dd>
      <dt>Esc</dt><dd>clear search / close help</dd>
      <dt>n / N</dt><dd>next / previous match</dd>
      <dt>j / k</dt><dd>scroll match down / up</dd>
      <dt>g / G</dt><dd>top / bottom of kernel</dd>
      <dt>[ / ]</dt><dd>previous / next kernel</dd>
      <dt>c</dt><dd>toggle comments</dd>
      <dt>l</dt><dd>toggle labels</dd>
      <dt>r</dt><dd>reload firmware</dd>
      <dt>Click</dt><dd>PC = copy · arrow = jump</dd>
      <dt>?</dt><dd>toggle this panel</dd>
    </dl>
  </div>

  <script>
  (() => {
    const REG = new Set(["zero","ra","sp","gp","tp",
      "t0","t1","t2","t3","t4","t5","t6",
      "s0","fp","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11",
      "a0","a1","a2","a3","a4","a5","a6","a7",
      "pc"]);

    const state = {
      data: null,
      kernel: 0,
      comments: true,
      labels: true,
      q: "",
      matchIdx: 0,
      matchCount: 0,
    };

    const $  = (id) => document.getElementById(id);
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c =>
      ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

    const hi = (text) => {
      if (!state.q) return esc(text);
      const q = state.q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return esc(text).replace(new RegExp(q, "ig"), m => `<mark>${m}</mark>`);
    };

    const current = () => state.data.kernels[state.kernel];

    // ---- URL hash routing ---------------------------------------------------
    function readHash() {
      const params = new URLSearchParams(location.hash.slice(1));
      const k = params.get("k");
      const pc = params.get("pc");
      const q = params.get("q");
      if (state.data && k) {
        const idx = state.data.kernels.findIndex(x => x.name === k);
        if (idx >= 0) state.kernel = idx;
      }
      if (q != null) {
        state.q = q;
        $("search").value = q;
      }
      if (pc) requestAnimationFrame(() => scrollToPc(parseInt(pc, 16)));
    }
    function writeHash() {
      const params = new URLSearchParams();
      if (state.data) params.set("k", current().name);
      if (state.q)    params.set("q", state.q);
      const h = "#" + params.toString();
      if (location.hash !== h) history.replaceState(null, "", h);
    }

    // ---- ASM tokenisation ---------------------------------------------------
    function renderAsm(row) {
      const opClass = "op-" + row.op.replace(/_/g, "-");
      const op = `<span class="tok-op ${opClass}">${hi(row.op)}</span>`;
      const args = row.args.map(a => {
        if (REG.has(a)) return `<span class="tok-reg">${hi(a)}</span>`;
        if (/^-?(0x[0-9a-f]+|\d+)$/i.test(a))
          return `<span class="tok-num">${hi(a)}</span>`;
        return hi(a);
      }).join('<span class="tok-comma">, </span>');
      return `${op}<span class="tok-paren">(</span>${args}<span class="tok-paren">)</span>`;
    }

    // ---- Loading ------------------------------------------------------------
    async function load() {
      $("viewer").innerHTML = '<div class="empty">Loading firmware…</div>';
      try {
        const res = await fetch("/api/firmware?ts=" + Date.now());
        state.data = await res.json();
        if (state.data.error) throw new Error(state.data.error);
        if (state.kernel >= state.data.kernels.length) state.kernel = 0;
        readHash();
        renderAll();
      } catch (err) {
        $("viewer").innerHTML = `<div class="empty">Error: ${esc(err.message || err)}</div>`;
      }
    }

    // ---- Render -------------------------------------------------------------
    function renderAll() {
      renderKernels();
      renderSidebars();
      renderTable();
      writeHash();
    }

    function renderKernels() {
      $("kernels").innerHTML = state.data.kernels.map((k, i) => `
        <button class="kernel ${i === state.kernel ? "active" : ""}" data-kernel="${i}">
          <strong>${esc(k.name)}</strong>
          <span>${esc(k.baseHex)} · ${k.instructionCount} insns · ${(k.byteCount/1024).toFixed(1)} KiB</span>
        </button>`).join("");
      document.querySelectorAll("[data-kernel]").forEach(btn => btn.onclick = () => {
        state.kernel = Number(btn.dataset.kernel);
        renderAll();
      });
    }

    function renderSidebars() {
      const k = current();

      $("segments").innerHTML = k.segments.map(s =>
        `<div class="pill"><b>${esc(s.label)}</b><span>${esc(s.addrHex)} · ${s.size} B</span></div>`
      ).join("") || '<div class="empty">No segments</div>';
      $("segCount").textContent = `${k.segments.length}`;

      const hist = k.opHistogram || [];
      const maxCount = hist.length ? hist[0].count : 1;
      $("histogram").innerHTML = hist.slice(0, 18).map(h => `
        <div class="row" data-op="${esc(h.op)}" title="Filter by ${esc(h.op)}">
          <code>${esc(h.op)}</code>
          <div class="bar" style="width:${(h.count/maxCount*100).toFixed(1)}%"></div>
          <div class="ct">${h.count}</div>
        </div>`).join("") || '<div class="empty">No instructions</div>';
      $("opCount").textContent = `${hist.length}`;
      document.querySelectorAll("[data-op]").forEach(el => el.onclick = () => {
        $("search").value = el.dataset.op;
        state.q = el.dataset.op;
        state.matchIdx = 0;
        renderTable();
        writeHash();
      });

      $("labelList").innerHTML = k.labels.map(l =>
        `<div class="pill" data-pc="${l.addr}"><b>${esc(l.name)}</b><span>${esc(l.addrHex)}</span></div>`
      ).join("") || '<div class="empty">No labels</div>';
      $("lblCount").textContent = `${k.labels.length}`;

      const ql = state.q.toLowerCase();
      const symbols = state.data.symbols.filter(s =>
        !state.q || (`${s.name} ${s.hex} ${s.expr} ${s.file}`).toLowerCase().includes(ql)
      );
      $("symbolList").innerHTML = symbols.slice(0, 250).map(s =>
        `<div class="pill" data-symbol="${esc(s.hex)}"><b>${hi(s.name)}</b><span>${esc(s.hex)} · ${esc(s.file)}:${s.line}</span></div>`
      ).join("") || '<div class="empty">No matching symbols</div>';
      $("symCount").textContent = `${symbols.length}${symbols.length > 250 ? "+" : ""}`;

      document.querySelectorAll("[data-pc]").forEach(el => el.onclick = () => scrollToPc(Number(el.dataset.pc)));
      document.querySelectorAll("[data-symbol]").forEach(el => el.onclick = () => {
        $("search").value = el.dataset.symbol;
        state.q = el.dataset.symbol;
        state.matchIdx = 0;
        renderTable();
        renderSidebars();
        writeHash();
      });
    }

    function rowMatches(row) {
      if (!state.q) return true;
      const hay = `${row.pcHex} ${row.wordHex} ${row.asm} ${row.comment} ${row.labels.join(" ")}`.toLowerCase();
      return hay.includes(state.q.toLowerCase());
    }

    function renderTable() {
      const k = current();
      const parts = [
        '<table>',
        '<thead><tr>',
        '<th>PC</th><th>Word</th><th></th><th>Asm</th><th>Notes</th>',
        '</tr></thead><tbody>'
      ];
      let matches = 0;
      for (const row of k.rows) {
        const match = rowMatches(row);
        if (state.q && !match) continue;
        if (match && state.q) matches++;

        if (state.labels && row.labels.length) {
          parts.push(
            `<tr class="label-row" id="pc-${row.pc}"><td colspan="5">` +
            row.labels.map(l => `<span class="lbl">${esc(l)}</span>`).join(" ") +
            `</td></tr>`
          );
        }

        let arrow = "";
        if (row.isBranch && row.targetPc != null) {
          const dir = row.targetPc > row.pc ? "↓" : (row.targetPc < row.pc ? "↑" : "↻");
          arrow = `<span class="arrow" data-target="${row.targetPc}" title="Jump to 0x${row.targetPc.toString(16).padStart(8,'0')}">${dir}</span>`;
        }

        const commentHtml = state.comments && row.comment
          ? hi(row.comment)
          : (row.isBranch && row.targetPc != null
              ? `<span class="comment dim">→ 0x${row.targetPc.toString(16).padStart(8,'0')}</span>`
              : "");

        parts.push(
          `<tr id="line-${row.pc}">` +
          `<td class="pc" data-copy="0x${row.pcHex}">${hi(row.pcHex)}</td>` +
          `<td class="word">${hi(row.wordHex)}</td>` +
          `<td class="arrow-cell">${arrow}</td>` +
          `<td class="asm">${renderAsm(row)}</td>` +
          `<td class="comment">${commentHtml}</td>` +
          `</tr>`
        );
      }
      parts.push('</tbody></table>');

      state.matchCount = state.q ? matches : k.instructionCount;
      $("viewer").innerHTML = matches === 0 && state.q
        ? '<div class="empty">No matching instructions</div>'
        : parts.join("");

      $("stats").innerHTML = `
        <span><b>${esc(k.name)}</b></span>
        <span>base <b>${esc(k.baseHex)}</b></span>
        <span><b>${k.instructionCount}</b> insns · ${(k.byteCount/1024).toFixed(1)} KiB</span>
        <span><b>${k.labels.length}</b> labels</span>
        ${state.q ? `<span class="match"><b>${matches}</b> matches</span>` : ""}
        <span style="margin-left:auto">${esc(state.data.generatedAt)}</span>
      `;

      // Wire row interactions
      document.querySelectorAll(".arrow[data-target]").forEach(el =>
        el.onclick = () => scrollToPc(Number(el.dataset.target)));
      document.querySelectorAll(".pc[data-copy]").forEach(el => {
        el.onclick = () => copyToClipboard(el.dataset.copy, el);
      });
    }

    // ---- Navigation ---------------------------------------------------------
    function scrollToPc(pc) {
      const el = document.getElementById("pc-" + pc) || document.getElementById("line-" + pc);
      if (!el) return;
      document.querySelectorAll("tr.target").forEach(r => r.classList.remove("target"));
      el.classList.add("target");
      el.scrollIntoView({block: "center"});
      // remove flash class after the animation
      setTimeout(() => el.classList.remove("target"), 1100);
    }

    function copyToClipboard(text, el) {
      navigator.clipboard?.writeText(text);
      const old = el.textContent;
      el.textContent = "copied";
      setTimeout(() => { el.innerHTML = hi(text.replace(/^0x/,"")); }, 600);
    }

    function moveMatch(dir) {
      const rows = [...document.querySelectorAll("tr[id^='line-']")];
      if (!rows.length) return;
      state.matchIdx = (state.matchIdx + dir + rows.length) % rows.length;
      rows.forEach(r => r.classList.remove("focus"));
      const row = rows[state.matchIdx];
      row.classList.add("focus");
      row.scrollIntoView({block: "center"});
    }

    // ---- Toolbar wiring -----------------------------------------------------
    let searchTimer;
    $("search").addEventListener("input", (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.q = e.target.value.trim();
        state.matchIdx = 0;
        renderSidebars();
        renderTable();
        writeHash();
      }, 80);
    });

    $("comments").onclick = () => {
      state.comments = !state.comments;
      $("comments").classList.toggle("active", state.comments);
      renderTable();
    };
    $("labels").onclick = () => {
      state.labels = !state.labels;
      $("labels").classList.toggle("active", state.labels);
      renderTable();
    };
    $("reload").onclick = load;
    $("helpBtn").onclick = () => $("help").classList.toggle("show");

    // ---- Keyboard shortcuts -------------------------------------------------
    document.addEventListener("keydown", (e) => {
      const inField = e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA";
      if (e.key === "Escape") {
        if (inField && $("search").value) {
          $("search").value = "";
          state.q = "";
          renderSidebars();
          renderTable();
          writeHash();
          e.preventDefault();
        } else if ($("help").classList.contains("show")) {
          $("help").classList.remove("show");
        } else if (inField) {
          $("search").blur();
        }
        return;
      }
      if (inField) return;
      switch (e.key) {
        case "/": e.preventDefault(); $("search").focus(); $("search").select(); break;
        case "?": $("help").classList.toggle("show"); break;
        case "c": $("comments").click(); break;
        case "l": $("labels").click(); break;
        case "r": load(); break;
        case "n": moveMatch(1); break;
        case "N": moveMatch(-1); break;
        case "j": $("viewer").scrollBy({top:  $("viewer").clientHeight * 0.15}); break;
        case "k": $("viewer").scrollBy({top: -$("viewer").clientHeight * 0.15}); break;
        case "g": $("viewer").scrollTo({top: 0}); break;
        case "G": $("viewer").scrollTo({top: $("viewer").scrollHeight}); break;
        case "[":
          if (state.data && state.kernel > 0) { state.kernel--; renderAll(); }
          break;
        case "]":
          if (state.data && state.kernel < state.data.kernels.length - 1) { state.kernel++; renderAll(); }
          break;
      }
    });

    window.addEventListener("hashchange", () => { readHash(); renderAll(); });

    load();
  })();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
  def log_message(self, fmt: str, *args: Any) -> None:
    sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

  def send_json(self, value: Any, status: int = 200) -> None:
    body = json.dumps(value).encode()
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def do_GET(self) -> None:
    path = urlparse(self.path).path
    if path == "/api/firmware":
      try:
        self.send_json(firmware_json())
      except Exception as exc:
        self.send_json({"error": str(exc)}, status=500)
      return
    if path in {"/", "/index.html"}:
      body = INDEX_HTML.encode()
      self.send_response(200)
      self.send_header("Content-Type", "text/html; charset=utf-8")
      self.send_header("Content-Length", str(len(body)))
      self.end_headers()
      self.wfile.write(body)
      return
    self.send_error(404)


def find_port(host: str, start: int) -> int:
  for port in range(start, start + 100):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      try:
        sock.bind((host, port))
      except OSError:
        continue
      return port
  raise RuntimeError(f"no free port near {start}")


def main(argv: list[str] | None = None) -> int:
  argv = list(sys.argv[1:] if argv is None else argv)
  host = os.environ.get("FW_VIEW_HOST", DEFAULT_HOST)
  port = int(os.environ.get("FW_VIEW_PORT", argv[0] if argv else DEFAULT_PORT))
  port = find_port(host, port)
  server = ThreadingHTTPServer((host, port), Handler)
  url = f"http://{host}:{port}/"
  print(f"Blackhole firmware viewer: {url}")
  if os.environ.get("FW_VIEW_OPEN", "1") not in {"0", "false", "False"}:
    threading.Timer(0.35, lambda: webbrowser.open(url)).start()
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    print("\nShutting down.")
  finally:
    server.server_close()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
