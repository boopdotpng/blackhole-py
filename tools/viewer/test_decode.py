"""Regression tests for binary decoding and safe annotations (no card required)."""
import inspect
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from asm import Asm
from isa import R, RV32, Tensix
from decode import ENCODERS, config_fields, cfg_address, decode_word, disassemble, tt_decode


def rows(words,base=0x4000):
    return disassemble(b''.join(w.to_bytes(4,'little') for w in words),base)


class DecodeTests(unittest.TestCase):
    def test_all_tensix_encoders_roundtrip(self):
        rng=random.Random(123)
        for opcode,(name,fields) in ENCODERS.items():
            for _ in range(8):
                values={n:rng.randrange(1<<(hi-lo+1)) for n,hi,lo in fields}
                word=int(getattr(Tensix,name)(**values))
                raw=((word<<2)|(word>>30))&0xffffffff
                decoded=decode_word(raw,0)
                self.assertEqual(decoded['op'],name[2:],name)
                self.assertEqual({a['name']:a['value'] for a in decoded['args']},values,name)
                self.assertEqual(decoded['tensixWord'],word)

    def test_every_rv32_encoder_has_decode(self):
        rv=RV32()
        for name,fn in inspect.getmembers(rv,inspect.ismethod):
            if name.startswith('_'): continue
            values={'rd':R.X9,'rs1':R.X3,'rs2':R.X18,'imm':-72,'shamt':13,'offset':-16,'csr':0x7c0}
            args={k:values[k] for k in inspect.signature(fn).parameters}
            word=fn(**args); row=decode_word(word,0x10000)
            self.assertEqual(row['op'],name.rstrip('_'),name)
            if 'rd' in args: self.assertEqual(row['rd'],9,name)
            if 'rs1' in args: self.assertEqual(row['rs1'],3,name)
            if 'rs2' in args: self.assertEqual(row['rs2'],18,name)
            if 'offset' in args and 'target' in row: self.assertEqual(row['target'],0xfff0,name)

    def test_store_negative_offset_uses_rs2(self):
        row=decode_word(RV32().sw(R.X17,R.X6,-2048),0)
        self.assertEqual((row['rs1'],row['rs2'],row['imm']),(6,17,-2048))

    def test_li_rounding_and_signed_immediates(self):
        for value in (0,0x7ff,0x800,0xffef0004,0x80000000,0xffffffff):
            k=Asm('trisc1'); k.li(R.X7,value)
            decoded=disassemble(k.assemble(),k.base)
            self.assertEqual(decoded[-1]['resolved'],value)

    def test_loop_must_not_claim_first_iteration_constant(self):
        rv=RV32()
        decoded=rows([rv.addi(R.X5,R.ZERO,0),rv.addi(R.X5,R.X5,1),rv.bne(R.X5,R.X6,-4),rv.sw(R.X5,R.X7)])
        self.assertNotIn('resolved',decoded[1])
        self.assertIn('Address depends on runtime register values',decoded[3]['annotations'])

    def test_branch_join_forgets_conflicting_addresses(self):
        rv=RV32()
        decoded=rows([rv.lui(R.X5,0xffef0000),rv.beq(R.X1,R.X2,8),rv.addi(R.X5,R.X5,4),rv.sw(R.ZERO,R.X5)])
        self.assertIsNone(decoded[-1]['address'])
        self.assertNotIn('config',decoded[-1])

    def test_branch_join_keeps_equal_constants(self):
        rv=RV32()
        decoded=rows([rv.lui(R.X5,0xffef0000),rv.beq(R.X1,R.X2,8),rv.addi(R.X5,R.X5,0),rv.sw(R.ZERO,R.X5)])
        self.assertEqual(decoded[-1]['config']['index'],0)

    def test_mmio_tensix_is_unrotated(self):
        k=Asm('brisc'); word=Tensix.TTSETC16(0,1); k.emit(word)
        decoded=disassemble(k.assemble(),k.base)
        embedded=decoded[-1]['embedded']
        self.assertEqual(embedded['tensixWord'],int(word))
        self.assertEqual(embedded['config']['fields'][0]['value'],1)

    def test_mop_template_is_unrotated(self):
        k=Asm('trisc0'); word=Tensix.TTREPLAY(2,3,0,0); k.write(0xffb80008,int(word))
        decoded=disassemble(k.assemble(),k.base)
        self.assertEqual(decoded[-1]['embedded']['op'],'REPLAY')

    def test_masked_config_does_not_zero_unwritten_bits(self):
        cfg=config_fields('cfg',0,0xffffffff,1)
        field=next(f for f in cfg['fields'] if f['name']=='ALU_FORMAT_SPEC_REG_SrcA_val')
        self.assertTrue(field['partial']); self.assertEqual(field['value'],1)
        self.assertEqual(len(cfg['fields']),1)

    def test_cfg_banks_and_thread_windows(self):
        self.assertEqual(cfg_address(0xffef0384),('cfg',1,'bank 1'))
        self.assertEqual(cfg_address(0xffef0704),('cfg',1,'both banks'))
        self.assertEqual(cfg_address(0xffef0b94),('thread_cfg',1,'thread 1'))
        self.assertIsNone(cfg_address(0xffef0db0))

    def test_supplemental_fields_have_provenance(self):
        cfg=config_fields('cfg',187,0)
        self.assertFalse(cfg['unknown'])
        self.assertTrue(all(f['source']=='tt-metal Blackhole cfg_defines.h' for f in cfg['fields']))

    def test_unknown_opcode_invalidates_constants(self):
        rv=RV32(); decoded=rows([rv.lui(R.X5,0xffef0000),0xffffffff,rv.sw(R.ZERO,R.X5)])
        self.assertEqual(decoded[1]['kind'],'unknown')
        self.assertIsNone(decoded[2]['address'])

    def test_jal_unreachable_fallthrough(self):
        rv=RV32(); decoded=rows([rv.jal(R.ZERO,8),rv.lui(R.X5,0xffef0000),rv.sw(R.ZERO,R.X5)])
        self.assertIn('Unreachable by statically known control flow',decoded[1]['annotations'])
        self.assertIsNone(decoded[2]['address'])

    def test_long_branch_veneer_decodes_actual_bytes(self):
        k=Asm('trisc1');k.beq(R.X5,R.X6,'end')
        for _ in range(1100): k.emit(Tensix.TTNOP())
        k.label('end'); image=k.assemble(); decoded=disassemble(image,k.base)
        self.assertEqual(decoded[0]['op'],'bne');self.assertEqual(decoded[0]['target'],k.base+8)
        self.assertEqual(decoded[1]['op'],'jal');self.assertEqual(decoded[1]['target'],k.base+len(image))

    def test_record_only_payload_is_not_marked_as_execution(self):
        k=Asm('trisc1')
        k.emit(Tensix.TTREPLAY(5,2,0,1))
        k.emit(Tensix.TTNOP()); k.emit(Tensix.TTSETC16(0,1)); k.emit(Tensix.TTNOP())
        decoded=disassemble(k.assemble(),k.base)
        self.assertEqual(decoded[1]['replayRecord'],dict(slot=5,execute=False))
        self.assertEqual(decoded[2]['replayRecord'],dict(slot=6,execute=False))
        self.assertNotIn('replayRecord',decoded[3])

    def test_execute_while_recording_and_slot_wrap(self):
        k=Asm('trisc1'); k.emit(Tensix.TTREPLAY(31,2,1,1))
        k.emit(Tensix.TTNOP()); k.emit(Tensix.TTNOP())
        decoded=disassemble(k.assemble(),k.base)
        self.assertEqual(decoded[2]['replayRecord'],dict(slot=0,execute=True))

    def test_replay_recording_does_not_guess_across_control_flow(self):
        k=Asm('trisc1'); k.emit(Tensix.TTREPLAY(0,2,0,1))
        k.beq(R.X1,R.X2,'target'); k.label('target'); k.emit(Tensix.TTNOP())
        decoded=disassemble(k.assemble(),k.base)
        self.assertNotIn('replayRecord',decoded[-1])

    def test_load_invalidates_destination(self):
        rv=RV32(); decoded=rows([rv.lui(R.X5,0xffef0000),rv.lw(R.X5,R.X6),rv.sw(R.ZERO,R.X5)])
        self.assertIsNone(decoded[-1]['address'])

if __name__=='__main__': unittest.main()
