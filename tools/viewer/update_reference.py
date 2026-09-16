"""Refresh bundled reference data from sibling working trees (no network needed)."""
import hashlib
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WORKSPACE=ROOT.parent
DATA=HERE/'data'
sys.path.insert(0,str(ROOT))

def main():
    docs=WORKSPACE/'tt-ins-docs'
    subprocess.run([sys.executable,str(docs/'scripts/build_reference.py')],check=True)
    shutil.copyfile(docs/'lib/instructions.json',DATA/'instructions.json')
    files=[docs/'lib/instructions.json', ROOT/'ttko/isa.py']
    for name in ('tensix_regs.json','tile_regs.json','tensix_isa.json'):
        source=WORKSPACE/'ttsim/data/bh'/name
        shutil.copyfile(source,DATA/name); files.append(source)
    # Supplement the simulator's intentionally partial table using the Blackhole
    # register header referenced by the ISA manual's BackendConfiguration page.
    header=WORKSPACE/'tt-metal/tt_metal/hw/inc/internal/tt-1xx/blackhole/cfg_defines.h'
    definitions={}; group=None
    for line in header.read_text().splitlines():
        if 'Registers for ' in line: group='thread_cfg' if 'Registers for THREAD' in line else 'cfg'
        match=re.match(r'#define (\w+)_(ADDR32|SHAMT|MASK)\s+(0x[\da-fA-F]+|\d+)\s*$',line)
        if group and match:
            name,field,value=match.groups(); definitions.setdefault((group,name),{})[field]=int(value,0)
    registers={'cfg':{},'thread_cfg':{}}
    for (group,name),fields in definitions.items():
        if set(fields)!={'ADDR32','SHAMT','MASK'}: continue
        mask=fields['MASK'] >> fields['SHAMT']
        if not mask or mask & (mask+1): raise ValueError('Noncontiguous mask: '+name)
        registers[group].setdefault(str(fields['ADDR32']),[]).append(dict(name=name,shift=fields['SHAMT'],size=mask.bit_length()))
    (DATA/'registers_full.json').write_text(json.dumps(registers,indent=2)+'\n'); files.append(header)
    symbols={}; enums={}
    for module_name in ('firmware.consts','tests.movement.unpacker.unpack'):
        module=importlib.import_module(module_name)
        for name,value in vars(module).items():
            if name.startswith('_'): continue
            items=vars(value).items() if isinstance(value,type) and value.__module__==module_name else [(name,value)]
            for field,constant in items:
                if field.startswith('_') or not field.isupper(): continue
                label=(name+'.'+field) if isinstance(value,type) else name
                if isinstance(constant,int):
                    if constant >= 4096: symbols.setdefault(str(int(constant)&0xffffffff),[]).append(label)
                    if isinstance(value,type): enums.setdefault(name,{})[field]=int(constant)
    (DATA/'symbols.json').write_text(json.dumps(dict(addresses=symbols,enums=enums),indent=2)+'\n')
    cpp=WORKSPACE/'ttsim/src/tensix.cpp'; text=cpp.read_text(); files.append(cpp)
    resets={'9':dict(value=0,note='Zero from memset in tensix_init')}
    for match in re.finditer(r'p_tensix->l_regs\[(\d+)\]\[lane\] = (0x[\da-fA-F]+);',text):
        resets[match[1]]=dict(value=int(match[2],16),line=text[:match.start()].count('\n')+1)
    resets['15']=dict(expression='lane << 1',note='Lane ID; mutable lane configuration')
    (DATA/'sfpu_registers.json').write_text(json.dumps(resets,indent=2)+'\n')
    provenance=dict(sources=[dict(path=str(p.relative_to(WORKSPACE)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
    (DATA/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(f'Bundled {sum(len(v) for g in registers.values() for v in g.values())} configuration fields.')

if __name__=='__main__': main()
