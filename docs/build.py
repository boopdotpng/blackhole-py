#!/usr/bin/env python3
# Builds docs/index.html: every Tensix instruction, config field and enum in hw/*.py, described by docs/notes.toml.
import dataclasses, html, re, sys, tomllib
from pathlib import Path
DOCS = Path(__file__).resolve().parent
sys.path.insert(0, str(DOCS.parent))
from hw import cfg, isa, sfpu_lat

N = tomllib.loads((DOCS / "notes.toml").read_text())
used: set[tuple] = set()
def warn(msg): print(f"build.py: {msg}", file=sys.stderr)
def get(*path, default=None):
  d = N
  for p in path:
    if not isinstance(d, dict) or p not in d: return default
    d = d[p]
  used.add(path)
  return d

def inl(t:str) -> str: return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(t))
def md(s:str) -> str:  # paragraphs, "- " lists, ``` blocks, `code`
  out = []
  for p in s.strip().split("\n\n"):
    if p.startswith("```"): out.append("<pre>" + html.escape("\n".join(p.split("\n")[1:-1])) + "</pre>")
    elif p.startswith("- "): out.append("<ul>" + "".join(f"<li>{inl(l[2:])}</li>" for l in re.split(r"\n(?=- )", p)) + "</ul>")
    elif p: out.append(f"<p>{inl(p)}</p>")
  return "".join(out)
def table(cols, rows, cls=""):
  return (f"<table class='{cls}'><thead><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead><tbody>" +
          "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table>")
def code(s) -> str: return f"<code>{html.escape(str(s))}</code>"
def slug(s:str) -> str: return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

class Entry:
  def __init__(self, title, body, meta=""): self.title, self.body, self.meta, self.id = title, body, meta, ""

# ---- Tensix ----

GROUPS = {"control": "Control", "config": "Configuration", "scalar": "Scalar unit", "ADC": "Address counters",
          "unpack/pack": "Unpack / pack / mover", "FPU": "FPU", "SFPU": "SFPU"}
def tensix_entries() -> dict[str, list[Entry]]:
  out: dict[str, list[Entry]] = {g: [] for g in GROUPS}
  for g in GROUPS:
    if notes := get("groups", g): out[g].append(Entry(f"{GROUPS[g]} overview", md("\n\n".join(f"- {n}" for n in notes).replace("\n\n- ", "\n- "))))
  for op in sorted(isa.TensixOp, key=lambda o: o.value):
    cls, e = isa.TENSIX[op], get("tensix", op.name) or {}
    if not e.get("desc"): warn(f"tensix {op.name}: no description")
    if (g := e.get("group")) not in GROUPS: warn(f"tensix {op.name}: unknown group {g!r}"); continue
    base = (get("tensix", e["fields_as"]) or {}).get("fields", {}) if "fields_as" in e else {}
    descs = base | e.get("fields", {})
    meta = [f"opcode 0x{op.value:02X}", GROUPS[g]]
    if "lat" in e: meta.append(f"latency {e['lat']}")
    if (d := sfpu_lat.sfpu_decode(int(isa.TENSIX[op](op)))) is not None: meta.append(f"latency {d.lat}{' (+1 issue)' if d.block else ''}, {d.unit} unit")
    fields = [f for f in cls._fields if f.name != "op"]
    for k in e.get("fields", {}):
      if k not in {f.name for f in fields}: warn(f"notes.toml tensix {op.name} field {k!r} matches nothing")
    body = md(e.get("desc", "")) + md(e.get("notes", ""))
    if "regs" in e: body += "<h4>Register usage</h4><ul class=regs>" + "".join(f"<li>{inl(l)}</li>" for l in e["regs"].split("\n")) + "</ul>"
    if fields:
      body += "<h4>Arguments</h4>" + table(["name", "bits", "type", "description"], [
        (code(f.name), code(f"{f.hi}:{f.lo}" if f.hi != f.lo else f.hi), code(f.enum.__name__) if f.enum else "int", md(descs.get(f.name, "")))
        for f in fields], "args")
    else: body += "<p class=mute>No arguments.</p>"
    out[g].append(Entry(op.name, body, " · ".join(meta)))
  return out

# ---- config ----

LETTER = {"addr_mod": "s", "pack_addr_mod": "s", "edge_mask": "s", "row_set_mapping": "s", "face_set_mapping": "s", "UNPACK": "i",
          "unpack_ctx_offset": "i", "unpack_ctx_reset": "i", "unpack_ctx_inc": "i", "scratch": "i"}
BLOCKS = ("THREAD", "ADDR_MOD", "PACK_ADDR_MOD", "MATH", "UNPACK", "PACK", "GLOBAL", "MOVER")
def cfg_fields() -> dict[str, list]:
  seen, out = set(), {}
  def walk(o, p):
    if isinstance(o, cfg.Field):
      if o not in seen: seen.add(o); out.setdefault(re.sub(r"(\w+)\[\d+\]", lambda m: f"{m[1]}[{LETTER.get(m[1], 'c')}]", p), []).append(o)
    elif isinstance(o, tuple): [walk(x, f"{p}[{i}]") for i, x in enumerate(o)]
    elif dataclasses.is_dataclass(o): [walk(getattr(o, f.name), f"{p}.{f.name}") for f in dataclasses.fields(o) if f.name != "words"]
  for n in ("THREAD", "MATH", "UNPACK", "PACK", "GLOBAL", "MOVER"): walk(getattr(cfg, n), n)
  return out
def span(xs):
  xs = list(dict.fromkeys(xs))
  return " / ".join(xs) if len(xs) <= 4 else f"{xs[0]} … {xs[-1]}"
def config_entries() -> list[Entry]:
  rows: dict[str, list] = {b: [] for b in BLOCKS}
  for path, fs in cfg_fields().items():
    if (desc := get("cfg", path)) is None: warn(f"cfg {path}: no description")
    block, name = ("ADDR_MOD", path[len("THREAD.addr_mod[s]."):]) if path.startswith("THREAD.addr_mod[") else \
                  ("PACK_ADDR_MOD", path[len("THREAD.pack_addr_mod[s]."):]) if path.startswith("THREAD.pack_addr_mod[") else \
                  (path.split(".")[0].split("[")[0], path.split(".", 1)[1] if "." in path else path)
    space = "T" if fs[0].space is cfg.Space.THREAD else "C"
    rows[block].append((code(name), f"{space} " + span(str(f.word) for f in fs), code(span(f"{f.shift + f.width - 1}:{f.shift}" if f.width > 1 else str(f.shift) for f in fs)), md(desc or "")))
  out = [Entry("Config overview", md(get("cfg_blocks", "_") or ""))]
  for b in BLOCKS:
    out.append(Entry(b, md(get("cfg_blocks", b) or "") + table(["field", "word", "bits", "description"], rows[b], "args"), f"cfg.{b} · {len(rows[b])} fields"))
  return out

# ---- enums, baby cores, left out ----

def enum_entries() -> list[Entry]:
  out = []
  for e in (isa.Stall, isa.Wait, isa.SemWait, isa.Adc, isa.LReg, isa.SfpuFormat, isa.LoadImm, isa.Broadcast, cfg.DataFormat):
    rows = []
    for m in [m for n, m in e.__members__.items() if n == m.name]:
      aliases = [a for a, v in e.__members__.items() if v is m and a != m.name]
      if (desc := get("enum", e.__name__, m.name)) is None: warn(f"enum {e.__name__}.{m.name}: no description")
      rows.append((code(m.name) + "".join(f" = {code(a)}" for a in aliases), code(int(m)), md(desc or "")))
    out.append(Entry(e.__name__, md(get("enum", e.__name__, "_") or "") + table(["member", "value", "description"], rows, "args"),
                     f"{'hw.cfg' if e is cfg.DataFormat else 'hw.isa'}.{e.__name__}"))
  return out

def other_entries() -> dict[str, list[Entry]]:
  baby = Entry("Baby RISC-V cores", table(["", ""], [(f"<b>{inl(r['what'])}</b>", md(r["fact"])) for r in get("baby_riscv")], "args facts"))
  t = table(["instructions (opcode)", "why"], [(inl(r["names"]), md(r["why"])) for r in get("left_out", "tensix")], "args")
  c = table(["field", "where", "status", "finding"], [(code(r["field"]), code(r["where"]), inl(r["status"]), md(r["finding"])) for r in get("left_out", "cfg")], "args")
  return {"Baby RISC-V": [baby], "Left out": [Entry("Tensix instructions", t), Entry("Config fields", c)]}

# ---- page ----

CSS = """
:root{--bg:#fff;--fg:#1f2328;--mute:#656d76;--line:#d8dee4;--soft:#f6f8fa;--code:#eff1f3;--acc:#0969da;--side:#f6f8fa}
[data-theme=dark]{--bg:#0d1117;--fg:#d1d7e0;--mute:#8d96a0;--line:#2a313c;--soft:#151b23;--code:#1f2630;--acc:#4493f8;--side:#10151c}
*{box-sizing:border-box}html{scroll-padding-top:16px}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}
code{background:var(--code);padding:1px 4px;border-radius:4px}pre{background:var(--code);padding:10px 12px;border-radius:6px;overflow:auto}
pre code{background:none;padding:0}a{color:var(--acc);text-decoration:none}
nav{position:fixed;top:0;left:0;bottom:0;width:280px;overflow-y:auto;background:var(--side);border-right:1px solid var(--line);padding:14px 12px 40px;font-size:14px}
nav .top{display:flex;gap:8px;align-items:center;margin-bottom:10px}nav .top b{font-size:16px;flex:1}
nav input{width:100%;padding:6px 9px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit;margin-bottom:8px}
nav button{border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:6px;padding:3px 8px;cursor:pointer;font:inherit}
nav h5{margin:16px 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
nav details{margin:0}nav summary{cursor:pointer;padding:2px 4px;border-radius:4px;font-weight:600}nav summary:hover{background:var(--code)}
nav ul{list-style:none;margin:2px 0 6px;padding:0 0 0 10px;border-left:1px solid var(--line)}
nav li a{display:block;padding:1px 8px;color:var(--fg);border-radius:4px;font-family:ui-monospace,Menlo,monospace;font-size:12.5px}
nav li a:hover{background:var(--code)}nav li a.on{background:var(--acc);color:#fff}
main{margin-left:280px;padding:24px 40px 80px}main>div{max-width:900px}
h2{font-size:26px;margin:48px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}h2:first-child{margin-top:0}
h3{font-size:20px;margin:36px 0 2px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
h4{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);margin:18px 0 6px}
.meta{color:var(--mute);font-size:13px;margin-bottom:10px}.mute{color:var(--mute)}
section{padding-bottom:8px;border-bottom:1px solid var(--line)}
table{border-collapse:collapse;width:100%;margin:6px 0 12px;font-size:14px}
th{text-align:left;font-weight:600;padding:6px 10px;border-bottom:2px solid var(--line);background:var(--soft)}
td{padding:6px 10px;border-bottom:1px solid var(--line);vertical-align:top}td p{margin:0 0 4px}td p:last-child{margin:0}
.args td:first-child{white-space:nowrap}.args td:nth-child(2),.args td:nth-child(3){white-space:nowrap}
.facts td:first-child{width:180px;white-space:normal}td ul,.regs{margin:2px 0;padding-left:20px}.regs{font-size:13.5px}
#menu{display:none}
@media (max-width:800px){nav{position:static;width:auto;max-height:none;border-right:0;border-bottom:1px solid var(--line)}
nav.closed .groups{display:none}#menu{display:inline-block}main{margin-left:0;padding:16px}h3{font-size:18px}}
"""
JS = """
const de=document.documentElement,q=document.getElementById('q'),secs=[...document.querySelectorAll('main section')];
document.getElementById('t').onclick=()=>{de.dataset.theme=de.dataset.theme==='dark'?'light':'dark';localStorage.theme=de.dataset.theme};
document.getElementById('menu').onclick=()=>document.querySelector('nav').classList.toggle('closed');
q.oninput=()=>{const s=q.value.toLowerCase();
 for(const x of secs){const hit=!s||x.textContent.toLowerCase().includes(s);x.hidden=!hit;
  const a=document.querySelector(`nav a[href="#${x.id}"]`);if(a)a.parentElement.hidden=!hit}
 for(const d of document.querySelectorAll('nav details')){const any=[...d.querySelectorAll('li')].some(l=>!l.hidden);d.hidden=!any;if(s)d.open=any}};
const links=new Map([...document.querySelectorAll('nav li a')].map(a=>[a.getAttribute('href').slice(1),a]));let cur;
const io=new IntersectionObserver(es=>{for(const e of es){const a=links.get(e.target.id);if(!e.isIntersecting||!a||a===cur)continue;
 cur&&cur.classList.remove('on');a.classList.add('on');cur=a;a.closest('details').open=true;a.scrollIntoView({block:'nearest'})}},{rootMargin:'0px 0px -80% 0px'});
secs.forEach(s=>io.observe(s));
"""
HEAD = "<script>document.documentElement.dataset.theme=localStorage.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')</script>"

def build():
  parts = [("Overview", {"About": [Entry("About these docs", md("\n".join(f"- {n}" for n in get("about", "notes"))))]}),
           ("Tensix instructions", {GROUPS[g]: es for g, es in tensix_entries().items()}),
           ("Config registers", {"Config": config_entries()}), ("Enums", {"Enums": enum_entries()}), ("Other", other_entries())]
  nav, main, ids = [], [], set()
  for part, groups in parts:
    nav.append(f"<h5>{part}</h5>"); main.append(f"<h2>{part}</h2>")
    for g, entries in groups.items():
      items = []
      for e in entries:
        e.id = slug(e.title) if slug(e.title) not in ids else slug(f"{g} {e.title}")
        ids.add(e.id)
        items.append(f"<li><a href=#{e.id}>{html.escape(e.title)}</a></li>")
        main.append(f"<section id={e.id}><h3>{html.escape(e.title)}</h3>" + (f"<div class=meta>{html.escape(e.meta)}</div>" if e.meta else "") + e.body + "</section>")
      nav.append(f"<details{' open' if part == 'Overview' else ''}><summary>{html.escape(g)}</summary><ul>{''.join(items)}</ul></details>")
  page = (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
          f"<title>blackhole-py docs</title>{HEAD}<style>{CSS}</style></head><body><nav class=closed><div class=top><b>blackhole-py</b>"
          f"<button id=menu>☰</button><button id=t title='light / dark'>◐</button></div><div class=groups><input id=q placeholder='Filter…'>"
          f"{''.join(nav)}</div></nav><main><div>{''.join(main)}</div></main><script>{JS}</script></body></html>")
  (DOCS / "index.html").write_text(page)
  for sec in ("tensix", "cfg", "groups", "cfg_blocks"):
    for k in N.get(sec, {}):
      if (sec, k) not in used and not (sec == "cfg_blocks" and k == "_"): warn(f"notes.toml [{sec}] {k!r} matches nothing")
  for e, ms in N.get("enum", {}).items():
    for m in ms:
      if m != "_" and ("enum", e, m) not in used: warn(f"notes.toml [enum.{e}] {m!r} matches nothing")

if __name__ == "__main__": build()
