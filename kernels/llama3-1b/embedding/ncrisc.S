# llama3 1b decode: embedding, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
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
     28: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
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
     54: 0dc000ef  jal          x1, 0x00000130  # target 0x00000130; x1 = 0x00000058
     58: 0f4000ef  jal          x1, 0x0000014c  # target 0x0000014c; x1 = 0x0000005c
     5c: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
     60: 108000ef  jal          x1, 0x00000168  # target 0x00000168; x1 = 0x00000064
     64: 000a8213  addi         x4, x21, 0
     68: 000b0293  addi         x5, x22, 0
     6c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     70: 86438393  addi         x7, x7, -1948  # x7 = 0xffb00864 · riscv_local_mem + 0x864
     74: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x864 · 0xffb00864
     78: 00030f93  addi         x31, x6, 0
     7c: 00020f13  addi         x30, x4, 0
     80: 00028e93  addi         x29, x5, 0
     84: 130000ef  jal          x1, 0x000001b4  # target 0x000001b4; x1 = 0x00000088
     88: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
     8c: 0dc000ef  jal          x1, 0x00000168  # target 0x00000168; x1 = 0x00000090
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
     bc: 0f8000ef  jal          x1, 0x000001b4  # target 0x000001b4; x1 = 0x000000c0
     c0: 070000ef  jal          x1, 0x00000130  # target 0x00000130; x1 = 0x000000c4
     c4: 088000ef  jal          x1, 0x0000014c  # target 0x0000014c; x1 = 0x000000c8
     c8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     cc: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
     d0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
     d4: 00220213  addi         x4, x4, 2
     d8: 01021213  slli         x4, x4, 16
     dc: 01025213  srli         x4, x4, 16
     e0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
     e4: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
     e8: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
     ec: ffb482b7  lui          x5, 0xffb48  # x5 = 0xffb48000
     f0: 02028293  addi         x5, x5, 32  # x5 = 0xffb48020
     f4: 0042a023  sw           x4, 0(x5)  # 0xffb48020; write runtime value
     f8: 0ff0000f  fence        0xf, 0xf
     fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    100: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    104: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    108: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    10c: 00520233  add          x4, x4, x5
    110: 00011337  lui          x6, 0x00011  # x6 = 0x00011000
    114: 00626663  bltu         x4, x6, 0x00000120  # target 0x00000120
    118: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    11c: 40720233  sub          x4, x4, x7
loc_120:
    120: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    124: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    128: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    12c: 1440006f  jal          x0, 0x00000270  # target 0x00000270
loc_130:
    130: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    134: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    138: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    13c: 000a0463  beq          x20, x0, 0x00000144  # target 0x00000144
    140: ff1ff06f  jal          x0, 0x00000130  # target 0x00000130
loc_144:
    144: 0ff0000f  fence        0xf, 0xf
    148: 00008067  jalr         x0, 0(x1)
loc_14c:
    14c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    150: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    154: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    158: 000a0463  beq          x20, x0, 0x00000160  # target 0x00000160
    15c: ff1ff06f  jal          x0, 0x0000014c  # target 0x0000014c
loc_160:
    160: 0ff0000f  fence        0xf, 0xf
    164: 00008067  jalr         x0, 0(x1)
loc_168:
    168: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    16c: 000aaa03  lw           x20, 0(x21)  # param e2e_x_a; 0x00000788
    170: 007a7d13  andi         x26, x20, 7
    174: ff8a7a13  andi         x20, x20, -8
    178: 01af8ab3  add          x21, x31, x26
    17c: 007afb93  andi         x23, x21, 7
    180: 003ada93  srli         x21, x21, 3
    184: 00ba9a93  slli         x21, x21, 11
    188: 014a8ab3  add          x21, x21, x20
    18c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000018c
    190: 018b0b13  addi         x22, x22, 24  # x22 = 0x000001a4
    194: 001b9b93  slli         x23, x23, 1
    198: 017b0b33  add          x22, x22, x23
    19c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    1a0: 00008067  jalr         x0, 0(x1)
    1a4: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    1a8: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    1ac: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    1b0: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_1b4:
    1b4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1b8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    1bc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    1c0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    1c4: 015a6463  bltu         x20, x21, 0x000001cc  # target 0x000001cc
    1c8: fedff06f  jal          x0, 0x000001b4  # target 0x000001b4
loc_1cc:
    1cc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1d0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    1d4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    1d8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    1dc: 015a6463  bltu         x20, x21, 0x000001e4  # target 0x000001e4
    1e0: fedff06f  jal          x0, 0x000001cc  # target 0x000001cc
loc_1e4:
    1e4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    1e8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    1ec: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    1f0: 014a1a13  slli         x20, x20, 20
    1f4: 014a5a13  srli         x20, x20, 20
    1f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_1fc:
    1fc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    200: 000b0463  beq          x22, x0, 0x00000208  # target 0x00000208
    204: ff9ff06f  jal          x0, 0x000001fc  # target 0x000001fc
loc_208:
    208: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    20c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    210: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    214: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    218: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    21c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    220: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    224: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    228: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    22c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    230: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    234: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    238: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    23c: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    240: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    244: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    248: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    24c: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    250: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    254: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    258: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    25c: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_260:
    260: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    264: 000b0463  beq          x22, x0, 0x0000026c  # target 0x0000026c
    268: ff9ff06f  jal          x0, 0x00000260  # target 0x00000260
loc_26c:
    26c: 00008067  jalr         x0, 0(x1)
    270:           j FW_NCRISC+4   # return to firmware, linked at install
