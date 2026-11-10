# llama3 8b-fp8 decode: embedding, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (1): 1,4
# params: 0x780=e2e_token_history, 0x784=e2e_embedding_weight, 0x788=e2e_x_a, 0x78c=token_pos
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000102b7  lui          x5, 0x00010  # x5 = 0x00010000
      c: 04028293  addi         x5, x5, 64  # x5 = 0x00010040
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00010040
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     24: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     28: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     2c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_30:
     30: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
     34: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
     38: 00045283  lhu          x5, 0(x8)  # 0xffb48028
     3c: 40428333  sub          x6, x5, x4
     40: 01031313  slli         x6, x6, 16
     44: 01035313  srli         x6, x6, 16
     48: 00737663  bgeu         x6, x7, 0x00000054  # target 0x00000054
     4c: 0ff0000f  fence        0xf, 0xf
     50: fe1ff06f  jal          x0, 0x00000030  # target 0x00000030
loc_54:
     54: 0ff0000f  fence        0xf, 0xf
     58: 14c000ef  jal          x1, 0x000001a4  # target 0x000001a4; x1 = 0x0000005c
     5c: 164000ef  jal          x1, 0x000001c0  # target 0x000001c0; x1 = 0x00000060
     60: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     64: 178000ef  jal          x1, 0x000001dc  # target 0x000001dc; x1 = 0x00000068
     68: 000a8213  addi         x4, x21, 0
     6c: 000b0293  addi         x5, x22, 0
     70: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     74: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     78: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     7c: 00030f93  addi         x31, x6, 0
     80: 00020f13  addi         x30, x4, 0
     84: 00028e93  addi         x29, x5, 0
     88: 1a0000ef  jal          x1, 0x00000228  # target 0x00000228; x1 = 0x0000008c
     8c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     90: 14c000ef  jal          x1, 0x000001dc  # target 0x000001dc; x1 = 0x00000094
     94: 000a8213  addi         x4, x21, 0
     98: 000b0293  addi         x5, x22, 0
     9c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     a0: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     a4: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     a8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     ac: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
     b0: 00730333  add          x6, x6, x7
     b4: 00030f93  addi         x31, x6, 0
     b8: 00020f13  addi         x30, x4, 0
     bc: 00028e93  addi         x29, x5, 0
     c0: 168000ef  jal          x1, 0x00000228  # target 0x00000228; x1 = 0x000000c4
     c4: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
     c8: 114000ef  jal          x1, 0x000001dc  # target 0x000001dc; x1 = 0x000000cc
     cc: 000a8213  addi         x4, x21, 0
     d0: 000b0293  addi         x5, x22, 0
     d4: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     d8: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     dc: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     e0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     e4: 00730333  add          x6, x6, x7
     e8: 00030f93  addi         x31, x6, 0
     ec: 00020f13  addi         x30, x4, 0
     f0: 00028e93  addi         x29, x5, 0
     f4: 134000ef  jal          x1, 0x00000228  # target 0x00000228; x1 = 0x000000f8
     f8: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
     fc: 0e0000ef  jal          x1, 0x000001dc  # target 0x000001dc; x1 = 0x00000100
    100: 000a8213  addi         x4, x21, 0
    104: 000b0293  addi         x5, x22, 0
    108: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    10c: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
    110: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
    114: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    118: 80038393  addi         x7, x7, -2048  # x7 = 0x00001800
    11c: 00730333  add          x6, x6, x7
    120: 00030f93  addi         x31, x6, 0
    124: 00020f13  addi         x30, x4, 0
    128: 00028e93  addi         x29, x5, 0
    12c: 0fc000ef  jal          x1, 0x00000228  # target 0x00000228; x1 = 0x00000130
    130: 074000ef  jal          x1, 0x000001a4  # target 0x000001a4; x1 = 0x00000134
    134: 08c000ef  jal          x1, 0x000001c0  # target 0x000001c0; x1 = 0x00000138
    138: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    13c: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    140: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    144: 00420213  addi         x4, x4, 4
    148: 01021213  slli         x4, x4, 16
    14c: 01025213  srli         x4, x4, 16
    150: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    154: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    158: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    15c: ffb482b7  lui          x5, 0xffb48  # x5 = 0xffb48000
    160: 02028293  addi         x5, x5, 32  # x5 = 0xffb48020
    164: 0042a023  sw           x4, 0(x5)  # 0xffb48020; write runtime value
    168: 0ff0000f  fence        0xf, 0xf
    16c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    170: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    174: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    178: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    17c: 00520233  add          x4, x4, x5
    180: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    184: 04030313  addi         x6, x6, 64  # x6 = 0x00012040
    188: 00626663  bltu         x4, x6, 0x00000194  # target 0x00000194
    18c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    190: 40720233  sub          x4, x4, x7
loc_194:
    194: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    198: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    19c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    1a0: 1440006f  jal          x0, 0x000002e4  # target 0x000002e4
loc_1a4:
    1a4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1a8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    1ac: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    1b0: 000a0463  beq          x20, x0, 0x000001b8  # target 0x000001b8
    1b4: ff1ff06f  jal          x0, 0x000001a4  # target 0x000001a4
loc_1b8:
    1b8: 0ff0000f  fence        0xf, 0xf
    1bc: 00008067  jalr         x0, 0(x1)
loc_1c0:
    1c0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1c4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    1c8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    1cc: 000a0463  beq          x20, x0, 0x000001d4  # target 0x000001d4
    1d0: ff1ff06f  jal          x0, 0x000001c0  # target 0x000001c0
loc_1d4:
    1d4: 0ff0000f  fence        0xf, 0xf
    1d8: 00008067  jalr         x0, 0(x1)
loc_1dc:
    1dc: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    1e0: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x00000788
    1e4: 007a7d13  andi         x26, x20, 7
    1e8: ff8a7a13  andi         x20, x20, -8
    1ec: 01af8ab3  add          x21, x31, x26
    1f0: 007afb93  andi         x23, x21, 7
    1f4: 003ada93  srli         x21, x21, 3
    1f8: 00ba9a93  slli         x21, x21, 11
    1fc: 014a8ab3  add          x21, x21, x20
    200: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000200
    204: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000218
    208: 001b9b93  slli         x23, x23, 1
    20c: 017b0b33  add          x22, x22, x23
    210: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    214: 00008067  jalr         x0, 0(x1)
    218: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    21c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    220: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    224: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_228:
    228: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    22c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    230: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    234: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    238: 015a6463  bltu         x20, x21, 0x00000240  # target 0x00000240
    23c: fedff06f  jal          x0, 0x00000228  # target 0x00000228
loc_240:
    240: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    244: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    248: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    24c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    250: 015a6463  bltu         x20, x21, 0x00000258  # target 0x00000258
    254: fedff06f  jal          x0, 0x00000240  # target 0x00000240
loc_258:
    258: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    25c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    260: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    264: 014a1a13  slli         x20, x20, 20
    268: 014a5a13  srli         x20, x20, 20
    26c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_270:
    270: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    274: 000b0463  beq          x22, x0, 0x0000027c  # target 0x0000027c
    278: ff9ff06f  jal          x0, 0x00000270  # target 0x00000270
loc_27c:
    27c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    280: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    284: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    288: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    28c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    290: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    294: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    298: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    29c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    2a0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    2a4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    2a8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    2ac: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2b0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    2b4: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    2b8: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    2bc: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    2c0: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    2c4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    2c8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    2cc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    2d0: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_2d4:
    2d4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    2d8: 000b0463  beq          x22, x0, 0x000002e0  # target 0x000002e0
    2dc: ff9ff06f  jal          x0, 0x000002d4  # target 0x000002d4
loc_2e0:
    2e0: 00008067  jalr         x0, 0(x1)
    2e4:           j FW_NCRISC+4   # return to firmware, linked at install
