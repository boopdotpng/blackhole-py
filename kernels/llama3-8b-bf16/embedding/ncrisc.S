# llama3 8b-bf16 decode: embedding, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (1): 1,2
# params: 0x780=e2e_token_history, 0x784=e2e_embedding_weight, 0x788=e2e_x_a, 0x78c=token_pos
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000102b7  lui          x5, 0x00010  # x5 = 0x00010000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00010000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     20: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     24: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     28: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_2c:
     2c: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
     30: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
     34: 00045283  lhu          x5, 0(x8)  # 0xffb48028
     38: 40428333  sub          x6, x5, x4
     3c: 01031313  slli         x6, x6, 16
     40: 01035313  srli         x6, x6, 16
     44: 00737663  bgeu         x6, x7, 0x00000050  # target 0x00000050
     48: 0ff0000f  fence        0xf, 0xf
     4c: fe1ff06f  jal          x0, 0x0000002c  # target 0x0000002c
loc_50:
     50: 0ff0000f  fence        0xf, 0xf
     54: 148000ef  jal          x1, 0x0000019c  # target 0x0000019c; x1 = 0x00000058
     58: 160000ef  jal          x1, 0x000001b8  # target 0x000001b8; x1 = 0x0000005c
     5c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     60: 174000ef  jal          x1, 0x000001d4  # target 0x000001d4; x1 = 0x00000064
     64: 000a8213  addi         x4, x21, 0
     68: 000b0293  addi         x5, x22, 0
     6c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     70: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     74: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     78: 00030f93  addi         x31, x6, 0
     7c: 00020f13  addi         x30, x4, 0
     80: 00028e93  addi         x29, x5, 0
     84: 19c000ef  jal          x1, 0x00000220  # target 0x00000220; x1 = 0x00000088
     88: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     8c: 148000ef  jal          x1, 0x000001d4  # target 0x000001d4; x1 = 0x00000090
     90: 000a8213  addi         x4, x21, 0
     94: 000b0293  addi         x5, x22, 0
     98: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     9c: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     a0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     a4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     a8: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
     ac: 00730333  add          x6, x6, x7
     b0: 00030f93  addi         x31, x6, 0
     b4: 00020f13  addi         x30, x4, 0
     b8: 00028e93  addi         x29, x5, 0
     bc: 164000ef  jal          x1, 0x00000220  # target 0x00000220; x1 = 0x000000c0
     c0: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     c4: 110000ef  jal          x1, 0x000001d4  # target 0x000001d4; x1 = 0x000000c8
     c8: 000a8213  addi         x4, x21, 0
     cc: 000b0293  addi         x5, x22, 0
     d0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     d4: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     d8: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     dc: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     e0: 00730333  add          x6, x6, x7
     e4: 00030f93  addi         x31, x6, 0
     e8: 00020f13  addi         x30, x4, 0
     ec: 00028e93  addi         x29, x5, 0
     f0: 130000ef  jal          x1, 0x00000220  # target 0x00000220; x1 = 0x000000f4
     f4: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     f8: 0dc000ef  jal          x1, 0x000001d4  # target 0x000001d4; x1 = 0x000000fc
     fc: 000a8213  addi         x4, x21, 0
    100: 000b0293  addi         x5, x22, 0
    104: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    108: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
    10c: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
    110: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    114: 80038393  addi         x7, x7, -2048  # x7 = 0x00001800
    118: 00730333  add          x6, x6, x7
    11c: 00030f93  addi         x31, x6, 0
    120: 00020f13  addi         x30, x4, 0
    124: 00028e93  addi         x29, x5, 0
    128: 0f8000ef  jal          x1, 0x00000220  # target 0x00000220; x1 = 0x0000012c
    12c: 070000ef  jal          x1, 0x0000019c  # target 0x0000019c; x1 = 0x00000130
    130: 088000ef  jal          x1, 0x000001b8  # target 0x000001b8; x1 = 0x00000134
    134: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    138: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    13c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    140: 00420213  addi         x4, x4, 4
    144: 01021213  slli         x4, x4, 16
    148: 01025213  srli         x4, x4, 16
    14c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    150: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    154: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    158: ffb482b7  lui          x5, 0xffb48  # x5 = 0xffb48000
    15c: 02028293  addi         x5, x5, 32  # x5 = 0xffb48020
    160: 0042a023  sw           x4, 0(x5)  # 0xffb48020; write runtime value
    164: 0ff0000f  fence        0xf, 0xf
    168: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    16c: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    170: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    174: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    178: 00520233  add          x4, x4, x5
    17c: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    180: 00626663  bltu         x4, x6, 0x0000018c  # target 0x0000018c
    184: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    188: 40720233  sub          x4, x4, x7
loc_18c:
    18c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    190: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    194: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    198: 1440006f  jal          x0, 0x000002dc  # target 0x000002dc
loc_19c:
    19c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1a0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    1a4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    1a8: 000a0463  beq          x20, x0, 0x000001b0  # target 0x000001b0
    1ac: ff1ff06f  jal          x0, 0x0000019c  # target 0x0000019c
loc_1b0:
    1b0: 0ff0000f  fence        0xf, 0xf
    1b4: 00008067  jalr         x0, 0(x1)
loc_1b8:
    1b8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1bc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    1c0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    1c4: 000a0463  beq          x20, x0, 0x000001cc  # target 0x000001cc
    1c8: ff1ff06f  jal          x0, 0x000001b8  # target 0x000001b8
loc_1cc:
    1cc: 0ff0000f  fence        0xf, 0xf
    1d0: 00008067  jalr         x0, 0(x1)
loc_1d4:
    1d4: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    1d8: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x00000788
    1dc: 007a7d13  andi         x26, x20, 7
    1e0: ff8a7a13  andi         x20, x20, -8
    1e4: 01af8ab3  add          x21, x31, x26
    1e8: 007afb93  andi         x23, x21, 7
    1ec: 003ada93  srli         x21, x21, 3
    1f0: 00ba9a93  slli         x21, x21, 11
    1f4: 014a8ab3  add          x21, x21, x20
    1f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000001f8
    1fc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000210
    200: 001b9b93  slli         x23, x23, 1
    204: 017b0b33  add          x22, x22, x23
    208: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    20c: 00008067  jalr         x0, 0(x1)
    210: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    214: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    218: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    21c: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_220:
    220: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    224: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    228: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    22c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    230: 015a6463  bltu         x20, x21, 0x00000238  # target 0x00000238
    234: fedff06f  jal          x0, 0x00000220  # target 0x00000220
loc_238:
    238: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    23c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    240: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    244: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    248: 015a6463  bltu         x20, x21, 0x00000250  # target 0x00000250
    24c: fedff06f  jal          x0, 0x00000238  # target 0x00000238
loc_250:
    250: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    254: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    258: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    25c: 014a1a13  slli         x20, x20, 20
    260: 014a5a13  srli         x20, x20, 20
    264: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_268:
    268: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    26c: 000b0463  beq          x22, x0, 0x00000274  # target 0x00000274
    270: ff9ff06f  jal          x0, 0x00000268  # target 0x00000268
loc_274:
    274: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    278: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    27c: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    280: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    284: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    288: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    28c: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    290: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    294: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    298: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    29c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    2a0: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    2a4: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2a8: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    2ac: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    2b0: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    2b4: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    2b8: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    2bc: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    2c0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    2c4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    2c8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_2cc:
    2cc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    2d0: 000b0463  beq          x22, x0, 0x000002d8  # target 0x000002d8
    2d4: ff9ff06f  jal          x0, 0x000002cc  # target 0x000002cc
loc_2d8:
    2d8: 00008067  jalr         x0, 0(x1)
    2dc:           j FW_NCRISC+4   # return to firmware, linked at install
