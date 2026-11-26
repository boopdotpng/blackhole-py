// Sidebar, filter and keyboard navigation for index.html.
const $ = s => document.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const de = document.documentElement, q = $('#q'), toc = $('#toc'), count = $('#count');
$('#theme').onclick = () => { de.dataset.theme = de.dataset.theme === 'dark' ? 'light' : 'dark'; localStorage.theme = de.dataset.theme; };
$('#menu').onclick = () => $('nav').classList.toggle('closed');

// minimal highlighting for <pre><code class=py>: keywords and # comments
const KW = /\b(for|in|if|elif|else|while|return|def|and|or|not|range|None|True|False|break|continue)\b/g;
for (const c of $$('pre code.py'))
  c.innerHTML = c.innerHTML.split('\n').map(l => {
    const i = l.indexOf('#'), [a, b] = i < 0 ? [l, ''] : [l.slice(0, i), l.slice(i)];
    return a.replace(KW, '<span class=k>$1</span>') + (b && `<span class=c>${b}</span>`);
  }).join('\n');

// build the sidebar: part heading, group (collapsible when a part has several), one link per section
const items = [];
for (const part of $$('main .part')) {
  const h = document.createElement('h5'); h.textContent = part.dataset.title; toc.append(h); part._h = h;
  const groups = $$(':scope>.group', part);
  for (const g of groups) {
    const ul = document.createElement('ul');
    for (const s of $$(':scope>section', g)) {
      const h3 = s.querySelector('h3'), name = h3.textContent, a = document.createElement('a');
      a.href = '#' + s.id; a.append(Object.assign(document.createElement('span'), { textContent: name }));
      if (s.dataset.op) a.append(Object.assign(document.createElement('small'), { textContent: s.dataset.op }));
      h3.innerHTML = `<a class=anchor href="#${s.id}">${h3.innerHTML}</a>`;
      const li = document.createElement('li'); li.append(a); ul.append(li);
      items.push({ s, a, li, key: `${name} ${s.dataset.op || ''} ${s.dataset.kw || ''}`.toLowerCase(), text: null });
    }
    if (groups.length > 1) {
      const d = document.createElement('details'), su = document.createElement('summary');
      su.textContent = g.dataset.title; d.append(su, ul); d.open = true; toc.append(d); g._d = d;
    } else toc.append(ul);
  }
}

// filter: every word must appear. Name / opcode / keyword hits come first, full-text hits after them (dimmed).
let vis = items, sel = -1, cur = null;
function filter() {
  const words = q.value.toLowerCase().trim().split(/\s+/).filter(Boolean), name = [], text = [];
  for (const it of items) {
    let m = !words.length || words.every(w => it.key.includes(w)) ? 2 : 0;
    if (!m && words.every(w => (it.text ??= it.s.textContent.toLowerCase()).includes(w))) m = 1;
    it.li.hidden = it.s.hidden = !m;
    it.a.classList.toggle('text', m === 1);
    (m === 2 ? name : m === 1 ? text : []).push(it);
  }
  vis = [...name, ...text];
  for (const g of $$('main .group')) { g.hidden = $$(':scope>section', g).every(s => s.hidden); if (g._d) g._d.hidden = g.hidden; }
  for (const p of $$('main .part')) { p.hidden = $$('section', p).every(s => s.hidden); p._h.hidden = p.hidden; }
  count.textContent = words.length ? ` · ${vis.length} match${vis.length === 1 ? '' : 'es'}` : '';
  select(words.length && vis.length ? 0 : -1);
}
function select(i) {
  items.forEach(it => it.a.classList.remove('sel')); sel = i;
  if (i >= 0) vis[i].a.classList.add('sel'), vis[i].a.scrollIntoView({ block: 'nearest' });
}
function go(it) { it.s.scrollIntoView(); history.replaceState(null, '', '#' + it.s.id); }
function focusFilter() { q.focus(); q.select(); $('nav').classList.remove('closed'); }

q.oninput = filter;
q.onkeydown = e => {
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault(); if (!vis.length) return;
    select(((sel < 0 ? -1 : sel) + (e.key === 'ArrowDown' ? 1 : -1) + vis.length) % vis.length); go(vis[sel]);
  } else if (e.key === 'Enter') { if (vis.length) go(vis[Math.max(sel, 0)]), q.blur(); }
  else if (e.key === 'Escape') {  // clear, and stay on the section you were reading
    const keep = cur; q.value = ''; filter(); q.blur(); if (keep) keep.s.scrollIntoView();
  }
};
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); focusFilter(); return; }
  if (e.target === q || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === '/') { e.preventDefault(); focusFilter(); }
  else if (e.key === 'j' || e.key === 'k') {
    const shown = items.filter(it => !it.s.hidden), i = shown.indexOf(cur);
    const n = shown[Math.min(shown.length - 1, Math.max(0, i + (e.key === 'j' ? 1 : -1)))]; if (n) go(n);
  } else if (e.key === 'Escape' && q.value) { const keep = cur; q.value = ''; filter(); if (keep) keep.s.scrollIntoView(); }
});

// highlight the section at the top of the viewport
const byId = new Map(items.map(it => [it.s.id, it]));
const io = new IntersectionObserver(es => {
  for (const e of es) {
    const it = byId.get(e.target.id);
    if (!e.isIntersecting || !it || it === cur) continue;
    cur?.a.classList.remove('on'); it.a.classList.add('on'); cur = it; it.a.scrollIntoView({ block: 'nearest' });
  }
}, { rootMargin: '0px 0px -85% 0px' });
items.forEach(it => io.observe(it.s));
if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
