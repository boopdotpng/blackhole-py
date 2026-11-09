# llama3 8b-fp8 decode: lm, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,4 2,4 3,4 4,4 5,4 6,4 7,4 10,4 11,4 12,4 13,4 14,4 1,5 2,5 3,5 4,5 5,5 6,5 7,5 10,5 11,5 12,5 13,5 14,5 1,6 2,6 3,6 4,6 5,6 6,6 7,6 10,6 11,6 12,6 13,6 14,6 1,7 2,7 3,7 4,7 5,7 6,7 7,7 10,7 11,7 12,7 13,7 14,7 1,8 2,8 3,8 4,8 5,8 6,8 7,8 10,8 11,8 12,8 13,8 14,8 1,9 2,9 3,9 4,9 5,9 6,9 7,9 10,9 11,9 12,9 13,9 14,9 1,10 2,10 3,10 4,10 5,10 6,10 7,10 10,10 11,10 12,10 13,10 14,10 1,11 2,11 3,11 4,11 5,11 6,11 7,11 10,11 11,11 12,11 13,11 14,11
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_lm_weight, 0x7c8=e2e_final_norm, 0x7cc=e2e_lm_weight_rows, 0x8180=e2e_logits, 0x8184=e2e_lm_weight_row_start, 0x8188=dram_port
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
      4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
      8: 00094437  lui          x8, 0x00094  # x8 = 0x00094000
      c: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00094000
     10: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     14: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     18: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: 00097237  lui          x4, 0x00097  # x4 = 0x00097000
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
     50: 7cc00293  addi         x5, x0, 1996  # x5 = 0x000007cc
     54: 0002a203  lw           x4, 0(x5)  # param e2e_lm_weight_rows; 0x000007cc
     58: 00000293  addi         x5, x0, 0  # x5 = 0x00000000
     5c: 00020313  addi         x6, x4, 0
loc_60:
     60: 0e62f863  bgeu         x5, x6, 0x00000150  # target 0x00000150
     64: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     68: 86858593  addi         x11, x11, -1944  # x11 = 0xffb00868 · riscv_local_mem + 0x868
     6c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x868 · 0xffb00868
     70: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
loc_74:
     74: ffb495b7  lui          x11, 0xffb49  # x11 = 0xffb49000
     78: 02858593  addi         x11, x11, 40  # x11 = 0xffb49028
     7c: 0005d403  lhu          x8, 0(x11)  # 0xffb49028
     80: 407404b3  sub          x9, x8, x7
     84: 01049493  slli         x9, x9, 16
     88: 0104d493  srli         x9, x9, 16
     8c: 00a4f663  bgeu         x9, x10, 0x00000098  # target 0x00000098
     90: 0ff0000f  fence        0xf, 0xf
     94: fe1ff06f  jal          x0, 0x00000074  # target 0x00000074
loc_98:
     98: 0ff0000f  fence        0xf, 0xf
     9c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     a0: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
     a4: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
     a8: 0003d403  lhu          x8, 0(x7)  # Address depends on runtime register values
     ac: 00f2f493  andi         x9, x5, 15
     b0: 00149493  slli         x9, x9, 1
     b4: 0102f593  andi         x11, x5, 16
     b8: 00559593  slli         x11, x11, 5
     bc: 00b4e4b3  or           x9, x9, x11
     c0: 1e02f593  andi         x11, x5, 480
     c4: 00b4e4b3  or           x9, x9, x11
     c8: 0092d593  srli         x11, x5, 9
     cc: 00a59593  slli         x11, x11, 10
     d0: 00b4e4b3  or           x9, x9, x11
     d4: 00097537  lui          x10, 0x00097  # x10 = 0x00097000
     d8: 00950533  add          x10, x10, x9
     dc: 00851023  sh           x8, 0(x10)  # Address depends on runtime register values
     e0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     e4: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     e8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     ec: 00138393  addi         x7, x7, 1
     f0: 01039393  slli         x7, x7, 16
     f4: 0103d393  srli         x7, x7, 16
     f8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     fc: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    100: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    104: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
    108: 02040413  addi         x8, x8, 32  # x8 = 0xffb49020
    10c: 00742023  sw           x7, 0(x8)  # 0xffb49020; write runtime value
    110: 0ff0000f  fence        0xf, 0xf
    114: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    118: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    11c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864
    120: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    124: 80040413  addi         x8, x8, -2048  # x8 = 0x00000800
    128: 008383b3  add          x7, x7, x8
    12c: 000954b7  lui          x9, 0x00095  # x9 = 0x00095000
    130: 0093e663  bltu         x7, x9, 0x0000013c  # target 0x0000013c
    134: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    138: 40a383b3  sub          x7, x7, x10
loc_13c:
    13c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    140: 86458593  addi         x11, x11, -1948  # x11 = 0xffb00864 · riscv_local_mem + 0x864
    144: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    148: 00128293  addi         x5, x5, 1
    14c: f15ff06f  jal          x0, 0x00000060  # target 0x00000060
loc_150:
    150: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    154: 064000ef  jal          x1, 0x000001b8  # target 0x000001b8; x1 = 0x00000158
    158: 000a8213  addi         x4, x21, 0
    15c: 000b0293  addi         x5, x22, 0
    160: 0e0000ef  jal          x1, 0x00000240  # target 0x00000240; x1 = 0x00000164
    164: 0f8000ef  jal          x1, 0x0000025c  # target 0x0000025c; x1 = 0x00000168
    168: 00097fb7  lui          x31, 0x00097  # x31 = 0x00097000
    16c: 00020f13  addi         x30, x4, 0
    170: 00028e93  addi         x29, x5, 0
    174: 104000ef  jal          x1, 0x00000278  # target 0x00000278; x1 = 0x00000178
    178: 0c8000ef  jal          x1, 0x00000240  # target 0x00000240; x1 = 0x0000017c
    17c: 0e0000ef  jal          x1, 0x0000025c  # target 0x0000025c; x1 = 0x00000180
    180: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    184: 034000ef  jal          x1, 0x000001b8  # target 0x000001b8; x1 = 0x00000188
    188: 000a8213  addi         x4, x21, 0
    18c: 000b0293  addi         x5, x22, 0
    190: 0b0000ef  jal          x1, 0x00000240  # target 0x00000240; x1 = 0x00000194
    194: 0c8000ef  jal          x1, 0x0000025c  # target 0x0000025c; x1 = 0x00000198
    198: 00098fb7  lui          x31, 0x00098  # x31 = 0x00098000
    19c: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00097800
    1a0: 00020f13  addi         x30, x4, 0
    1a4: 00028e93  addi         x29, x5, 0
    1a8: 0d0000ef  jal          x1, 0x00000278  # target 0x00000278; x1 = 0x000001ac
    1ac: 094000ef  jal          x1, 0x00000240  # target 0x00000240; x1 = 0x000001b0
    1b0: 0ac000ef  jal          x1, 0x0000025c  # target 0x0000025c; x1 = 0x000001b4
    1b4: 1800006f  jal          x0, 0x00000334  # target 0x00000334
loc_1b8:
    1b8: 00008ab7  lui          x21, 0x00008  # x21 = 0x00008000
    1bc: 180a8a93  addi         x21, x21, 384  # x21 = 0x00008180
    1c0: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x00008180
    1c4: 007a7d13  andi         x26, x20, 7
    1c8: ff8a7a13  andi         x20, x20, -8
    1cc: 01af8ab3  add          x21, x31, x26
    1d0: 007afb93  andi         x23, x21, 7
    1d4: 003ada93  srli         x21, x21, 3
    1d8: 00ba9a93  slli         x21, x21, 11
    1dc: 014a8ab3  add          x21, x21, x20
    1e0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000001e0
    1e4: 030b0b13  addi         x22, x22, 48  # x22 = 0x00000210
    1e8: 00008eb7  lui          x29, 0x00008  # x29 = 0x00008000
    1ec: 188e8e93  addi         x29, x29, 392  # x29 = 0x00008188
    1f0: 000ead83  lw           x27, 0(x29)  # param dram_port; 0x00008188
    1f4: 01000e13  addi         x28, x0, 16  # x28 = 0x00000010
    1f8: 03cd8db3  mul          x27, x27, x28
    1fc: 01bb0b33  add          x22, x22, x27
    200: 001b9b93  slli         x23, x23, 1
    204: 017b0b33  add          x22, x22, x23
    208: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    20c: 00008067  jalr         x0, 0(x1)
    210: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    214: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    218: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    21c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    220: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    224: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    228: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    22c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    230: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    234: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    238: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    23c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_240:
    240: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    244: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    248: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    24c: 000a0463  beq          x20, x0, 0x00000254  # target 0x00000254
    250: ff1ff06f  jal          x0, 0x00000240  # target 0x00000240
loc_254:
    254: 0ff0000f  fence        0xf, 0xf
    258: 00008067  jalr         x0, 0(x1)
loc_25c:
    25c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    260: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    264: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    268: 000a0463  beq          x20, x0, 0x00000270  # target 0x00000270
    26c: ff1ff06f  jal          x0, 0x0000025c  # target 0x0000025c
loc_270:
    270: 0ff0000f  fence        0xf, 0xf
    274: 00008067  jalr         x0, 0(x1)
loc_278:
    278: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    27c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    280: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    284: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    288: 015a6463  bltu         x20, x21, 0x00000290  # target 0x00000290
    28c: fedff06f  jal          x0, 0x00000278  # target 0x00000278
loc_290:
    290: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    294: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    298: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    29c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    2a0: 015a6463  bltu         x20, x21, 0x000002a8  # target 0x000002a8
    2a4: fedff06f  jal          x0, 0x00000290  # target 0x00000290
loc_2a8:
    2a8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    2ac: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    2b0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    2b4: 014a1a13  slli         x20, x20, 20
    2b8: 014a5a13  srli         x20, x20, 20
    2bc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_2c0:
    2c0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    2c4: 000b0463  beq          x22, x0, 0x000002cc  # target 0x000002cc
    2c8: ff9ff06f  jal          x0, 0x000002c0  # target 0x000002c0
loc_2cc:
    2cc: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    2d0: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    2d4: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    2d8: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    2dc: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    2e0: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    2e4: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    2e8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    2ec: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    2f0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    2f4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    2f8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    2fc: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    300: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    304: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    308: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    30c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    310: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    314: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    318: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    31c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    320: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_324:
    324: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    328: 000b0463  beq          x22, x0, 0x00000330  # target 0x00000330
    32c: ff9ff06f  jal          x0, 0x00000324  # target 0x00000324
loc_330:
    330: 00008067  jalr         x0, 0(x1)
    334:           j FW_NCRISC+4   # return to firmware, linked at install
