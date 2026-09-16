"""Isolated pytest collector/capture worker. Never executes a hardware launch."""
import argparse
import hashlib
import json
import linecache
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pytest
from asm import Asm
from device import Device
from pcie import Allocator, PCIDevice, P100_WORKER_CORES, P150_DRAM_ENDPOINTS, TLBWindow
from tests.harness import RawHarness
from firmware.consts import TensixL1
from decode import disassemble


class HardwareBoundary(BaseException): pass


def no_hardware(*args, **kwargs):
    raise HardwareBoundary('Direct hardware access is unavailable in offline capture')

# Block alternate paths as well as replacing the normal bh fixture.
PCIDevice.__init__ = no_hardware
TLBWindow.__init__ = no_hardware
Device.__init__ = no_hardware


def source_stack():
    result=[]; frame=sys._getframe(2)
    while frame and len(result)<5:
        path=Path(frame.f_code.co_filename)
        if path.is_relative_to(ROOT) and 'tools/viewer' not in str(path) and path.name not in ('asm.py','isa.py'):
            result.append(dict(path=str(path.relative_to(ROOT)),line=frame.f_lineno,function=frame.f_code.co_name,
                               text=linecache.getline(str(path),frame.f_lineno).strip()))
        frame=frame.f_back
    return result


class OfflineDevice:
    """Use real allocation rules with an explicitly synthetic P150 topology."""
    alloc_dram=Device.alloc_dram
    alloc_interleaved_dram=Device.alloc_interleaved_dram
    def __init__(self, owner):
        self.owner=owner
        self.cores=P100_WORKER_CORES
        self.pcie=SimpleNamespace(cores=self.cores,dram_endpoints=P150_DRAM_ENDPOINTS,
                                  sysmem=SimpleNamespace(noc_addr=0x10000000 << 32))
        self._dram=Allocator(0x40,1 << 32,64)
    def write_dram(self,*args,**kwargs): pass
    def read_dram(self,*args,**kwargs): raise HardwareBoundary('Stopped before reading device results; later host-dependent launches are not captured.')
    def launch(self,core_images,**kwargs):
        self.owner.record_launch(core_images,kwargs)
    def __getattr__(self,name):
        raise HardwareBoundary(f'Device.{name} requires live runtime state; offline capture stopped here.')


class CaptureHarness(RawHarness):
    def __init__(self, owner): super().__init__(OfflineDevice(owner),core_index=27)
    def launch(self,images,*,params=(),l1=None,core=None,profiler=None):
        self.device.owner.record_launch({self.core if core is None else core:dict(images)},dict(params=params,l1=l1 or {}))
        if profiler is not None:
            # The hardware profiler reads the device immediately after launch.
            raise HardwareBoundary('Stopped at profiler readback; timing and later host-dependent launches require hardware.')
    def read_l1(self,*args,**kwargs): raise HardwareBoundary('Stopped before reading device results; later host-dependent launches are not captured.')


class Plugin:
    def __init__(self, capture=False, audit=False):
        self.audit=audit
        self.capture=capture; self.catalog=[]; self.results=[]; self.current=None; self.images={}
        self.old_emit=Asm._emit; self.old_instructions=Asm.instructions; self.old_lower=Asm.lower
        if capture:
            owner=self
            def emit(asm,word):
                if not hasattr(asm,'_viewer_sources'): asm._viewer_sources={}
                asm._viewer_sources[len(asm.items)]=source_stack()
                return owner.old_emit(asm,word)
            def lower(asm):
                shift=len(asm._prologue)
                if shift: asm._viewer_sources={i+shift:v for i,v in getattr(asm,'_viewer_sources',{}).items()}
                return owner.old_lower(asm)
            def instructions(asm):
                words=owner.old_instructions(asm)
                image=b''.join(word.to_bytes(4,'little') for word in words)
                if owner.current is not None:
                    digest=hashlib.sha256(image).hexdigest(); key=asm.role+':'+digest
                    if key not in owner.images:
                        long,targets=asm._layout(); labels={}
                        for name,offset in targets.items(): labels.setdefault(str(asm.base+offset),[]).append(name)
                        origins={}; extra=0
                        for i in range(len(asm.items)):
                            origin=getattr(asm,'_viewer_sources',{}).get(i)
                            if origin: origins[str(asm.base+4*(i+extra))]=origin
                            if i in long:
                                if origin: origins[str(asm.base+4*(i+extra+1))]=origin
                                extra+=1
                        owner.images[key]=dict(id=key,role=asm.role,base=asm.base,sha256=digest,size=len(image),
                                               rows=disassemble(image,asm.base,labels,origins),hex=image.hex())
                    if key not in owner.current['generated']: owner.current['generated'].append(key)
                return words
            Asm._emit=emit; Asm.lower=lower; Asm.instructions=instructions

    def pytest_collection_modifyitems(self,items):
        for item in items:
            params=getattr(item,'callspec',None)
            self.catalog.append(dict(id=item.nodeid,test=item.nodeid.split('[')[0],case=params.id if params else 'default',
                                     params={k:repr(v) for k,v in params.params.items()} if params else {},
                                     path=str(item.path.relative_to(ROOT)),line=item.location[1]+1,
                                     doc=(item.obj.__doc__ or '').strip() if hasattr(item,'obj') else ''))

    @pytest.hookimpl(tryfirst=True)
    def pytest_fixture_setup(self,fixturedef,request):
        if self.capture and fixturedef.argname=='bh':
            value=CaptureHarness(self)
            fixturedef.cached_result=(value,fixturedef.cache_key(request),None)
            return value

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_protocol(self,item,nextitem):
        if self.capture:
            self.images={}
            self.current=dict(id=item.nodeid,generated=[],launches=[],boundary=None,errors=[],status='capturing')
        result=yield
        if self.capture:
            self.current['images']=list(self.images.values())
            if self.audit:
                self.current['images']=[dict(role=i['role'], size=i['size'], rows=len(i['rows']),
                    unknown=[hex(r['word']) for r in i['rows'] if r['kind']=='unknown'],
                    config=sum('config' in r for r in i['rows'])) for i in self.current['images']]
            self.results.append(self.current); self.current=None
        return result

    @pytest.hookimpl(tryfirst=True)
    def pytest_pyfunc_call(self,pyfuncitem):
        if not self.capture: return None
        try:
            pyfuncitem.obj(**{name:pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames})
            self.current['status']='complete'
        except HardwareBoundary as error:
            self.current['boundary']=str(error); self.current['status']='boundary'
        return True

    def pytest_runtest_logreport(self,report):
        if self.current is not None and (report.failed or report.skipped):
            self.current['errors'].append(str(report.longrepr))
            self.current['status']='error' if report.failed else 'skipped'

    def record_launch(self,core_images,options):
        if self.current is None: raise RuntimeError('Launch outside capture')
        roles=[]
        for core,images in core_images.items():
            for role,image in images.items():
                image=bytes(image); digest=hashlib.sha256(image).hexdigest(); key=role+':'+digest
                if key not in self.images:
                    self.images[key]=dict(id=key,role=role,base=TensixL1.WORKER_TEXT_BASE[role],sha256=digest,size=len(image),
                                          rows=disassemble(image,TensixL1.WORKER_TEXT_BASE[role]),hex=image.hex())
                roles.append(dict(core=list(core),role=role,image=key))
        self.current['launches'].append(dict(roles=roles,params=repr(options.get('params',())),
            l1=[dict(address=a,size=len(data)) for a,data in (options.get('l1') or {}).items()],source=source_stack()))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['catalog','capture'])
    parser.add_argument('--case',default='tests')
    parser.add_argument('--output',required=True)
    parser.add_argument('--audit',action='store_true',help='Keep capture coverage counts instead of full listings')
    args=parser.parse_args()
    import os
    os.chdir(ROOT)
    plugin=Plugin(args.mode=='capture',args.audit)
    options=['-q','--tb=short','-p','no:cacheprovider',args.case]
    if args.mode=='catalog': options+=['--collect-only']
    code=pytest.main(options,plugins=[plugin])
    out=dict(cases=plugin.catalog,results=plugin.results,pytestExit=int(code),
             context=dict(mode='offline',board='synthetic P150, 8 DRAM banks',coreIndex=27,
                          dram='deterministic allocation from 0x40; not a live device allocation',
                          boundary='No device results are fabricated. Capture stops at the first required hardware result.'))
    Path(args.output).write_text(json.dumps(out,separators=(',',':')))
    return 0 if plugin.catalog else 1

if __name__=='__main__': raise SystemExit(main())
