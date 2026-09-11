import { describeOperation, isRegisterSetup } from '/behavior.mjs';
const $ = id => document.getElementById(id);
const h = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hex = (n, width = 8) => '0x' + (n >>> 0).toString(16).padStart(width, '0');
let catalog = [], docs = [], capture = null, currentImage = null, pending = null, matchIndex = -1, matches = [], selectedRow = null;
let revision = 0;
let visibleIndices = [];
$('show-setup').checked = localStorage.getItem('bh-viewer-show-setup') === 'true';
const theme = localStorage.getItem('bh-viewer-theme');
document.documentElement.classList.toggle('dark', theme ? theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches);
$('theme').onclick = () => { document.documentElement.classList.toggle('dark'); localStorage.setItem('bh-viewer-theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light'); };
async function api(url, signal) {
  const response = await fetch(url, {signal});
  const data = await response.json();
  if (!response.ok) throw Error(data.error || response.statusText);
  return data;
}
function status(text, error = false) { $('capture-status').classList.toggle('error', error); $('capture-status').textContent = text; }
function selection() { return new URLSearchParams(location.hash.slice(1)); }
function setHash(values, replace = false) {
  const params = new URLSearchParams(values);
  history[replace ? 'replaceState' : 'pushState'](null, '', '#' + params.toString());
}
function setOptions(element, entries, value) {
  element.replaceChildren(...entries.map(([v, label]) => new Option(label, v)));
  if (entries.some(([v]) => v === value)) element.value = value;
  element.disabled = entries.length === 0;
}
function showView(reference) {
  $('assembly').hidden = reference; $('reference').hidden = !reference;
  $('test-browser').hidden = reference; $('instruction-browser').hidden = !reference;
  $('reference-view').classList.toggle('active', reference); $('assembly-view').classList.toggle('active', !reference);
}
function selectTest(test, caseId) {
  const cases = catalog.filter(c => c.test === test);
  setOptions($('case'), cases.map(c => [c.id, c.case]), caseId);
  $('case-count').textContent = `${cases.length} ${cases.length === 1 ? 'case' : 'cases'}`;
  $('case-search').value = ''; renderCases(); renderTests();
}
async function collect(refresh = false) {
  const thisRevision = ++revision;
  status('Collecting pytest cases…'); $('refresh').disabled = true;
  try {
    const data = await api('/api/catalog');
    if (thisRevision !== revision) return;
    catalog = data.cases;
    const tests = [...new Set(catalog.map(c => c.test))];
    $('test-total').textContent = tests.length;
    const preferred = selection().get('case');
    const selected = catalog.find(c => c.id === preferred) || catalog.find(c => c.id.includes('test_sfpu_predication')) || catalog[0];
    setOptions($('test'), tests.map(test => [test, test.replace(/^tests\//, '').replace('.py::', ' / ')]), selected?.test);
    if (!selected) { status('No pytest cases found.'); $('listing').innerHTML = '<div class="empty">No tests to display.</div>'; return; }
    selectTest(selected.test, selected.id);
    await loadCase(selected.id, true, refresh);
    route();
  } catch (error) { status(error.message, true); $('listing').innerHTML = '<div class="empty">Could not collect tests. Use Refresh to try again.</div>'; }
  finally { $('refresh').disabled = false; }
}
async function loadCase(id, keepHash = false, refresh = false) {
  pending?.abort(); pending = new AbortController();
  const signal = pending.signal;
  const test = catalog.find(c => c.id === id);
  if (!test) return;
  capture = currentImage = null; selectedRow = null;
  matches = []; matchIndex = -1; $('find-count').textContent = '';
  $('find-prev').disabled = $('find-next').disabled = true;
  $('detail').hidden = true; $('kernels').replaceChildren(); $('download').disabled = true; $('image-meta').textContent = '';
  $('test-heading').textContent = test.test.split('::').pop();
  $('active-case').textContent = test.case;
  $('test-path').textContent = `${test.path}:${test.line}`;
  renderCases(); renderTests();
  $('parameters').innerHTML = Object.entries(test.params).map(([k,v]) => `<span><span class="key">${h(k)}</span> = ${h(v)}</span>`).join('');
  $('listing').innerHTML = '<div class="empty">Capturing emitted assembly…</div>';
  status('Building this exact case offline…');
  if (!keepHash) setHash({case: id});
  try {
    const data = await api('/api/case?id=' + encodeURIComponent(id) + (refresh ? '&refresh=1' : ''), signal);
    if (signal.aborted) return;
    capture = data.result;
    if (!capture) throw Error('The case did not produce a capture result.');
    const launched = new Set(capture.launches.flatMap(l => l.roles.map(r => r.image)));
    const images = capture.images;
    const roleCounts = {};
    const counts = {};
    images.forEach(image => { counts[image.role] = (counts[image.role] || 0) + 1; });
    $('kernels').replaceChildren(...images.map(image => {
      const button = document.createElement('button');
      roleCounts[image.role] = (roleCounts[image.role] || 0) + 1;
      button.textContent = image.role + (counts[image.role] > 1 ? ` · ${roleCounts[image.role]}` : '');
      const count = document.createElement('small'); count.textContent = `  ${image.rows.length}`; button.append(count);
      button.dataset.image = image.id; button.title = `${image.size} bytes · ${launched.has(image.id) ? 'submitted to launch' : 'generated, not submitted before capture stopped'}`;
      button.onclick = () => { showImage(image); setHash({case: id, image: image.id}); };
      return button;
    }));
    status(`${images.length} ${images.length === 1 ? 'image' : 'images'} · ${capture.launches.length} ${capture.launches.length === 1 ? 'launch' : 'launches'} captured. ${capture.boundary || (capture.status === 'complete' ? 'Host code generation completed.' : 'Capture did not complete.')}`, capture.errors.length > 0);
    const details = document.createElement('details');
    details.innerHTML = '<summary>Capture context</summary>';
    const text = document.createElement('div');
    text.textContent = `${data.context.board}; core index ${data.context.coreIndex}; ${data.context.dram}. Runtime register and memory values are shown as unknown. ` + (capture.launches.length ? `Launch parameters: ${capture.launches.map((l,i) => `${i+1}: ${l.params}`).join(' · ')}` : '');
    details.append(text);
    capture.errors.forEach(error => { const pre = document.createElement('pre'); pre.textContent = error; details.append(pre); });
    $('capture-status').append(details);
    const image = images.find(i => i.id === selection().get('image')) || images.find(i => i.role === 'trisc1' && launched.has(i.id)) || images[0];
    if (image) showImage(image);
    else $('listing').innerHTML = `<div class="empty">${capture.status === 'complete' ? 'This case emits no assembly.' : 'No kernel was emitted before capture stopped.'}</div>`;
  } catch (error) {
    if (error.name === 'AbortError') return;
    status(error.message, true); $('listing').innerHTML = '<div class="empty">Could not capture this case. Select another case or use Refresh to retry.</div>';
  }
}
function showImage(image) {
  currentImage = image; selectedRow = null; $('detail').hidden = true;
  document.querySelectorAll('#kernels button').forEach(b => b.classList.toggle('active', b.dataset.image === image.id));
  visibleIndices = image.rows.flatMap((row,index) => $('show-setup').checked || !isRegisterSetup(row) ? [index] : []);
  const hiddenCount = image.rows.length-visibleIndices.length;
  $('image-meta').textContent = `${visibleIndices.length} visible${hiddenCount ? ` · ${hiddenCount} setup instructions hidden` : ''} · ${image.size.toLocaleString()} bytes · base ${hex(image.base)} · SHA-256 ${image.sha256.slice(0,12)}`;
  $('download').disabled = false;
  $('listing').innerHTML = '<div class="asm-head"><span>Address</span><span>Operation</span></div>' + image.rows.map((row,index) => {
    const labels = row.labels.map(label => `<div class="asm-label">${h(label)}:</div>`).join('');
    if (!$('show-setup').checked && isRegisterSetup(row)) return labels;
    const display = describeOperation(row,docs,image);
    return labels + `<div id="pc-${row.pc}" data-index="${index}" class="asm-row ${h(row.kind)}" tabindex="0" role="button" aria-label="${h(hex(row.pc) + ' ' + display.plain)}"><span class="address">${hex(row.pc).slice(2)}</span><span class="behavior ${row.config ? 'config' : h(row.kind)}">${display.html}</span></div>`;
  }).join('');
  findMatches();
}
function argsHTML(args) {
  return args.map(a => `<div class="argument"><div class="argument-head"><span>${h(a.name)}</span><strong>${h(a.value)} <span class="dim">${hex(a.value,1)}</span></strong></div><span class="bits">bits ${a.hi}:${a.lo}</span>${a.label ? `<p>${h(a.label)}</p>` : ''}<p>${h(a.meaning || '')}</p></div>`).join('');
}
function selectRow(index) {
  if (!currentImage) return;
  const row = currentImage.rows[index]; if (!row) return;
  selectedRow = index;
  document.querySelectorAll('.asm-row.selected').forEach(e => e.classList.remove('selected'));
  $('pc-' + row.pc)?.classList.add('selected');
  const info = row.embedded || row;
  const doc = docs.find(d => d.name === info.doc);
  let body = `<div class="detail-header"><div><h2>${h(row.op)}</h2><span class="bits">${hex(row.pc)} · ${h(currentImage.role)} · ↑ ↓ to step</span></div><button id="close-detail" class="plain" aria-label="Close instruction details">×</button></div>`;
  body += `<pre class="raw-operands">${h(row.op)} ${h(row.operands)}</pre>`;
  if (doc) body += `<p class="detail-summary">${h(doc.summary)}</p>`;
  body += `<div class="raw-values">Emitted word &nbsp;${hex(row.word)}<br>Little endian &nbsp;${h(row.bytes)}${info.tensixWord === undefined ? '' : `<br>Tensix word &nbsp; ${hex(info.tensixWord)}`}<br>${h(row.encoding || (row.embedded ? 'Unrotated instruction written through MMIO' : 'RISC-V RV32'))}</div>`;
  if (row.address !== undefined && row.address !== null) body += `<div class="raw-values">Memory address ${hex(row.address)}${row.addressLabel ? `<br>${h(row.addressLabel)}` : ''}</div>`;
  if (info.args.length) body += '<h3>Every encoded operand</h3>' + argsHTML(info.args);
  else if (row.kind === 'riscv') {
    const entries = ['rd','rs1','rs2'].filter(k => row[k] !== undefined).map(k => `<div class="argument-head"><span>${k}</span><strong>x${row[k]} <span class="dim">(${['zero','ra','sp','gp','tp','t0','t1','t2','s0','s1','a0','a1','a2','a3','a4','a5','a6','a7','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','t3','t4','t5','t6'][row[k]]})</span></strong></div>`);
    if (row.imm !== undefined) entries.push(`<div class="argument-head"><span>immediate</span><strong>${row.imm} · ${hex(row.imm)}</strong></div>`);
    if (row.target !== undefined) entries.push(`<div class="argument-head"><span>target</span><strong>${hex(row.target)}</strong></div>`);
    if (row.csr !== undefined) entries.push(`<div class="argument-head"><span>CSR</span><strong>${hex(row.csr,3)}</strong></div>`);
    body += '<h3>Operands</h3>' + entries.join('');
  } else body += '<p class="note">No encoded operands.</p>';
  if (row.replayRecord) body += `<p class="note">${row.replayRecord.execute ? 'Recorded and executed' : 'Recorded only; not executed here'} in replay[${row.replayRecord.slot}].</p>`;
  const config = info.config || row.config;
  if (config) {
    body += `<h3>${h(config.group)}[${config.index}]</h3><p class="note">${h(config.operation || 'Configuration write')} · ${h(config.bank)} · ${h(config.source)}</p>`;
    body += config.fields.map(f => `<div class="argument"><div class="argument-head"><span>${h(f.name)}</span><strong>${f.value === null ? '?' : f.value}</strong></div><span class="bits">bits ${f.hi}:${f.lo}${f.partial ? ' · only masked bits known' : ''} · ${h(f.source)}</span>${f.unsupported ? '<p>Not implemented by ttsim.</p>' : ''}</div>`).join('');
    if (config.unknown) body += '<p class="note">This index is not described in the bundled ttsim register table.</p>';
  }
  if (doc?.notes.length) body += '<h3>Instruction notes</h3>' + doc.notes.map(n => `<p class="note">${h(n)}</p>`).join('');
  if (info.simArgs?.length) body += `<details><summary>ttsim field names</summary><p class="note">Raw extraction from ttsim’s table. These are shown separately because some widths and names differ from the encoder/manual.</p><div class="sim-fields">${info.simArgs.map(a => `${h(a.name)} = ${a.value} [${a.hi}:${a.lo}]`).join('<br>')}</div></details>`;
  if (row.source?.length) body += '<h3>Emitted from</h3>' + row.source.map(s => `<div class="source"><span>${h(s.path)}:${s.line}</span><pre>${h(s.text)}</pre></div>`).join('');
  if (doc) body += `<button id="open-doc" class="plain doc-link">Open ${h(doc.name)} reference ↗</button>`;
  $('detail').innerHTML = body; $('detail').hidden = false; $('detail').scrollTop = 0;
  $('close-detail').onclick = closeDetail;
  if ($('open-doc')) $('open-doc').onclick = () => openDoc(doc.name);
}
function closeDetail() { $('detail').hidden = true; if (selectedRow !== null) $('pc-' + currentImage.rows[selectedRow]?.pc)?.focus(); }
$('listing').addEventListener('click', event => {
  const target = event.target.closest('[data-target]');
  if (target) {
    event.stopPropagation();
    let dest = $('pc-' + target.dataset.target);
    if (!dest && currentImage.rows.some(row => row.pc === Number(target.dataset.target))) {
      $('show-setup').checked = true; localStorage.setItem('bh-viewer-show-setup','true');
      showImage(currentImage); dest = $('pc-' + target.dataset.target);
    }
    if (dest) { dest.scrollIntoView({block:'center'}); dest.focus(); selectRow(Number(dest.dataset.index)); }
    return;
  }
  const row = event.target.closest('[data-index]'); if (row) selectRow(Number(row.dataset.index));
});
$('listing').addEventListener('keydown', event => {
  if (event.target.matches('.asm-row') && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); selectRow(Number(event.target.dataset.index)); }
  if (event.target.matches('.asm-row') && ['ArrowDown','ArrowUp'].includes(event.key)) {
    event.preventDefault(); moveInstruction(Number(event.target.dataset.index), event.key === 'ArrowDown' ? 1 : -1);
  }
});
function moveInstruction(from, step) {
  if (!currentImage?.rows.length || !visibleIndices.length) return;
  const position = visibleIndices.indexOf(from);
  const index = visibleIndices[Math.max(0,Math.min(visibleIndices.length-1,position+step))];
  selectRow(index);
  const row = $('pc-' + currentImage.rows[index].pc);
  row?.focus({preventScroll:true}); row?.scrollIntoView({block:'nearest',inline:'nearest'});
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !$('detail').hidden) closeDetail();
  if (e.defaultPrevented || $('assembly').hidden || selectedRow === null || !['ArrowDown','ArrowUp'].includes(e.key)) return;
  if (e.target.closest('input,textarea,select,[contenteditable=true]')) return;
  if (e.target.closest('#detail') || e.target === document.body) {
    e.preventDefault(); moveInstruction(selectedRow,e.key === 'ArrowDown' ? 1 : -1);
  }
});
function findMatches() {
  const q = $('find').value.toLowerCase().trim(); matches = [];
  document.querySelectorAll('.asm-row').forEach(e => { const found = !!q && e.textContent.toLowerCase().includes(q); e.classList.toggle('match',found); e.classList.remove('current-match'); if (found) matches.push(e); });
  matchIndex = -1; $('find-count').textContent = q ? `${matches.length} found` : '';
  $('find-prev').disabled = $('find-next').disabled = matches.length === 0;
}
function nextMatch(step) {
  if (!matches.length) return;
  matches[matchIndex]?.classList.remove('current-match');
  matchIndex = matchIndex === -1 ? (step > 0 ? 0 : matches.length-1) : (matchIndex + step + matches.length) % matches.length;
  matches[matchIndex].classList.add('current-match'); matches[matchIndex].scrollIntoView({block:'center'});
  $('find-count').textContent = `${matchIndex+1}/${matches.length}`;
}
$('find').oninput = findMatches; $('find-next').onclick = () => nextMatch(1); $('find-prev').onclick = () => nextMatch(-1);
$('find').onkeydown = e => { if (e.key === 'Enter') nextMatch(e.shiftKey ? -1 : 1); };
$('download').onclick = () => {
  if (!currentImage) return;
  const lines = [`# ${capture.id}`, `# ${currentImage.role}; base ${hex(currentImage.base)}; SHA-256 ${currentImage.sha256}`, `# ${capture.boundary || capture.status}`, '# Annotated disassembly (Tensix operand syntax is descriptive).', ''];
  currentImage.rows.forEach(row => { lines.push(...row.labels.map(l => l+':')); lines.push(`${hex(row.pc)}  ${hex(row.word)}  ${row.op} ${row.operands}`); row.annotations.forEach(a => lines.push('    # '+a)); });
  const url = URL.createObjectURL(new Blob([lines.join('\n')+'\n'],{type:'text/plain'}));
  const link = document.createElement('a'); link.href = url; link.download = `${capture.id.split('::').pop().replace(/[^a-zA-Z0-9_-]/g,'_')}-${currentImage.role}.s`; link.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
};
function openDoc(name, keepHash = false) {
  const doc = docs.find(d => d.name === name) || docs[0]; if (!doc) return;
  showView(true); $('instruction-select').value = doc.name; renderInstructions();
  $('instruction-article').innerHTML = `<span class="dim">${h(doc.group)} · ${h(doc.manualArch)}</span><h1>${h(doc.name)}</h1><h2>${h(doc.title)}</h2><p>${h(doc.summary)}</p><h2>Arguments</h2>${doc.args.length ? doc.args.map(a => `<div class="argument"><div class="argument-head"><span>${h(a.name)}</span><span>bits ${a.hi}:${a.lo} · default ${h(a.default)}</span></div><p>${h(a.meaning)}</p></div>`).join('') : '<p>No arguments.</p>'}<h2>Notes</h2>${doc.notes.map(n => `<p>${h(n)}</p>`).join('')}${doc.constants.length ? `<h2>Named constants</h2><pre class="sim-fields">${h(doc.constants.join('\n'))}</pre>` : ''}<p class="note">${h(doc.evidence)}</p><a href="${h(doc.manualUrl)}" target="_blank" rel="noreferrer">Open the pinned ISA manual ↗</a>`;
  if (!keepHash) setHash({case:$('case').value,doc:doc.name});
  document.title = `${doc.name} · Blackhole`;
}
function route() {
  const params = selection();
  if (params.has('doc')) { openDoc(params.get('doc'),true); return; }
  showView(false); document.title = 'Blackhole · Test assembly';
  const id = params.get('case');
  if (id && id !== $('case').value && catalog.some(c => c.id === id)) {
    const item = catalog.find(c => c.id === id); $('test').value = item.test; selectTest(item.test,id); loadCase(id,true);
  } else if (capture && params.has('image')) {
    const image = capture.images.find(i => i.id === params.get('image')); if (image && image !== currentImage) showImage(image);
  }
}
$('test').onchange = () => { selectTest($('test').value); loadCase($('case').value); };
$('case').onchange = () => loadCase($('case').value);
$('refresh').onclick = () => collect(true);
$('instruction-select').onchange = () => openDoc($('instruction-select').value);
$('reference-view').onclick = () => openDoc($('instruction-select').value);
$('assembly-view').onclick = () => { showView(false); setHash({case:$('case').value,...(currentImage ? {image:currentImage.id} : {})}); document.title = 'Blackhole · Test assembly'; };
window.addEventListener('popstate', route);
window.addEventListener('hashchange', route);
Promise.all([api('/api/reference').then(data => { docs = data.instructions; $('doc-count').textContent = docs.length; setOptions($('instruction-select'),docs.map(d => [d.name,`${d.name} — ${d.title}`])); renderInstructions(); }),collect()]).then(route).catch(error => status(error.message,true));

function renderTests() {
  const tokens = $('test-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const groups = new Map();
  for (const item of catalog) {
    if (!groups.has(item.test)) groups.set(item.test, []);
    groups.get(item.test).push(item);
  }
  let previousFile = '';
  const html = [];
  for (const [test,cases] of groups) {
    const haystack = test + ' ' + cases.map(c => c.case + ' ' + JSON.stringify(c.params)).join(' ');
    if (!tokens.every(t => haystack.toLowerCase().includes(t))) continue;
    const file = cases[0].path.replace(/^tests\//,'').replace(/\.py$/,'');
    if (file !== previousFile) { html.push(`<div class="test-group">${h(file)}</div>`); previousFile = file; }
    const active = test === $('test').value;
    html.push(`<button class="test-item ${active ? 'active' : ''}" data-test="${h(test)}" ${active ? 'aria-current="true"' : ''}><span>${h(test.split('::').pop().replace(/^test_/,''))}</span><small>${cases.length}</small></button>`);
  }
  $('test-list').innerHTML = html.join('') || '<p class="note">No matching tests.</p>';
}
function renderCases() {
  const tokens = $('case-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const cases = catalog.filter(c => c.test === $('test').value && tokens.every(t => (c.case + ' ' + JSON.stringify(c.params)).toLowerCase().includes(t)));
  $('case-list').innerHTML = cases.map(c => `<button class="case-item ${c.id === $('case').value ? 'active' : ''}" data-case="${h(c.id)}" ${c.id === $('case').value ? 'aria-current="true"' : ''}>${h(c.case)}</button>`).join('') || '<p class="note">No matching cases.</p>';
}
$('test-search').oninput = renderTests; $('case-search').oninput = renderCases;
$('test-list').onclick = e => {
  const button = e.target.closest('[data-test]'); if (!button) return;
  $('test').value = button.dataset.test; selectTest(button.dataset.test); showView(false); loadCase($('case').value);
};
$('case-list').onclick = e => {
  const button = e.target.closest('[data-case]'); if (!button) return;
  $('case').value = button.dataset.case; renderCases(); loadCase(button.dataset.case);
};
for (const id of ['test-search','case-search']) $(id).onkeydown = e => {
  if (e.key === 'Enter' || e.key === 'ArrowDown') { e.preventDefault(); $(id === 'test-search' ? 'test-list' : 'case-list').querySelector('button')?.focus(); }
};
for (const id of ['test-list','case-list']) $(id).onkeydown = e => {
  const buttons = [...$(id).querySelectorAll('button')]; const index = buttons.indexOf(document.activeElement);
  if (index >= 0 && ['ArrowDown','ArrowUp'].includes(e.key)) { e.preventDefault(); buttons[Math.max(0,Math.min(buttons.length-1,index+(e.key === 'ArrowDown' ? 1 : -1)))]?.focus(); }
};

function renderInstructions() {
  const tokens = $('instruction-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const groups = ['SFPU','FPU','Unpack / pack','Addressing','Control'];
  $('instruction-list').innerHTML = groups.map(group => {
    const found = docs.filter(d => d.group === group && tokens.every(t => (d.name + ' ' + d.title + ' ' + d.summary + ' ' + d.args.map(a => a.meaning).join(' ')).toLowerCase().includes(t)));
    if (!found.length) return '';
    return `<div class="test-group">${h(group)}</div>` + found.map(d => `<button class="instruction-item ${$('instruction-select').value === d.name ? 'active' : ''}" data-doc="${h(d.name)}"><span>${h(d.name)}</span><small>${h(d.title)}</small></button>`).join('');
  }).join('') || '<p class="note">No matching instructions.</p>';
}
$('instruction-search').oninput = renderInstructions;
$('instruction-list').onclick = e => { const button = e.target.closest('[data-doc]'); if (button) openDoc(button.dataset.doc); };
$('instruction-search').onkeydown = e => { if (e.key === 'Enter' || e.key === 'ArrowDown') { e.preventDefault(); $('instruction-list').querySelector('button')?.focus(); } };
$('instruction-list').onkeydown = e => {
  const buttons = [...$('instruction-list').querySelectorAll('button')]; const index = buttons.indexOf(document.activeElement);
  if (index >= 0 && ['ArrowDown','ArrowUp'].includes(e.key)) { e.preventDefault(); buttons[Math.max(0,Math.min(buttons.length-1,index+(e.key === 'ArrowDown' ? 1 : -1)))]?.focus(); }
};

$('show-setup').onchange = () => {
  localStorage.setItem('bh-viewer-show-setup',String($('show-setup').checked));
  if (!currentImage) return;
  const previous = selectedRow;
  showImage(currentImage);
  if (previous !== null && visibleIndices.length) {
    const next = visibleIndices.includes(previous) ? previous : visibleIndices.find(i => i > previous) ?? visibleIndices.at(-1);
    selectRow(next);
    $('pc-' + currentImage.rows[next].pc)?.scrollIntoView({block:'nearest',inline:'nearest'});
  }
};
