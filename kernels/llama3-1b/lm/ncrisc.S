# llama3 1b decode: lm, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_lm_weight, 0x788=e2e_final_norm, 0x119c0=e2e_logits, 0x119c4=e2e_lm_weight_row_start, 0x119c8=e2e_lm_weight_rows, 0x119cc=dram_port
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00014437  lui          x8, 0x00014  # x8 = 0x00014000
      c: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00014000
     10: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     14: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: 00016237  lui          x4, 0x00016  # x4 = 0x00016000
     20: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
loc_24:
     24: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     28: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     2c: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     30: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     34: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     38: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     3c: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     40: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     44: 02020213  addi         x4, x4, 32
     48: ff828293  addi         x5, x5, -8
     4c: fc029ce3  bne          x5, x0, 0x00000024  # target 0x00000024
     50: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     54: 9c828293  addi         x5, x5, -1592  # x5 = 0x000119c8
     58: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x000119c8
     5c: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     60: 00020313  addi         x6, x4, 0
loc_64:
     64: 0e62f863  bgeu         x5, x6, 0x00000154  # target 0x00000154
     68: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     6c: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     70: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     74: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_78:
     78: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     7c: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     80: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     84: 407404b3  sub          x9, x8, x7
     88: 01049493  slli         x9, x9, 16
     8c: 0104d493  srli         x9, x9, 16
     90: 00a4f663  bgeu         x9, x10, 0x0000009c  # target 0x0000009c
     94: 0ff0000f  fence        0xf, 0xf
     98: fe1ff06f  jal          x0, 0x00000078  # target 0x00000078
loc_9c:
     9c: 0ff0000f  fence        0xf, 0xf
     a0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     a4: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     a8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     ac: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
     b0: 00f2f493  andi         x9, x5, 15
     b4: 00149493  slli         x9, x9, 1
     b8: 0102f593  andi         x11, x5, 16
     bc: 00559593  slli         x11, x11, 5
     c0: 00b4e4b3  or           x9, x9, x11
     c4: 1e02f593  andi         x11, x5, 480
     c8: 00b4e4b3  or           x9, x9, x11
     cc: 0092d593  srli         x11, x5, 9
     d0: 00a59593  slli         x11, x11, 10
     d4: 00b4e4b3  or           x9, x9, x11
     d8: 00016537  lui          x10, 0x00016  # x10 = 0x00016000
     dc: 00950533  add          x10, x10, x9
     e0: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
     e4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     e8: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     ec: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     f0: 00138393  addi         x7, x7, 1
     f4: 01039393  slli         x7, x7, 16
     f8: 0103d393  srli         x7, x7, 16
     fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    100: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    104: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    108: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    10c: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    110: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    114: 0ff0000f  fence        0xf, 0xf
    118: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    11c: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    120: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    124: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    128: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    12c: 008383b3  add          x7, x7, x8
    130: 000154b7  lui          x9, 0x00015  # x9 = 0x00015000
    134: 0093e663  bltu         x7, x9, 0x00000140  # target 0x00000140
    138: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    13c: 40a383b3  sub          x7, x7, x10
loc_140:
    140: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    144: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    148: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    14c: 00128293  addi         x5, x5, 1
    150: f15ff06f  jal          x0, 0x00000064  # target 0x00000064
loc_154:
    154: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    158: 064000ef  jal          x1, 0x000001bc  # target 0x000001bc; x1 = 0x0000015c
    15c: 000a8213  addi         x4, x21, 0
    160: 000b0293  addi         x5, x22, 0
    164: 0e0000ef  jal          x1, 0x00000244  # target 0x00000244; x1 = 0x00000168
    168: 0f8000ef  jal          x1, 0x00000260  # target 0x00000260; x1 = 0x0000016c
    16c: 00016fb7  lui          x31, 0x00016  # x31 = 0x00016000
    170: 00020f13  addi         x30, x4, 0
    174: 00028e93  addi         x29, x5, 0
    178: 104000ef  jal          x1, 0x0000027c  # target 0x0000027c; x1 = 0x0000017c
    17c: 0c8000ef  jal          x1, 0x00000244  # target 0x00000244; x1 = 0x00000180
    180: 0e0000ef  jal          x1, 0x00000260  # target 0x00000260; x1 = 0x00000184
    184: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    188: 034000ef  jal          x1, 0x000001bc  # target 0x000001bc; x1 = 0x0000018c
    18c: 000a8213  addi         x4, x21, 0
    190: 000b0293  addi         x5, x22, 0
    194: 0b0000ef  jal          x1, 0x00000244  # target 0x00000244; x1 = 0x00000198
    198: 0c8000ef  jal          x1, 0x00000260  # target 0x00000260; x1 = 0x0000019c
    19c: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    1a0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00016800
    1a4: 00020f13  addi         x30, x4, 0
    1a8: 00028e93  addi         x29, x5, 0
    1ac: 0d0000ef  jal          x1, 0x0000027c  # target 0x0000027c; x1 = 0x000001b0
    1b0: 094000ef  jal          x1, 0x00000244  # target 0x00000244; x1 = 0x000001b4
    1b4: 0ac000ef  jal          x1, 0x00000260  # target 0x00000260; x1 = 0x000001b8
    1b8: 1800006f  jal          x0, 0x00000338  # target 0x00000338
loc_1bc:
    1bc: 00012ab7  lui          x21, 0x00012  # x21 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1c0: 9c0a8a93  addi         x21, x21, -1600  # x21 = 0x000119c0
    1c4: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x000119c0
    1c8: 007a7d13  andi         x26, x20, 7
    1cc: ff8a7a13  andi         x20, x20, -8
    1d0: 01af8ab3  add          x21, x31, x26
    1d4: 007afb93  andi         x23, x21, 7
    1d8: 003ada93  srli         x21, x21, 3
    1dc: 00ba9a93  slli         x21, x21, 11
    1e0: 014a8ab3  add          x21, x21, x20
    1e4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000001e4
    1e8: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000214
    1ec: 00012eb7  lui          x29, 0x00012  # x29 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1f0: 9cce8e93  addi         x29, x29, -1588  # x29 = 0x000119cc
    1f4: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x000119cc
    1f8: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    1fc: 03cd8db3  mul          x27, x27, x28
    200: 01bb0b33  add          x22, x22, x27
    204: 001b9b93  slli         x23, x23, 1
    208: 017b0b33  add          x22, x22, x23
    20c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    210: 00008067  jalr         x0, 0(x1)
    214: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    218: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    21c: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    220: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    224: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    228: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    22c: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    230: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    234: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    238: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    23c: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    240: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_244:
    244: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    248: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    24c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    250: 000a0463  beq          x20, x0, 0x00000258  # target 0x00000258
    254: ff1ff06f  jal          x0, 0x00000244  # target 0x00000244
loc_258:
    258: 0ff0000f  fence        0xf, 0xf
    25c: 00008067  jalr         x0, 0(x1)
loc_260:
    260: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    264: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    268: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    26c: 000a0463  beq          x20, x0, 0x00000274  # target 0x00000274
    270: ff1ff06f  jal          x0, 0x00000260  # target 0x00000260
loc_274:
    274: 0ff0000f  fence        0xf, 0xf
    278: 00008067  jalr         x0, 0(x1)
loc_27c:
    27c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    280: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    284: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    288: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    28c: 015a6463  bltu         x20, x21, 0x00000294  # target 0x00000294
    290: fedff06f  jal          x0, 0x0000027c  # target 0x0000027c
loc_294:
    294: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    298: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    29c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    2a0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2a4: 015a6463  bltu         x20, x21, 0x000002ac  # target 0x000002ac
    2a8: fedff06f  jal          x0, 0x00000294  # target 0x00000294
loc_2ac:
    2ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2b0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    2b4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    2b8: 014a1a13  slli         x20, x20, 20
    2bc: 014a5a13  srli         x20, x20, 20
    2c0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_2c4:
    2c4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    2c8: 000b0463  beq          x22, x0, 0x000002d0  # target 0x000002d0
    2cc: ff9ff06f  jal          x0, 0x000002c4  # target 0x000002c4
loc_2d0:
    2d0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    2d4: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    2d8: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    2dc: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    2e0: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    2e4: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    2e8: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    2ec: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    2f0: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    2f4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    2f8: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    2fc: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    300: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    304: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    308: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    30c: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    310: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    314: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    318: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    31c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    320: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    324: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_328:
    328: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    32c: 000b0463  beq          x22, x0, 0x00000334  # target 0x00000334
    330: ff9ff06f  jal          x0, 0x00000328  # target 0x00000328
loc_334:
    334: 00008067  jalr         x0, 0(x1)
    338:           j FW_NCRISC+4   # return to firmware, linked at install
