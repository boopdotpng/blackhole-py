import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describeOperation, isRegisterSetup } from './static/behavior.mjs';
const docs = JSON.parse(readFileSync(new URL('./data/instructions.json',import.meta.url))).instructions;
const tt = (op,args) => ({op,kind:'tensix',doc:'TT'+op,args:Object.entries(args).map(([name,value])=>({name,value})),annotations:[]});
const describe = row => describeOperation(row,docs,{rows:[]});
assert.match(describe(tt('SFPADD',{lreg_src_a:10,lreg_src_b:2,lreg_src_c:3,lreg_dest:0,instr_mod1:2})).plain,/L0 ← L2 − L3/);
assert.match(describe(tt('SFPMAD',{lreg_src_a:2,lreg_src_b:3,lreg_src_c:4,lreg_dest:1,instr_mod1:1})).plain,/L1 ← −L2 × L3 \+ L4/);
assert.match(describe(tt('SFPLOADI',{lreg_ind:1,instr_mod0:4,imm16:65535})).plain,/L1 ← -1/);
assert.match(describe(tt('SFPLOADI',{lreg_ind:1,instr_mod0:0,imm16:0x3f80})).plain,/L1 ← 1 \(BF16/);
assert.match(describe(tt('SFPENCC',{lreg_c:0,lreg_dest:0,imm12_math:0,instr_mod1:2})).plain,/Disable lane predication.*lane flags ← true/);
assert.match(describe(tt('REPLAY',{load_mode:1,len:16,start_idx:4,execute_while_loading:0})).plain,/Record 16 instructions into replay\[4\].*without executing/);
assert.match(describe({...tt('SETC16',{}),config:{group:'thread_cfg',index:0,fields:[{name:'CFG_STATE_ID_StateID',value:1}],mask:null,bank:'current thread'}}).plain,/thread.CFG_STATE_ID_StateID ← 1/);
assert.match(describe({kind:'riscv',op:'sw',args:[],memory:'write',address:0x50000,width:4,rs2:5,annotations:['write 0x00000040']}).plain,/store32\(0x00050000\) ← 0x00000040/);
assert.match(describe({kind:'unknown',op:'.word',operands:'<script>',args:[],annotations:[]}).html,/&lt;script&gt;/);
assert.match(describe({kind:'riscv',op:'beq',branch:true,rs1:1,rs2:2,target:0x40,args:[],annotations:[]}).html,/data-target="64"/);
if (process.argv[2]) {
  const captured = JSON.parse(readFileSync(process.argv[2]));
  const results = captured.result ? [captured.result] : captured.results;
  let count=0;
  for (const result of results) for (const image of result.images) for (const row of image.rows) {
    const display=describeOperation(row,docs,image);
    assert.equal(typeof display.plain,'string');assert.ok(display.html);count++;
  }
  console.log(`Rendered ${count} captured operations without errors.`);
}
const nop = {...tt('NOP',{}),tensixWord:0x02000000};
const writeNOP = {kind:'riscv',op:'sw',args:[],memory:'write',address:0xffb8000c,rs1:4,rs2:5,width:4,embedded:nop,annotations:[]};
assert.match(describe(writeNOP).plain,/MOP\[3\] ← NOP.*nothing executes here/);
const setup = {kind:'riscv',op:'lui',rd:5,resolved:0x02000000,annotations:[]};
assert.match(describeOperation(setup,docs,{rows:[setup,writeNOP]}).plain,/x5 ← encoding of NOP/);
assert.match(describe({...setup,rd:4,resolved:0xffb8000c}).plain,/x4 ← address of MOP\[3\]/);
const branch = {kind:'riscv',branch:true};
assert.doesNotMatch(describeOperation(setup,docs,{rows:[setup,branch,writeNOP]}).plain,/encoding of NOP/);
const savedConfig = {...writeNOP,embedded:{...tt('SETC16',{}),config:{group:'thread_cfg',index:0,fields:[{name:'CFG_STATE_ID_StateID',value:1}],mask:null,bank:'current thread'}}};
assert.match(describe(savedConfig).plain,/MOP\[3\] ← SETC16.*nothing executes here/);
console.log('15 behavior checks passed.');

assert.equal(isRegisterSetup({kind:'riscv',op:'lui',rd:4,resolved:0xffb80000}),true);
assert.equal(isRegisterSetup({kind:'riscv',op:'addi',rd:4}),false); // Runtime loop update.
assert.equal(isRegisterSetup({kind:'riscv',rd:4,resolved:1,memory:'read'}),false);
assert.equal(isRegisterSetup({kind:'riscv',rd:1,resolved:0x4004,jump:true}),false);
assert.equal(isRegisterSetup({kind:'riscv',rd:0,resolved:0}),false); // Dependency/sync idioms.
assert.equal(isRegisterSetup({kind:'riscv',rd:4,resolved:0,csr:0x7c0}),false);
assert.equal(isRegisterSetup({kind:'tensix',rd:4,resolved:0}),false);
console.log('7 setup visibility checks passed.');

assert.match(describe(tt('RDCFG',{GprAddress:3,CfgReg:12})).plain,/TensixGPR\[3\] ← config\[12\].*configuration read/);
assert.match(describe(tt('WRCFG',{GprAddress:7,CfgReg:15,wr128b:1})).plain,/config\[12…15\] ← TensixGPR\[4…7\].*128-bit/);
assert.match(describe({...tt('NOP',{}),replayRecord:{slot:4,execute:false}}).plain,/Record only replay\[4\]/);
assert.match(describe(tt('REPLAY',{start_idx:0,len:0,load_mode:0,execute_while_loading:0})).plain,/Replay 64 instructions/);
console.log('4 recording/config-transfer checks passed.');
