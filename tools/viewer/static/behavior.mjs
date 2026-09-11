const h = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hex = (n, width = 8) => '0x' + (n >>> 0).toString(16).padStart(width, '0');

function mopSlot(address) {
  if (address === null || address === undefined || address < 0xffb80000 || address > 0xffb80020 || address % 4) return null;
  return (address - 0xffb80000) / 4;
}
const mopRoles = [
  'loop template: outer count',
  'loop template: inner count · mask template: flags',
  'loop template: StartOp · mask template: InsnB',
  'loop template: EndOp0 · mask template: InsnA0',
  'loop template: EndOp1 · mask template: InsnA1',
  'loop template: LoopOp · mask template: InsnA2',
  'loop template: LoopOp1 · mask template: InsnA3',
  'loop template: Loop0Last · mask template: SkipA0',
  'loop template: Loop1Last · mask template: SkipB',
];
function nextRegisterUse(row, image) {
  const index = image?.rows.indexOf(row) ?? -1;
  if (index < 0 || !row.rd) return null;
  // Remain within a straight-line block and stop at the first read or rewrite.
  for (let i=index+1; i<image.rows.length; i++) {
    const candidate=image.rows[i];
    if (candidate.labels?.length || candidate.branch || candidate.jump || candidate.kind === 'unknown') return null;
    if (candidate.rs1 === row.rd || candidate.rs2 === row.rd) return candidate;
    if (candidate.rd === row.rd) return null;
  }
  return null;
}

export function describeOperation(row, docs, currentImage) {
  const info = row.embedded || row;
  const values = Object.fromEntries((info.args || []).map(a => [a.name,a.value]));
  const labels = Object.fromEntries((info.args || []).map(a => [a.name,a.label || '']));
  const config = info.config || row.config;
  const doc = docs.find(d => d.name === info.doc);
  const a = values;
  const reg = n => `L${n}`;
  const arg = (name) => labels[name] || String(a[name]);
  const result = (title, support = '') => ({plain:title + ' ' + support, html:`<span class="behavior-title">${h(title)}</span>${support ? `<div class="behavior-support">${h(support)}</div>` : ''}`});
  if (row.replayRecord) {
    const nested = describeOperation({...row,replayRecord:null},docs,currentImage);
    const action = row.replayRecord.execute ? 'Record and execute' : 'Record only';
    return {plain:`${action} replay[${row.replayRecord.slot}]: ${nested.plain}`,
      html:`<div class="behavior-support">${h(action)} → replay[${row.replayRecord.slot}]${row.replayRecord.execute ? '' : ' · not executed here'}</div>${nested.html}`};
  }
  if ((!row.embedded || mopSlot(row.address) === null) && (info.op === 'RDCFG' || info.op === 'WRCFG')) {
    const count = info.op === 'WRCFG' && a.wr128b ? 4 : 1;
    const index = count === 4 ? a.CfgReg & ~3 : a.CfgReg;
    const gprIndex = count === 4 ? a.GprAddress & ~3 : a.GprAddress;
    const suffix = count === 4 ? `…${index+3}` : '';
    const gpr = `TensixGPR[${gprIndex}${count === 4 ? `…${gprIndex+3}` : ''}]`;
    const cfg = `config[${index}${suffix}]`;
    return result(info.op === 'RDCFG' ? `${gpr} ← ${cfg}` : `${cfg} ← ${gpr}`,
      `current thread StateID · ${count*32}-bit ${info.op === 'RDCFG' ? 'configuration read' : 'configuration write'}${count === 4 ? '; source and destination aligned to four words' : ''}`);
  }
  if (config && !(row.memory === 'write' && mopSlot(row.address) !== null)) {
    const masked = config.mask !== null && config.mask !== 0xffffffff;
    const prefix = config.group === 'thread_cfg' ? 'thread' : 'config';
    const fields = config.fields.map(f => `${prefix}.${f.name}${f.partial ? ' [masked bits]' : ''} ← ${f.value === null ? 'runtime value' : f.value}`);
    const title = fields.length ? fields.join('\n') : `${prefix}[${config.index}] ← ${config.value === null ? 'runtime value' : hex(config.value)}`;
    const context = `${config.bank} · ${masked ? 'masked update; other bits preserved' : config.operation || 'configuration write'}`;
    return {plain:title+' '+context,html:title.split('\n').map(line => `<span class="assignment">${h(line)}</span>`).join('')+`<div class="behavior-support">${h(context)}</div>`};
  }
  const slot = mopSlot(row.address);
  if (row.memory === 'write' && slot !== null) {
    const stored = row.embedded;
    if (stored) {
      const nested = describeOperation({...stored,annotations:[]},docs,currentImage);
      const title = `MOP[${slot}] ← ${stored.op}`;
      const note = stored.op === 'NOP' ? 'Save a no-op for later MOP expansion; nothing executes here.' : 'Save this instruction for later MOP expansion; nothing executes here.';
      return {plain:title+' '+mopRoles[slot]+' '+note+' '+nested.plain,
        html:`<span class="behavior-title">${h(title)}</span><div class="behavior-support">${h(mopRoles[slot])}</div><div class="behavior-support">${h(note)}</div>${stored.op === 'NOP' ? '' : `<div class="stored-operation">${nested.html}</div>`}`};
    }
    const value = row.annotations.find(a => a.startsWith('write '))?.slice(6) || `x${row.rs2}`;
    return result(`MOP[${slot}] ← ${value}`,`${mopRoles[slot]} · configure for later expansion`);
  }
  if (row.embedded) {
    const nested = describeOperation({...row.embedded,annotations:[]},docs,currentImage);
    return {plain:'Issue through MMIO: '+nested.plain,html:`<span class="behavior-title">Issue through MMIO</span><div>${nested.html}</div>`};
  }
  if (row.kind === 'tensix') {
    const fields = info.args.map(f => `${f.name}=${f.label || f.value}`).join(' · ');
    const active = 'active lanes';
    switch (info.op) {
      case 'NOP': return result('No operation');
      case 'SFPNOP': return result('SFPU dependency spacing');
      case 'SEMPOST': return result(`Post ${arg('sem_sel')}`, 'increment selected semaphores');
      case 'SEMGET': return result(`Get ${arg('sem_sel')}`, 'decrement selected semaphores');
      case 'SEMINIT': return result(`Initialize ${arg('sem_sel')} ← ${a.init_value}`, `maximum ${a.max_value}`);
      case 'SEMWAIT': return result(`Wait while ${arg('sem_sel')} ${({1:'is empty',2:'is full',3:'is empty or full'})[a.wait_sem_cond] || `condition=${a.wait_sem_cond}`}`,`block ${arg('stall_res')}`);
      case 'STALLWAIT': return result(`Stall ${arg('stall_res')}`,`until conditions clear: ${arg('wait_res')}`);
      case 'REPLAY': return result(`${a.load_mode ? 'Record' : 'Replay'} ${a.len || 64} instructions ${a.load_mode ? 'into' : 'from'} replay[${a.start_idx}]`, a.load_mode ? (a.execute_while_loading ? 'execute while recording' : 'record without executing') : 'expand the stored instruction sequence');
      case 'MOP': return result('Execute configured macro-op',a.mop_type === 1 ? 'nested-loop template; counts and instructions from MopCfg' : fields);
      case 'SFPLOAD': case 'SFPSTORE': {
        const location = `Dst[offset=${a.dest_reg_addr} + configured counters]`;
        const fmt = ({0:'configured format',1:'FP16',2:'BF16',3:'FP32'})[a.instr_mod0] || `transfer mode ${a.instr_mod0}`;
        return result(info.op === 'SFPLOAD' ? `${reg(a.lreg_ind)} ← ${location}` : `${location} ← ${reg(a.lreg_ind)}`,`${active} · ${fmt} · address modifier ${a.sfpu_addr_mode}`);
      }
      case 'SFPLOADI': {
        const mode = a.instr_mod0;
        let value = hex(a.imm16,4);
        if (mode === 2) value = String(a.imm16);
        if (mode === 4) value = String(a.imm16 & 0x8000 ? a.imm16-65536 : a.imm16);
        if (mode === 0) { const buffer = new ArrayBuffer(4); const view = new DataView(buffer); view.setUint32(0,a.imm16 << 16,true); value = `${view.getFloat32(0,true)} (BF16 ${hex(a.imm16,4)})`; }
        return result(`${reg(a.lreg_ind)}${mode === 8 ? '.high16' : mode === 10 ? '.low16' : ''} ← ${value}`,`${active} · ${({0:'BF16 broadcast',1:'FP16-like conversion',2:'unsigned integer',4:'signed integer',8:'preserve lower half',10:'preserve upper half'})[mode] || `mode ${mode}`}`);
      }
      case 'SFPADD': case 'SFPMUL': case 'SFPMAD': {
        const modifier = a.instr_mod1;
        if (modifier >= 4 || a.lreg_dest >= 8) break;
        const A = (modifier & 1 ? '−' : '') + reg(a.lreg_src_a), B = reg(a.lreg_src_b), C = reg(a.lreg_src_c);
        let expression = `${A} × ${B} ${modifier & 2 ? '−' : '+'} ${C}`;
        if (info.op === 'SFPADD' && a.lreg_src_a === 10) expression = `${modifier & 1 ? '−' : ''}${B} ${modifier & 2 ? '−' : '+'} ${C}`;
        if (info.op === 'SFPMUL' && a.lreg_src_c === 9) expression = `${A} × ${B}`;
        return result(`${reg(a.lreg_dest)} ← ${expression}`,`${active} · FP32${info.op === 'SFPMAD' ? ' fused multiply-add' : ''}`);
      }
      case 'SFPMOV': if ([0,1,2].includes(a.instr_mod1) && a.imm12_math === 0 && a.lreg_dest < 8) return result(`${reg(a.lreg_dest)} ← ${a.instr_mod1 === 1 ? 'toggle_sign(' : ''}${reg(a.lreg_c)}${a.instr_mod1 === 1 ? ')' : ''}`,a.instr_mod1 === 2 ? 'all lanes' : active); break;
      case 'SFPABS': if (a.imm12_math === 0 && a.instr_mod1 <= 1 && a.lreg_dest < 8) return result(`${reg(a.lreg_dest)} ← abs(${reg(a.lreg_c)})`,`${active} · ${a.instr_mod1 ? 'FP32; negative NaNs unchanged' : 'signed integer'}`); break;
      case 'SFPAND': case 'SFPOR': case 'SFPXOR': {
        if (a.lreg_dest >= 8 || a.instr_mod1 > 1 || a.imm12_math > 15 || (info.op === 'SFPXOR' && (a.instr_mod1 || a.imm12_math))) break;
        const input = a.instr_mod1 & 1 ? a.imm12_math : a.lreg_dest;
        return result(`${reg(a.lreg_dest)} ← ${reg(input)} ${({SFPAND:'&',SFPOR:'|',SFPXOR:'^'})[info.op]} ${reg(a.lreg_c)}`,`${active} · bitwise`);
      }
      case 'SFPENCC': {
        if (a.lreg_c || a.lreg_dest || ![1,2,8,9,10].includes(a.instr_mod1)) break;
        const mode = a.instr_mod1;
        const predicate = mode & 1 ? 'Toggle lane predication' : mode & 2 ? `${a.imm12_math & 1 ? 'Enable' : 'Disable'} lane predication` : 'Keep lane predication';
        return result(predicate, `lane flags ← ${mode & 8 ? Boolean(a.imm12_math & 2) : true}`);
      }
      case 'SETADCXX': return result(`Set X counters: start ← ${a.x_start}, end ← ${a.x_end2}`,`units: ${[a.CntSetMask&1 ? 'unpacker 0' : '',a.CntSetMask&2 ? 'unpacker 1' : '',a.CntSetMask&4 ? 'packers' : ''].filter(Boolean).join(', ')}`);
      case 'TRNSPSRCB': return result('Transpose SrcB rows 16–31', '16 × 16 matrix in the current SrcB bank');
    }
    return result(doc?.title || info.op, fields);
  }
  const register = n => `x${n}`;
  if (row.memory) {
    const knownAddress = row.address !== null && row.address !== undefined;
    const numeric = knownAddress ? hex(row.address) : null;
    // Also accept earlier cached captures that only have the display annotation.
    const addressAnnotation = knownAddress ? row.annotations.find(a => a === numeric || a.endsWith(' · '+numeric)) : null;
    const symbolic = row.addressLabel || (addressAnnotation && addressAnnotation !== numeric ? addressAnnotation.slice(0,-numeric.length-3) : null);
    const loc = knownAddress ? symbolic || numeric : `${register(row.rs1)}${row.imm < 0 ? ' − ' : ' + '}${Math.abs(row.imm)}`;
    const bits = row.width * 8;
    const notes = row.annotations.filter(a => a !== addressAnnotation && !a.startsWith('x') && !a.startsWith('write ')).join(' · ');
    if (row.memory === 'read') return result(`${register(row.rd)} ← load${bits}(${loc})`,notes);
    const value = row.annotations.find(a => a.startsWith('write '))?.slice(6) || register(row.rs2);
    return result(`store${bits}(${loc}) ← ${value}`,notes);
  }
  if (row.branch || row.jump) {
    const label = currentImage?.rows.find(r => r.pc === row.target)?.labels[0] || (row.target !== undefined ? hex(row.target) : `${register(row.rs1)} + ${row.imm}`);
    const comparison = ({beq:'=',bne:'≠',blt:'< signed',bge:'≥ signed',bltu:'< unsigned',bgeu:'≥ unsigned'})[row.op];
    const prefix = row.branch ? `if ${register(row.rs1)} ${comparison} ${register(row.rs2)} → ` : row.rd ? `call (return in ${register(row.rd)}) → ` : 'jump → ';
    return {plain:prefix+label,html:`<span class="behavior-title">${h(prefix)}${row.target !== undefined ? `<button class="target" data-target="${row.target}">${h(label)}</button>` : h(label)}</span>`};
  }
  if (row.resolved !== undefined) {
    const slot = mopSlot(row.resolved);
    if (slot !== null) return result(`${register(row.rd)} ← address of MOP[${slot}]`,`${hex(row.resolved)} · register setup; no memory write`);
    const use = nextRegisterUse(row,currentImage);
    if (use?.memory === 'write' && use.rs2 === row.rd && use.embedded?.tensixWord === row.resolved) {
      const destination = mopSlot(use.address);
      return result(`${register(row.rd)} ← encoding of ${use.embedded.op}`,`${hex(row.resolved)} · prepare instruction bits${destination !== null ? ` for MOP[${destination}]` : ' for MMIO'}; not executed here`);
    }
    const annotation=row.annotations.map(a => a.replace(/^x\d+ = 0x[\da-f]+(?: · )?/,'')).filter(Boolean).join(' · ');
    return result(`${register(row.rd)} ← ${hex(row.resolved)}`,annotation || 'RISC-V register assignment; no memory write');
  }
  if (row.op === 'fence') return result('Memory ordering fence', 'order earlier accesses before later accesses');
  if (row.rd !== undefined && row.rs1 !== undefined && row.csr === undefined) {
    const operator = ({addi:'+',add:'+',sub:'−',mul:'×',divu:'÷ unsigned',remu:'% unsigned',sltu:'< unsigned',sltiu:'< unsigned',min:'min signed',and:'&',andi:'&',or:'|',ori:'|',xor:'^',xori:'^',slli:'<<',srli:'>> unsigned',srai:'>> signed'})[row.op];
    if (operator) return result(`${register(row.rd)} ← ${register(row.rs1)} ${operator} ${row.rs2 !== undefined ? register(row.rs2) : row.imm}`);
  }
  return result(`${row.op} ${row.operands}`,row.annotations.join(' · '));
}

// Hide proven constant/address preparation, not runtime arithmetic or side effects.
export function isRegisterSetup(row) {
  return row.kind === 'riscv' && row.rd > 0 && row.resolved !== undefined
    && !row.memory && !row.branch && !row.jump && row.csr === undefined;
}
