"""Decode emitted bytes; annotations use a conservative constant analysis over the CFG."""
import ast
from collections import deque
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).with_name('data')
DOCS = json.loads((DATA / 'instructions.json').read_text())
DOC_BY_NAME = {d['name']: d for d in DOCS['instructions']}
REGS = json.loads((DATA / 'tensix_regs.json').read_text())
TILE = json.loads((DATA / 'tile_regs.json').read_text())
SIM_ISA = json.loads((DATA / 'tensix_isa.json').read_text())
FULL_REGS = json.loads((DATA / 'registers_full.json').read_text())
SYMBOLS = json.loads((DATA / 'symbols.json').read_text())
SFPU_REGS = json.loads((DATA / 'sfpu_registers.json').read_text())
MASK = 0xffffffff
ABI = 'zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6'.split()

def hex32(n): return f'0x{n & MASK:08x}'
def signed(n, bits): return n - (1 << bits) if n & (1 << (bits - 1)) else n

def encoders():
    result = {}
    for node in ast.walk(ast.parse((ROOT / 'isa.py').read_text())):
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith('TT'): continue
        call = next((n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == '_tt'), None)
        if call is None: continue
        fields = [(ast.unparse(a.elts[0]), ast.literal_eval(a.elts[1]), ast.literal_eval(a.elts[2])) for a in call.args[1:]]
        result[ast.literal_eval(call.args[0])] = (node.name, fields)
    return result

ENCODERS = encoders()


def config_fields(group, index, value=None, mask=None):
    fields = list(REGS[group].get(str(index), []))
    known = {f['name'] for f in fields}
    fields += [dict(f, supplemental=True) for f in FULL_REGS[group].get(str(index), []) if f['name'] not in known]
    out = []
    for f in fields:
        bits = ((1 << f['size']) - 1) << f['shift']
        if mask is not None and not bits & mask: continue
        v = None if value is None else (value & bits & (MASK if mask is None else mask)) >> f['shift']
        partial = mask is not None and mask & bits != bits
        out.append(dict(name=f['name'], value=v, lo=f['shift'], hi=f['shift']+f['size']-1,
                        partial=partial, unsupported=f.get('unsupported', False),
                        source='tt-metal Blackhole cfg_defines.h' if f.get('supplemental') else 'ttsim/data/bh/tensix_regs.json'))
    return dict(group=group, index=index, fields=out, value=value, mask=mask,
                source='ttsim + Blackhole cfg_defines.h', unknown=not bool(fields),
                bank='current thread StateID' if group=='cfg' else 'current thread')


def tt_decode(word):
    entry = ENCODERS.get(word >> 24)
    if entry is None:
        return dict(op='.word', operands=hex32(word), kind='unknown', args=[], note='Unknown Tensix opcode')
    name, fields = entry
    doc = DOC_BY_NAME.get(name, {})
    meanings = {a['name']: a for a in doc.get('args', [])}
    args = [dict(name=n, value=(word >> lo) & ((1 << (hi-lo+1))-1), hi=hi, lo=lo,
                 meaning=meanings.get(n, {}).get('meaning', 'Raw field from isa.py.')) for n,hi,lo in fields]
    for arg in args:
        arg['label'] = operand_label(name, arg['name'], arg['value'])
    values = {a['name']: a['value'] for a in args}
    row = dict(op=name.removeprefix('TT'), doc=name, operands=', '.join(f"{a['name']}={a['value']}" for a in args),
               kind='tensix', args=args, tensixWord=word)
    if name == 'TTSETC16':
        row['config'] = config_fields('thread_cfg', values['setc16_reg'], values['setc16_value'])
    elif name.startswith('TTRMWCIB'):
        shift = int(name[-1]) * 8
        row['config'] = config_fields('cfg', values['CfgRegAddr'], values['Data'] << shift, values['Mask'] << shift)
        row['config']['operation'] = 'read-modify-write; unmasked bits preserved'
    elif name in ('TTWRCFG', 'TTRDCFG'):
        row['config'] = config_fields('cfg', values.get('CfgReg', values.get('CfgRegAddr', 0)))
        row['config']['operation'] = ('Read configuration into Tensix GPR' if name == 'TTRDCFG' else 'Write configuration from Tensix GPR') + '; value is runtime-dependent'
    sim = SIM_ISA.get(name[2:], {})
    row['simArgs'] = [dict(name=n, hi=int(span.split(':')[0]), lo=int(span.split(':')[1]),
                          value=(word >> int(span.split(':')[1])) & ((1 << (int(span.split(':')[0])-int(span.split(':')[1])+1))-1))
                      for n, span in sim.get('args', {}).items()]
    return row


def decode_word(w, pc):
    if w & 3 != 3:
        row = tt_decode(((w >> 2) | (w << 30)) & MASK)
        row['encoding'] = 'inline Tensix: rotate emitted word right by 2'
        return row
    op, rd, f3, a, b, f7 = w & 127, (w >> 7) & 31, (w >> 12) & 7, (w >> 15) & 31, (w >> 20) & 31, w >> 25
    imm = signed(w >> 20, 12)
    row = dict(kind='riscv', args=[])
    def finish(name, operands, **kw):
        row.update(op=name, operands=operands, **kw)
        return row
    reg = lambda n: f'x{n}'
    if op in (0x37, 0x17): return finish('lui' if op == 0x37 else 'auipc', f'{reg(rd)}, 0x{w >> 12:05x}', rd=rd, imm=w & 0xfffff000)
    if op == 0x33:
        name = {(0,0):'add',(0,32):'sub',(0,1):'mul',(5,1):'divu',(7,1):'remu',(3,0):'sltu',(4,5):'min',(7,0):'and',(6,0):'or',(4,0):'xor'}.get((f3,f7))
        if name: return finish(name, f'{reg(rd)}, {reg(a)}, {reg(b)}', rd=rd, rs1=a, rs2=b)
    if op == 0x13:
        name = {0:'addi',3:'sltiu',7:'andi',6:'ori',4:'xori'}.get(f3)
        if f3 == 1 and f7 == 0: name, imm = 'slli', b
        if f3 == 5 and f7 in (0,32): name, imm = ('srai' if f7 else 'srli'), b
        if name: return finish(name, f'{reg(rd)}, {reg(a)}, {imm}', rd=rd, rs1=a, imm=imm)
    if op == 3 and f3 in (2,4,5): return finish({2:'lw',4:'lbu',5:'lhu'}[f3], f'{reg(rd)}, {imm}({reg(a)})', rd=rd, rs1=a, imm=imm, memory='read', width={2:4,4:1,5:2}[f3])
    if op == 0x23 and f3 in (0,1,2):
        imm = signed(((w >> 25) << 5) | ((w >> 7) & 31), 12)
        return finish({0:'sb',1:'sh',2:'sw'}[f3], f'{reg(b)}, {imm}({reg(a)})', rs1=a, rs2=b, imm=imm, memory='write', width=1 << f3)
    if op == 0x63 and f3 in (0,1,4,5,6,7):
        imm = signed(((w >> 31) << 12) | (((w >> 7) & 1) << 11) | (((w >> 25) & 63) << 5) | (((w >> 8) & 15) << 1),13)
        return finish({0:'beq',1:'bne',4:'blt',5:'bge',6:'bltu',7:'bgeu'}[f3], f'{reg(a)}, {reg(b)}, {hex32(pc+imm)}', rs1=a, rs2=b, target=(pc+imm)&MASK, branch=True)
    if op == 0x6f:
        imm = signed(((w >> 31) << 20) | (((w >> 12)&255)<<12) | (((w >> 20)&1)<<11) | (((w >> 21)&1023)<<1),21)
        return finish('jal', f'{reg(rd)}, {hex32(pc+imm)}', rd=rd, target=(pc+imm)&MASK, jump=True)
    if op == 0x67 and f3 == 0: return finish('jalr',f'{reg(rd)}, {imm}({reg(a)})',rd=rd,rs1=a,imm=imm,jump=True)
    if op == 0x73 and f3 in (2,3): return finish('csrrs' if f3 == 2 else 'csrrc',f'{reg(rd)}, 0x{w>>20:03x}, {reg(a)}',rd=rd,rs1=a,csr=w>>20)
    if op == 0x0f and f3 == 0: return finish('fence', f'0x{(w>>24)&15:x}, 0x{(w>>20)&15:x}')
    return finish('.word',hex32(w),kind='unknown',note='Unrecognized RISC-V encoding; no semantic inference')


def transfer(row, state):
    s = list(state)
    op = row['op']; a = s[row.get('rs1',0)]; b = s[row.get('rs2',0)]; v = row.get('imm')
    result = None
    if row['kind'] == 'unknown': return (0,) + (None,)*31
    if op == 'lui': result = v
    elif op == 'auipc': result = row['pc'] + v
    elif op in ('jal','jalr'): result = row['pc'] + 4
    elif a is not None:
        if op == 'addi': result = a+v
        elif op == 'sltiu': result = int(a < (v&MASK))
        elif op == 'andi': result = a&v
        elif op == 'ori': result = a|v
        elif op == 'xori': result = a^v
        elif op == 'slli': result = a << v
        elif op == 'srli': result = a >> v
        elif op == 'srai': result = signed(a,32) >> v
        elif b is not None:
            if op == 'add': result = a+b
            elif op == 'sub': result = a-b
            elif op == 'mul': result = a*b
            elif op == 'divu': result = a//b if b else MASK
            elif op == 'remu': result = a%b if b else a
            elif op == 'min': result = min(signed(a,32),signed(b,32))
            elif op == 'sltu': result = int(a<b)
            elif op == 'and': result = a&b
            elif op == 'or': result = a|b
            elif op == 'xor': result = a^b
    if 'rd' in row and row['rd']: s[row['rd']] = None if result is None else result&MASK
    s[0] = 0
    return tuple(s)


def constants(rows, base):
    if not rows: return []
    states = [None]*len(rows); states[0] = (0,)+(None,)*31
    queue = deque([0]); pending = {0}
    while queue:
        i = queue.popleft(); pending.remove(i)
        row = rows[i]; out = transfer(row, states[i])
        successors = []
        if 'target' in row: successors.append((row['target']-base)//4 if (row['target']-base)%4 == 0 else -1)
        if not row.get('jump'): successors.append(i+1)
        # Calls can return; conservatively forget registers on the return edge.
        if row.get('jump') and row.get('rd',0): successors.append(i+1)
        for j in successors:
            if not 0 <= j < len(rows): continue
            edge = (0,)+(None,)*31 if row.get('jump') and row.get('rd',0) and j == i+1 else out
            old = states[j]
            merged = edge if old is None else tuple(x if x == y else None for x,y in zip(old,edge))
            if old != merged:
                states[j] = merged
                if j not in pending: queue.append(j); pending.add(j)
    return states


def cfg_address(addr):
    offset=addr-0xffef0000
    if not 0 <= offset < 0xdb0: return None
    if offset < 0xa80:
        bank=offset//0x380
        return 'cfg', (offset%0x380)//4, ('bank 0','bank 1','both banks')[bank]
    return 'thread_cfg', ((offset-0xa80)%0x110)//4, 'thread '+str((offset-0xa80)//0x110)


def address_label(addr):
    symbolic=SYMBOLS['addresses'].get(str(addr),[])
    space=cfg_address(addr)
    if space:
        group,index,bank=space
        fields=config_fields(group,index)['fields']
        return f"{group}[{index}] ({bank})" + (' · ' + ', '.join(f['name'] for f in fields) if fields else ' (undocumented index)')
    if symbolic: return ' · '.join(symbolic)
    if 0xffb80000 <= addr <= 0xffb80020 and addr%4==0:
        index=(addr-0xffb80000)//4
        names=('OuterCount','InnerCount / Flags','StartOp / InsnB','EndOp0 / InsnA0','EndOp1 / InsnA1','LoopOp / InsnA2','LoopOp1 / InsnA3','Loop0Last / SkipA0','Loop1Last / SkipB')
        return f'MopCfg[{index}] · {names[index]}'
    for region in TILE['address_map']:
        base, limit = int(region['base'],0), int(region['limit'],0)
        if base <= addr <= limit:
            group = next((r for r in TILE['regs'] if r['name'] == region['name']), {})
            for reg in group.get('regs',[]):
                if int(reg['offset'],0) == addr-base: return region['name']+'.'+reg['name']
            return f"{region['name']} + 0x{addr-base:x}"
    return None


def operand_label(instruction, name, value):
    if instruction.startswith('TTSFP') and name.startswith('lreg'):
        label=f'L{value}'
        # Destination selectors and several macro selectors are not reads.
        if name not in ('lreg_dest','lreg_ind') and str(value) in SFPU_REGS:
            reset=SFPU_REGS[str(value)]
            if 'value' in reset:
                number=struct.unpack('<f',struct.pack('<I',reset['value']))[0]
                label+=f" · {'programmable; ttsim reset' if 11<=value<=14 else 'constant'} {number:g} ({hex32(reset['value'])})"
            else: label+=' · lane ID (ttsim reset lane << 1)'
        return label
    enums=SYMBOLS['enums']
    group={'stall_res':'Stall','wait_res':'Wait','wait_sem_cond':'SemWait'}.get(name)
    if group:
        members=enums.get(group,{})
        if group=='SemWait': return ' | '.join(f'{group}.{k}' for k,v in members.items() if v==value)
        return ' | '.join(f'{group}.{k}' for k,v in members.items() if v and value&v==v)
    if name=='sem_sel':
        return ' | '.join('Sem.'+next((k for k,v in enums.get('Sem',{}).items() if v==i),str(i)) for i in range(8) if value&(1<<i))
    return ''


def mark_replay_recording(rows):
    """Label only unambiguous inline, straight-line recording payloads."""
    remaining = 0
    slot = 0
    execute = False
    for row in rows:
        if row.get('branch') or row.get('jump') or row.get('labels') or row['kind'] == 'unknown':
            remaining = 0
        # An MMIO instruction could address another Tensix thread; MOP expands
        # a sequence whose length is not known from its opcode alone.
        if row.get('embedded') or (row['kind'] == 'tensix' and row['op'] in ('MOP', 'MOP_CFG')):
            remaining = 0
            continue
        if row['kind'] != 'tensix':
            continue
        if remaining:
            row['replayRecord'] = dict(slot=slot % 32, execute=execute)
            row['annotations'].append(f"Record replay[{slot % 32}]" + (' and execute' if execute else '; not executed here'))
            remaining -= 1
            slot += 1
        elif row['op'] == 'REPLAY':
            args = {a['name']: a['value'] for a in row['args']}
            if args['load_mode'] == 1 and args['execute_while_loading'] in (0, 1) and args['len'] < 64 and args['start_idx'] < 32:
                remaining = args['len'] or 64
                slot = args['start_idx']
                execute = bool(args['execute_while_loading'])


def disassemble(image, base, labels=None, origins=None):
    if len(image)%4: raise ValueError('Image has incomplete 32-bit instructions')
    rows=[]
    for offset in range(0,len(image),4):
        w=int.from_bytes(image[offset:offset+4],'little'); pc=base+offset
        row=decode_word(w,pc); row.update(pc=pc,word=w,bytes=image[offset:offset+4].hex(' '),labels=(labels or {}).get(str(pc),[]),source=(origins or {}).get(str(pc)))
        rows.append(row)
    states=constants(rows,base)
    for row,state in zip(rows,states):
        row['annotations']=[f"{a['name']}: {a['label']}" for a in row.get('args',[]) if a.get('label')]
        if 'target' in row:
            row['annotations'].append('target '+hex32(row['target']))
            if base <= row['target'] < base+len(image) and (row['target']-base)%4 == 0:
                dest=rows[(row['target']-base)//4]
                if not dest['labels']: dest['labels']=[f"loc_{row['target']:x}"]
        if state is None:
            row['annotations'].append('Unreachable by statically known control flow')
            continue
        after=transfer(row,state)
        if row.get('rd') and after[row['rd']] is not None:
            value=after[row['rd']]; label=address_label(value)
            row['resolved']=value
            row['annotations'].append(f"x{row['rd']} = {hex32(value)}"+(f' · {label}' if label else ''))
        if row.get('memory'):
            address=None if state[row['rs1']] is None else (state[row['rs1']]+row['imm'])&MASK
            value=state[row['rs2']] if 'rs2' in row else None
            row['address']=address
            if address is None: row['annotations'].append('Address depends on runtime register values')
            else:
                label=address_label(address)
                row['addressLabel'] = next(iter(SYMBOLS['addresses'].get(str(address), [])), None) or label
                row['annotations'].append((label+' · ' if label else '')+hex32(address))
                space=cfg_address(address)
                if space and row['memory']=='write':
                    group,index,bank=space
                    shift=(address%4)*8; mask=((1<<(8*row['width']))-1)<<shift
                    row['config']=config_fields(group,index,None if value is None else (value<<shift)&mask,mask)
                    row['config']['bank']=bank
                    if group=='thread_cfg' or row['width']!=4:
                        row['config']['operation']='Not a supported direct RISC-V configuration write in the Blackhole manual'
                        row['annotations'].append(row['config']['operation'])
                if row['memory']=='write':
                    row['annotations'].append('write '+(hex32(value & ((1<<(row['width']*8))-1)) if value is not None else 'runtime value'))
                    if ((0xffe40000 <= address <= 0xffe40fff) or (0xffe50000 <= address <= 0xffe50fff) or (0xffe60000 <= address <= 0xffe60fff) or (0xffb80008 <= address <= 0xffb80020)) and row['width']==4 and value is not None:
                        row['embedded']=tt_decode(value)
                        row['annotations'].append(('MOP template instruction · ' if address < 0xffc00000 else 'MMIO instruction · ')+row['embedded']['op']+' '+row['embedded']['operands'])
        if 'config' in row:
            cfg=row['config']
            row['annotations'].append(f"{cfg['group']}[{cfg['index']}] ({cfg['bank']})"+(' · fields not in ttsim' if cfg['unknown'] else ''))
            for f in cfg['fields']:
                row['annotations'].append(f[ 'name']+' = '+('runtime' if f['value'] is None else str(f['value']))+(' (masked bits only)' if f['partial'] else ''))
    mark_replay_recording(rows)
    return rows
