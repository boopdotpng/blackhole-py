# llama3 8b-bf16 decode: lm, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (88): 1,2 2,2 3,2 4,2 5,2 6,2 7,2 10,2 11,2 12,2 13,2 1,3 2,3 3,3 4,3 5,3 6,3 7,3 10,3 11,3 12,3 13,3 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9
# params: 0x780=e2e_x_a_decode_token, 0x784=e2e_lm_weight, 0x788=e2e_final_norm, 0xe9c0=e2e_logits, 0xe9c4=e2e_lm_weight_row_start, 0xe9c8=e2e_lm_weight_rows, 0xe9cc=dram_port
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00013437  lui          x8, 0x00013  # x8 = 0x00013000
      c: fc040413  addi         x8, x8, -64  # x8 = 0x00012fc0
     10: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00012fc0
     14: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     18: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: 00016237  lui          x4, 0x00016  # x4 = 0x00016000
     24: fc020213  addi         x4, x4, -64  # x4 = 0x00015fc0
     28: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
loc_2c:
     2c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     30: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     34: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     38: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     3c: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     40: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     44: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     48: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     4c: 02020213  addi         x4, x4, 32
     50: ff828293  addi         x5, x5, -8
     54: fc029ce3  bne          x5, x0, 0x0000002c  # target 0x0000002c
     58: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     5c: 9c828293  addi         x5, x5, -1592  # x5 = 0x0000e9c8
     60: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x0000e9c8
     64: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     68: 00020313  addi         x6, x4, 0
loc_6c:
     6c: 0e62fc63  bgeu         x5, x6, 0x00000164  # target 0x00000164
     70: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     74: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     78: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     7c: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_80:
     80: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     84: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     88: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     8c: 407404b3  sub          x9, x8, x7
     90: 01049493  slli         x9, x9, 16
     94: 0104d493  srli         x9, x9, 16
     98: 00a4f663  bgeu         x9, x10, 0x000000a4  # target 0x000000a4
     9c: 0ff0000f  fence        0xf, 0xf
     a0: fe1ff06f  jal          x0, 0x00000080  # target 0x00000080
loc_a4:
     a4: 0ff0000f  fence        0xf, 0xf
     a8: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     ac: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     b0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     b4: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
     b8: 00f2f493  andi         x9, x5, 15
     bc: 00149493  slli         x9, x9, 1
     c0: 0102f593  andi         x11, x5, 16
     c4: 00559593  slli         x11, x11, 5
     c8: 00b4e4b3  or           x9, x9, x11
     cc: 1e02f593  andi         x11, x5, 480
     d0: 00b4e4b3  or           x9, x9, x11
     d4: 0092d593  srli         x11, x5, 9
     d8: 00a59593  slli         x11, x11, 10
     dc: 00b4e4b3  or           x9, x9, x11
     e0: 00016537  lui          x10, 0x00016  # x10 = 0x00016000
     e4: fc050513  addi         x10, x10, -64  # x10 = 0x00015fc0
     e8: 00950533  add          x10, x10, x9
     ec: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
     f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     f4: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     f8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     fc: 00138393  addi         x7, x7, 1
    100: 01039393  slli         x7, x7, 16
    104: 0103d393  srli         x7, x7, 16
    108: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    10c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    110: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    114: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    118: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    11c: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    120: 0ff0000f  fence        0xf, 0xf
    124: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    128: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    12c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    130: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    134: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    138: 008383b3  add          x7, x7, x8
    13c: 000144b7  lui          x9, 0x00014  # x9 = 0x00014000
    140: fc048493  addi         x9, x9, -64  # x9 = 0x00013fc0
    144: 0093e663  bltu         x7, x9, 0x00000150  # target 0x00000150
    148: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    14c: 40a383b3  sub          x7, x7, x10
loc_150:
    150: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    154: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    158: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    15c: 00128293  addi         x5, x5, 1
    160: f0dff06f  jal          x0, 0x0000006c  # target 0x0000006c
loc_164:
    164: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    168: 068000ef  jal          x1, 0x000001d0  # target 0x000001d0; x1 = 0x0000016c
    16c: 000a8213  addi         x4, x21, 0
    170: 000b0293  addi         x5, x22, 0
    174: 0e4000ef  jal          x1, 0x00000258  # target 0x00000258; x1 = 0x00000178
    178: 0fc000ef  jal          x1, 0x00000274  # target 0x00000274; x1 = 0x0000017c
    17c: 00016fb7  lui          x31, 0x00016  # x31 = 0x00016000
    180: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00015fc0
    184: 00020f13  addi         x30, x4, 0
    188: 00028e93  addi         x29, x5, 0
    18c: 104000ef  jal          x1, 0x00000290  # target 0x00000290; x1 = 0x00000190
    190: 0c8000ef  jal          x1, 0x00000258  # target 0x00000258; x1 = 0x00000194
    194: 0e0000ef  jal          x1, 0x00000274  # target 0x00000274; x1 = 0x00000198
    198: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    19c: 034000ef  jal          x1, 0x000001d0  # target 0x000001d0; x1 = 0x000001a0
    1a0: 000a8213  addi         x4, x21, 0
    1a4: 000b0293  addi         x5, x22, 0
    1a8: 0b0000ef  jal          x1, 0x00000258  # target 0x00000258; x1 = 0x000001ac
    1ac: 0c8000ef  jal          x1, 0x00000274  # target 0x00000274; x1 = 0x000001b0
    1b0: 00016fb7  lui          x31, 0x00016  # x31 = 0x00016000
    1b4: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x000167c0
    1b8: 00020f13  addi         x30, x4, 0
    1bc: 00028e93  addi         x29, x5, 0
    1c0: 0d0000ef  jal          x1, 0x00000290  # target 0x00000290; x1 = 0x000001c4
    1c4: 094000ef  jal          x1, 0x00000258  # target 0x00000258; x1 = 0x000001c8
    1c8: 0ac000ef  jal          x1, 0x00000274  # target 0x00000274; x1 = 0x000001cc
    1cc: 1800006f  jal          x0, 0x0000034c  # target 0x0000034c
loc_1d0:
    1d0: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    1d4: 9c0a8a93  addi         x21, x21, -1600  # x21 = 0x0000e9c0
    1d8: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x0000e9c0
    1dc: 007a7d13  andi         x26, x20, 7
    1e0: ff8a7a13  andi         x20, x20, -8
    1e4: 01af8ab3  add          x21, x31, x26
    1e8: 007afb93  andi         x23, x21, 7
    1ec: 003ada93  srli         x21, x21, 3
    1f0: 00ba9a93  slli         x21, x21, 11
    1f4: 014a8ab3  add          x21, x21, x20
    1f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000001f8
    1fc: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000228
    200: 0000feb7  lui          x29, 0x0000f  # x29 = 0x0000f000
    204: 9cce8e93  addi         x29, x29, -1588  # x29 = 0x0000e9cc
    208: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x0000e9cc
    20c: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    210: 03cd8db3  mul          x27, x27, x28
    214: 01bb0b33  add          x22, x22, x27
    218: 001b9b93  slli         x23, x23, 1
    21c: 017b0b33  add          x22, x22, x23
    220: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    224: 00008067  jalr         x0, 0(x1)
    228: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    22c: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    230: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    234: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    238: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    23c: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    240: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    244: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    248: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    24c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    250: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    254: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_258:
    258: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    25c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    260: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    264: 000a0463  beq          x20, x0, 0x0000026c  # target 0x0000026c
    268: ff1ff06f  jal          x0, 0x00000258  # target 0x00000258
loc_26c:
    26c: 0ff0000f  fence        0xf, 0xf
    270: 00008067  jalr         x0, 0(x1)
loc_274:
    274: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    278: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    27c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    280: 000a0463  beq          x20, x0, 0x00000288  # target 0x00000288
    284: ff1ff06f  jal          x0, 0x00000274  # target 0x00000274
loc_288:
    288: 0ff0000f  fence        0xf, 0xf
    28c: 00008067  jalr         x0, 0(x1)
loc_290:
    290: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    294: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    298: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    29c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2a0: 015a6463  bltu         x20, x21, 0x000002a8  # target 0x000002a8
    2a4: fedff06f  jal          x0, 0x00000290  # target 0x00000290
loc_2a8:
    2a8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2ac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    2b0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    2b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2b8: 015a6463  bltu         x20, x21, 0x000002c0  # target 0x000002c0
    2bc: fedff06f  jal          x0, 0x000002a8  # target 0x000002a8
loc_2c0:
    2c0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2c4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    2c8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    2cc: 014a1a13  slli         x20, x20, 20
    2d0: 014a5a13  srli         x20, x20, 20
    2d4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_2d8:
    2d8: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    2dc: 000b0463  beq          x22, x0, 0x000002e4  # target 0x000002e4
    2e0: ff9ff06f  jal          x0, 0x000002d8  # target 0x000002d8
loc_2e4:
    2e4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    2e8: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    2ec: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    2f0: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    2f4: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    2f8: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    2fc: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    300: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    304: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    308: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    30c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    310: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    314: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    318: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    31c: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    320: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    324: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    328: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    32c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    330: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    334: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    338: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_33c:
    33c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    340: 000b0463  beq          x22, x0, 0x00000348  # target 0x00000348
    344: ff9ff06f  jal          x0, 0x0000033c  # target 0x0000033c
loc_348:
    348: 00008067  jalr         x0, 0(x1)
    34c:           j FW_NCRISC+4   # return to firmware, linked at install
