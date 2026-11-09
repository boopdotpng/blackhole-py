# llama3 1B decode: lm, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (16): 12,5 1,6 4,6 7,6 12,6 1,7 4,7 7,7 12,7 1,8 4,8 7,8 12,8 1,9 4,9 7,9
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_lm_weight, 0x7c8=e2e_final_norm, 0x8180=e2e_logits, 0x8184=e2e_lm_weight_row_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000952b7  lui          x5, 0x00095  # x5 = 0x00095000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00095000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     20: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
     24: 000904b7  lui          x9, 0x00090  # x9 = 0x00090000
     28: 00942023  sw           x9, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00090000
     2c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     30: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
     34: 00042023  sw           x0, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     38: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     3c: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
     40: 0004a203  lw           x4, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_44:
     44: ffb4c4b7  lui          x9, 0xffb4c  # x9 = 0xffb4c000
     48: 02048493  addi         x9, x9, 32  # x9 = 0xffb4c020
     4c: 0004d283  lhu          x5, 0(x9)  # 0xffb4c020
     50: 40520333  sub          x6, x4, x5
     54: 01031313  slli         x6, x6, 16
     58: 01035313  srli         x6, x6, 16
     5c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     60: 406383b3  sub          x7, x7, x6
     64: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
     68: 0083f663  bgeu         x7, x8, 0x00000074  # target 0x00000074
     6c: 0ff0000f  fence        0xf, 0xf
     70: fd5ff06f  jal          x0, 0x00000044  # target 0x00000044
loc_74:
     74: 0ff0000f  fence        0xf, 0xf
     78: 218000ef  jal          x1, 0x00000290  # target 0x00000290; x1 = 0x0000007c
     7c: 230000ef  jal          x1, 0x000002ac  # target 0x000002ac; x1 = 0x00000080
     80: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     84: 244000ef  jal          x1, 0x000002c8  # target 0x000002c8; x1 = 0x00000088
     88: 000a8213  addi         x4, x21, 0
     8c: 000b0293  addi         x5, x22, 0
     90: 00020f93  addi         x31, x4, 0
     94: 00028f13  addi         x30, x5, 0
     98: 00095eb7  lui          x29, 0x00095  # x29 = 0x00095000
     9c: 278000ef  jal          x1, 0x00000314  # target 0x00000314; x1 = 0x000000a0
     a0: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     a4: 224000ef  jal          x1, 0x000002c8  # target 0x000002c8; x1 = 0x000000a8
     a8: 000a8213  addi         x4, x21, 0
     ac: 000b0293  addi         x5, x22, 0
     b0: 00020f93  addi         x31, x4, 0
     b4: 00028f13  addi         x30, x5, 0
     b8: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     bc: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00095800
     c0: 254000ef  jal          x1, 0x00000314  # target 0x00000314; x1 = 0x000000c4
     c4: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     c8: 2f0000ef  jal          x1, 0x000003b8  # target 0x000003b8; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: 00020f93  addi         x31, x4, 0
     d8: 00028f13  addi         x30, x5, 0
     dc: 00096eb7  lui          x29, 0x00096  # x29 = 0x00096000
     e0: 234000ef  jal          x1, 0x00000314  # target 0x00000314; x1 = 0x000000e4
     e4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     e8: 2d0000ef  jal          x1, 0x000003b8  # target 0x000003b8; x1 = 0x000000ec
     ec: 000a8213  addi         x4, x21, 0
     f0: 000b0293  addi         x5, x22, 0
     f4: 00020f93  addi         x31, x4, 0
     f8: 00028f13  addi         x30, x5, 0
     fc: 00097eb7  lui          x29, 0x00097  # x29 = 0x00097000
    100: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00096800
    104: 210000ef  jal          x1, 0x00000314  # target 0x00000314; x1 = 0x00000108
    108: 1a4000ef  jal          x1, 0x000002ac  # target 0x000002ac; x1 = 0x0000010c
    10c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    110: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    114: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    118: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    11c: 00520233  add          x4, x4, x5
    120: 00097337  lui          x6, 0x00097  # x6 = 0x00097000
    124: 00626663  bltu         x4, x6, 0x00000130  # target 0x00000130
    128: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    12c: 40720233  sub          x4, x4, x7
loc_130:
    130: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    134: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    138: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    13c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    140: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    144: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    148: 00420213  addi         x4, x4, 4
    14c: 01021213  slli         x4, x4, 16
    150: 01025213  srli         x4, x4, 16
    154: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    158: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    15c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    160: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    164: 02828293  addi         x5, x5, 40  # x5 = 0xffb4c028
    168: 0042a023  sw           x4, 0(x5)  # 0xffb4c028; write runtime value
    16c: 0ff0000f  fence        0xf, 0xf
    170: 7c400313  addi         x6, x0, 1988  # x6 = 0x000007c4
    174: 00032203  lw           x4, 0(x6)  # param e2e_lm_weight; 0x000007c4
    178: ff827213  andi         x4, x4, -8
    17c: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    180: 18440413  addi         x8, x8, 388  # x8 = 0x00008184
    184: 00042303  lw           x6, 0(x8)  # param e2e_lm_weight_row_start; 0x00008184
    188: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
    18c: 02730333  mul          x6, x6, x7
    190: 00737293  andi         x5, x6, 7
    194: 00335313  srli         x6, x6, 3
    198: 00b31313  slli         x6, x6, 11
    19c: 00620233  add          x4, x4, x6
    1a0: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    1a4: 5b100393  addi         x7, x0, 1457  # x7 = 0x000005b1
loc_1a8:
    1a8: 0e737263  bgeu         x6, x7, 0x0000028c  # target 0x0000028c
    1ac: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1b0: 88468693  addi         x13, x13, -1916  # x13 = 0xffb00884 · riscv_local_mem + 0x884
    1b4: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x884 · 0xffb00884
loc_1b8:
    1b8: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    1bc: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    1c0: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    1c4: 40940533  sub          x10, x8, x9
    1c8: 01051513  slli         x10, x10, 16
    1cc: 01055513  srli         x10, x10, 16
    1d0: 00400593  addi         x11, x0, 4  # x11 = 0x00000004
    1d4: 40a585b3  sub          x11, x11, x10
    1d8: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    1dc: 00c5f663  bgeu         x11, x12, 0x000001e8  # target 0x000001e8
    1e0: 0ff0000f  fence        0xf, 0xf
    1e4: fd5ff06f  jal          x0, 0x000001b8  # target 0x000001b8
loc_1e8:
    1e8: 0ff0000f  fence        0xf, 0xf
    1ec: 0a4000ef  jal          x1, 0x00000290  # target 0x00000290; x1 = 0x000001f0
    1f0: 0bc000ef  jal          x1, 0x000002ac  # target 0x000002ac; x1 = 0x000001f4
    1f4: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    1f8: 88048493  addi         x9, x9, -1920  # x9 = 0xffb00880 · riscv_local_mem + 0x880
    1fc: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x880 · 0xffb00880
    200: 00020f93  addi         x31, x4, 0
    204: 00028f13  addi         x30, x5, 0
    208: 00040e93  addi         x29, x8, 0
    20c: 00200e13  addi         x28, x0, 2  # x28 = 0x00000002
    210: 1f4000ef  jal          x1, 0x00000404  # target 0x00000404; x1 = 0x00000214
    214: 000f8213  addi         x4, x31, 0
    218: 000f0293  addi         x5, x30, 0
    21c: 090000ef  jal          x1, 0x000002ac  # target 0x000002ac; x1 = 0x00000220
    220: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    224: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    228: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    22c: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    230: 00940433  add          x8, x8, x9
    234: 00092537  lui          x10, 0x00092  # x10 = 0x00092000
    238: 00a46663  bltu         x8, x10, 0x00000244  # target 0x00000244
    23c: 000025b7  lui          x11, 0x00002  # x11 = 0x00002000
    240: 40b40433  sub          x8, x8, x11
loc_244:
    244: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    248: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    24c: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    250: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    254: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    258: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884
    25c: 00240413  addi         x8, x8, 2
    260: 01041413  slli         x8, x8, 16
    264: 01045413  srli         x8, x8, 16
    268: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    26c: 88448493  addi         x9, x9, -1916  # x9 = 0xffb00884 · riscv_local_mem + 0x884
    270: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    274: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    278: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    27c: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    280: 0ff0000f  fence        0xf, 0xf
    284: 00130313  addi         x6, x6, 1
    288: f21ff06f  jal          x0, 0x000001a8  # target 0x000001a8
loc_28c:
    28c: 2680006f  jal          x0, 0x000004f4  # target 0x000004f4
loc_290:
    290: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    294: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    298: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    29c: 000a0463  beq          x20, x0, 0x000002a4  # target 0x000002a4
    2a0: ff1ff06f  jal          x0, 0x00000290  # target 0x00000290
loc_2a4:
    2a4: 0ff0000f  fence        0xf, 0xf
    2a8: 00008067  jalr         x0, 0(x1)
loc_2ac:
    2ac: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    2b0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    2b4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    2b8: 000a0463  beq          x20, x0, 0x000002c0  # target 0x000002c0
    2bc: ff1ff06f  jal          x0, 0x000002ac  # target 0x000002ac
loc_2c0:
    2c0: 0ff0000f  fence        0xf, 0xf
    2c4: 00008067  jalr         x0, 0(x1)
loc_2c8:
    2c8: 7c000a93  addi         x21, x0, 1984  # x21 = 0x000007c0
    2cc: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a_decode_token; 0x000007c0
    2d0: 007a7d13  andi         x26, x20, 7
    2d4: ff8a7a13  andi         x20, x20, -8
    2d8: 01af8ab3  add          x21, x31, x26
    2dc: 007afb93  andi         x23, x21, 7
    2e0: 003ada93  srli         x21, x21, 3
    2e4: 00ba9a93  slli         x21, x21, 11
    2e8: 014a8ab3  add          x21, x21, x20
    2ec: 00000b17  auipc        x22, 0x00000  # x22 = 0x000002ec
    2f0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000304
    2f4: 001b9b93  slli         x23, x23, 1
    2f8: 017b0b33  add          x22, x22, x23
    2fc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    300: 00008067  jalr         x0, 0(x1)
    304: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    308: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    30c: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    310: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_314:
    314: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    318: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    31c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    320: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    324: 015a6463  bltu         x20, x21, 0x0000032c  # target 0x0000032c
    328: fedff06f  jal          x0, 0x00000314  # target 0x00000314
loc_32c:
    32c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    330: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    334: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    338: 014a1a13  slli         x20, x20, 20
    33c: 014a5a13  srli         x20, x20, 20
    340: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_344:
    344: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    348: 000b0463  beq          x22, x0, 0x00000350  # target 0x00000350
    34c: ff9ff06f  jal          x0, 0x00000344  # target 0x00000344
loc_350:
    350: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    354: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    358: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    35c: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    360: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    364: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    368: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    36c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    370: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    374: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    378: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    37c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    380: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    384: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    388: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    38c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    390: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    394: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    398: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    39c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    3a0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    3a4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_3a8:
    3a8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    3ac: 000b0463  beq          x22, x0, 0x000003b4  # target 0x000003b4
    3b0: ff9ff06f  jal          x0, 0x000003a8  # target 0x000003a8
loc_3b4:
    3b4: 00008067  jalr         x0, 0(x1)
loc_3b8:
    3b8: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    3bc: 000aaa03  lw           x20, 0(x21)  # param e2e_final_norm; 0x000007c8
    3c0: 007a7d13  andi         x26, x20, 7
    3c4: ff8a7a13  andi         x20, x20, -8
    3c8: 01af8ab3  add          x21, x31, x26
    3cc: 007afb93  andi         x23, x21, 7
    3d0: 003ada93  srli         x21, x21, 3
    3d4: 00ba9a93  slli         x21, x21, 11
    3d8: 014a8ab3  add          x21, x21, x20
    3dc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003dc
    3e0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000003f4
    3e4: 001b9b93  slli         x23, x23, 1
    3e8: 017b0b33  add          x22, x22, x23
    3ec: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3f0: 00008067  jalr         x0, 0(x1)
    3f4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3f8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    3fc: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    400: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_404:
    404: 00000a17  auipc        x20, 0x00000  # x20 = 0x00000404
    408: 0e0a0a13  addi         x20, x20, 224  # x20 = 0x000004e4
loc_40c:
    40c: 001f1a93  slli         x21, x30, 1
    410: 014a8ab3  add          x21, x21, x20
    414: 000ada83  lhu          x21, 0(x21)  # Address depends on runtime register values
loc_418:
    418: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    41c: 244c0c13  addi         x24, x24, 580  # x24 = 0xffb20244 · noc0_regs + 0x244
    420: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x244 · 0xffb20244
    424: 08100c13  addi         x24, x0, 129  # x24 = 0x00000081
    428: 018be463  bltu         x23, x24, 0x00000430  # target 0x00000430
    42c: fedff06f  jal          x0, 0x00000418  # target 0x00000418
loc_430:
    430: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
    434: 148c0c13  addi         x24, x24, 328  # x24 = 0xffb20148 · noc0_regs + 0x148
    438: 000c2b83  lw           x23, 0(x24)  # noc0_regs + 0x148 · 0xffb20148
    43c: 014b9b93  slli         x23, x23, 20
    440: 014bdb93  srli         x23, x23, 20
    444: ffb20c37  lui          x24, 0xffb20  # x24 = 0xffb20000 · noc0_regs + 0x0
loc_448:
    448: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    44c: 000c8463  beq          x25, x0, 0x00000454  # target 0x00000454
    450: ff9ff06f  jal          x0, 0x00000448  # target 0x00000448
loc_454:
    454: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    458: 01fd2023  sw           x31, 0(x26)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    45c: 000d2223  sw           x0, 4(x26)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    460: 015d2423  sw           x21, 8(x26)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    464: 01dd2623  sw           x29, 12(x26)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    468: 000d2823  sw           x0, 16(x26)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    46c: 017d2a23  sw           x23, 20(x26)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    470: 40000d93  addi         x27, x0, 1024  # x27 = 0x00000400
    474: 01bd2c23  sw           x27, 24(x26)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    478: 00002db7  lui          x27, 0x00002  # x27 = 0x00002000
    47c: 090d8d93  addi         x27, x27, 144  # x27 = 0x00002090
    480: 01bd2e23  sw           x27, 28(x26)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    484: 00001db7  lui          x27, 0x00001  # x27 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    488: 800d8d93  addi         x27, x27, -2048  # x27 = 0x00000800
    48c: 03bd2023  sw           x27, 32(x26)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    490: 020d2223  sw           x0, 36(x26)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    494: 020d2423  sw           x0, 40(x26)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    498: 020d2623  sw           x0, 44(x26)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    49c: ffb20d37  lui          x26, 0xffb20  # x26 = 0xffb20000 · noc0_regs + 0x0
    4a0: 040d0d13  addi         x26, x26, 64  # x26 = 0xffb20040 · noc0_regs + 0x40
    4a4: 00100d93  addi         x27, x0, 1  # x27 = 0x00000001
    4a8: 01bd2023  sw           x27, 0(x26)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_4ac:
    4ac: 040c2c83  lw           x25, 64(x24)  # noc0_regs + 0x40 · 0xffb20040
    4b0: 000c8463  beq          x25, x0, 0x000004b8  # target 0x000004b8
    4b4: ff9ff06f  jal          x0, 0x000004ac  # target 0x000004ac
loc_4b8:
    4b8: 00001b37  lui          x22, 0x00001  # x22 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4bc: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00000800
    4c0: 016e8eb3  add          x29, x29, x22
    4c4: 001f0f13  addi         x30, x30, 1
    4c8: 00800a93  addi         x21, x0, 8  # x21 = 0x00000008
    4cc: 015f1663  bne          x30, x21, 0x000004d8  # target 0x000004d8
    4d0: 00000f13  addi         x30, x0, 0  # x30 = 0x00000000
    4d4: 016f8fb3  add          x31, x31, x22
loc_4d8:
    4d8: fffe0e13  addi         x28, x28, -1
    4dc: f20e18e3  bne          x28, x0, 0x0000040c  # target 0x0000040c
    4e0: 00008067  jalr         x0, 0(x1)
    4e4: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4e8: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    4ec: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    4f0: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    4f4:           j FW_BRISC+4   # return to firmware, linked at install
