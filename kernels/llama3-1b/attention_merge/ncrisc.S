# llama3 1b decode: attention_merge, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000172b7  lui          x5, 0x00017  # x5 = 0x00017000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00017000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     20: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     24: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     28: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
loc_2c:
     2c: ffb49437  lui          x8, 0xffb49  # x8 = 0xffb49000
     30: 02840413  addi         x8, x8, 40  # x8 = 0xffb49028
     34: 00045283  lhu          x5, 0(x8)  # 0xffb49028
     38: 40428333  sub          x6, x5, x4
     3c: 01031313  slli         x6, x6, 16
     40: 01035313  srli         x6, x6, 16
     44: 00737663  bgeu         x6, x7, 0x00000050  # target 0x00000050
     48: 0ff0000f  fence        0xf, 0xf
     4c: fe1ff06f  jal          x0, 0x0000002c  # target 0x0000002c
loc_50:
     50: 0ff0000f  fence        0xf, 0xf
     54: 344000ef  jal          x1, 0x00000398  # target 0x00000398; x1 = 0x00000058
     58: 35c000ef  jal          x1, 0x000003b4  # target 0x000003b4; x1 = 0x0000005c
     5c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
     60: a4028293  addi         x5, x5, -1472  # x5 = 0x0000ea40
     64: 0002a203  lw           x4, 0(x5)  # param merge_head; 0x0000ea40
     68: 00821213  slli         x4, x4, 8
     6c: 00020293  addi         x5, x4, 0
     70: 00a2d313  srli         x6, x5, 10
     74: 00030f93  addi         x31, x6, 0
     78: 358000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x0000007c
     7c: 000a8393  addi         x7, x21, 0
     80: 000b0413  addi         x8, x22, 0
     84: 3ff2f293  andi         x5, x5, 1023
     88: 00129493  slli         x9, x5, 1
     8c: 007484b3  add          x9, x9, x7
     90: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
     94: 00048f13  addi         x30, x9, 0
     98: 00040e93  addi         x29, x8, 0
     9c: 380000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000000a0
     a0: 01028293  addi         x5, x5, 16
     a4: 00129493  slli         x9, x5, 1
     a8: 007484b3  add          x9, x9, x7
     ac: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
     b0: 200f8f93  addi         x31, x31, 512  # x31 = 0x00017200
     b4: 00048f13  addi         x30, x9, 0
     b8: 00040e93  addi         x29, x8, 0
     bc: 360000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000000c0
     c0: 02020293  addi         x5, x4, 32
     c4: 00a2d313  srli         x6, x5, 10
     c8: 00030f93  addi         x31, x6, 0
     cc: 304000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x000000d0
     d0: 000a8393  addi         x7, x21, 0
     d4: 000b0413  addi         x8, x22, 0
     d8: 3ff2f293  andi         x5, x5, 1023
     dc: 00129493  slli         x9, x5, 1
     e0: 007484b3  add          x9, x9, x7
     e4: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
     e8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00017800
     ec: 00048f13  addi         x30, x9, 0
     f0: 00040e93  addi         x29, x8, 0
     f4: 328000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000000f8
     f8: 01028293  addi         x5, x5, 16
     fc: 00129493  slli         x9, x5, 1
    100: 007484b3  add          x9, x9, x7
    104: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    108: a00f8f93  addi         x31, x31, -1536  # x31 = 0x00017a00
    10c: 00048f13  addi         x30, x9, 0
    110: 00040e93  addi         x29, x8, 0
    114: 308000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000118
    118: 04020293  addi         x5, x4, 64
    11c: 00a2d313  srli         x6, x5, 10
    120: 00030f93  addi         x31, x6, 0
    124: 2ac000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x00000128
    128: 000a8393  addi         x7, x21, 0
    12c: 000b0413  addi         x8, x22, 0
    130: 3ff2f293  andi         x5, x5, 1023
    134: 00129493  slli         x9, x5, 1
    138: 007484b3  add          x9, x9, x7
    13c: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    140: 020f8f93  addi         x31, x31, 32  # x31 = 0x00017020
    144: 00048f13  addi         x30, x9, 0
    148: 00040e93  addi         x29, x8, 0
    14c: 2d0000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000150
    150: 01028293  addi         x5, x5, 16
    154: 00129493  slli         x9, x5, 1
    158: 007484b3  add          x9, x9, x7
    15c: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    160: 220f8f93  addi         x31, x31, 544  # x31 = 0x00017220
    164: 00048f13  addi         x30, x9, 0
    168: 00040e93  addi         x29, x8, 0
    16c: 2b0000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000170
    170: 06020293  addi         x5, x4, 96
    174: 00a2d313  srli         x6, x5, 10
    178: 00030f93  addi         x31, x6, 0
    17c: 254000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x00000180
    180: 000a8393  addi         x7, x21, 0
    184: 000b0413  addi         x8, x22, 0
    188: 3ff2f293  andi         x5, x5, 1023
    18c: 00129493  slli         x9, x5, 1
    190: 007484b3  add          x9, x9, x7
    194: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    198: 820f8f93  addi         x31, x31, -2016  # x31 = 0x00017820
    19c: 00048f13  addi         x30, x9, 0
    1a0: 00040e93  addi         x29, x8, 0
    1a4: 278000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000001a8
    1a8: 01028293  addi         x5, x5, 16
    1ac: 00129493  slli         x9, x5, 1
    1b0: 007484b3  add          x9, x9, x7
    1b4: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    1b8: a20f8f93  addi         x31, x31, -1504  # x31 = 0x00017a20
    1bc: 00048f13  addi         x30, x9, 0
    1c0: 00040e93  addi         x29, x8, 0
    1c4: 258000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000001c8
    1c8: 08020293  addi         x5, x4, 128
    1cc: 00a2d313  srli         x6, x5, 10
    1d0: 00030f93  addi         x31, x6, 0
    1d4: 1fc000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x000001d8
    1d8: 000a8393  addi         x7, x21, 0
    1dc: 000b0413  addi         x8, x22, 0
    1e0: 3ff2f293  andi         x5, x5, 1023
    1e4: 00129493  slli         x9, x5, 1
    1e8: 007484b3  add          x9, x9, x7
    1ec: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    1f0: 040f8f93  addi         x31, x31, 64  # x31 = 0x00017040
    1f4: 00048f13  addi         x30, x9, 0
    1f8: 00040e93  addi         x29, x8, 0
    1fc: 220000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000200
    200: 01028293  addi         x5, x5, 16
    204: 00129493  slli         x9, x5, 1
    208: 007484b3  add          x9, x9, x7
    20c: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    210: 240f8f93  addi         x31, x31, 576  # x31 = 0x00017240
    214: 00048f13  addi         x30, x9, 0
    218: 00040e93  addi         x29, x8, 0
    21c: 200000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000220
    220: 0a020293  addi         x5, x4, 160
    224: 00a2d313  srli         x6, x5, 10
    228: 00030f93  addi         x31, x6, 0
    22c: 1a4000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x00000230
    230: 000a8393  addi         x7, x21, 0
    234: 000b0413  addi         x8, x22, 0
    238: 3ff2f293  andi         x5, x5, 1023
    23c: 00129493  slli         x9, x5, 1
    240: 007484b3  add          x9, x9, x7
    244: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    248: 840f8f93  addi         x31, x31, -1984  # x31 = 0x00017840
    24c: 00048f13  addi         x30, x9, 0
    250: 00040e93  addi         x29, x8, 0
    254: 1c8000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000258
    258: 01028293  addi         x5, x5, 16
    25c: 00129493  slli         x9, x5, 1
    260: 007484b3  add          x9, x9, x7
    264: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    268: a40f8f93  addi         x31, x31, -1472  # x31 = 0x00017a40
    26c: 00048f13  addi         x30, x9, 0
    270: 00040e93  addi         x29, x8, 0
    274: 1a8000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000278
    278: 0c020293  addi         x5, x4, 192
    27c: 00a2d313  srli         x6, x5, 10
    280: 00030f93  addi         x31, x6, 0
    284: 14c000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x00000288
    288: 000a8393  addi         x7, x21, 0
    28c: 000b0413  addi         x8, x22, 0
    290: 3ff2f293  andi         x5, x5, 1023
    294: 00129493  slli         x9, x5, 1
    298: 007484b3  add          x9, x9, x7
    29c: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    2a0: 060f8f93  addi         x31, x31, 96  # x31 = 0x00017060
    2a4: 00048f13  addi         x30, x9, 0
    2a8: 00040e93  addi         x29, x8, 0
    2ac: 170000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000002b0
    2b0: 01028293  addi         x5, x5, 16
    2b4: 00129493  slli         x9, x5, 1
    2b8: 007484b3  add          x9, x9, x7
    2bc: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    2c0: 260f8f93  addi         x31, x31, 608  # x31 = 0x00017260
    2c4: 00048f13  addi         x30, x9, 0
    2c8: 00040e93  addi         x29, x8, 0
    2cc: 150000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x000002d0
    2d0: 0e020293  addi         x5, x4, 224
    2d4: 00a2d313  srli         x6, x5, 10
    2d8: 00030f93  addi         x31, x6, 0
    2dc: 0f4000ef  jal          x1, 0x000003d0  # target 0x000003d0; x1 = 0x000002e0
    2e0: 000a8393  addi         x7, x21, 0
    2e4: 000b0413  addi         x8, x22, 0
    2e8: 3ff2f293  andi         x5, x5, 1023
    2ec: 00129493  slli         x9, x5, 1
    2f0: 007484b3  add          x9, x9, x7
    2f4: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    2f8: 860f8f93  addi         x31, x31, -1952  # x31 = 0x00017860
    2fc: 00048f13  addi         x30, x9, 0
    300: 00040e93  addi         x29, x8, 0
    304: 118000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000308
    308: 01028293  addi         x5, x5, 16
    30c: 00129493  slli         x9, x5, 1
    310: 007484b3  add          x9, x9, x7
    314: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    318: a60f8f93  addi         x31, x31, -1440  # x31 = 0x00017a60
    31c: 00048f13  addi         x30, x9, 0
    320: 00040e93  addi         x29, x8, 0
    324: 0f8000ef  jal          x1, 0x0000041c  # target 0x0000041c; x1 = 0x00000328
    328: 070000ef  jal          x1, 0x00000398  # target 0x00000398; x1 = 0x0000032c
    32c: 088000ef  jal          x1, 0x000003b4  # target 0x000003b4; x1 = 0x00000330
    330: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    334: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    338: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    33c: 00220213  addi         x4, x4, 2
    340: 01021213  slli         x4, x4, 16
    344: 01025213  srli         x4, x4, 16
    348: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    34c: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    350: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    354: ffb492b7  lui          x5, 0xffb49  # x5 = 0xffb49000
    358: 02028293  addi         x5, x5, 32  # x5 = 0xffb49020
    35c: 0042a023  sw           x4, 0(x5)  # 0xffb49020; write runtime value
    360: 0ff0000f  fence        0xf, 0xf
    364: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    368: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    36c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    370: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    374: 00520233  add          x4, x4, x5
    378: 00018337  lui          x6, 0x00018  # x6 = 0x00018000
    37c: 00626663  bltu         x4, x6, 0x00000388  # target 0x00000388
    380: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    384: 40720233  sub          x4, x4, x7
loc_388:
    388: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    38c: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    390: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    394: 1400006f  jal          x0, 0x000004d4  # target 0x000004d4
loc_398:
    398: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    39c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    3a0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    3a4: 000a0463  beq          x20, x0, 0x000003ac  # target 0x000003ac
    3a8: ff1ff06f  jal          x0, 0x00000398  # target 0x00000398
loc_3ac:
    3ac: 0ff0000f  fence        0xf, 0xf
    3b0: 00008067  jalr         x0, 0(x1)
loc_3b4:
    3b4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    3b8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    3bc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    3c0: 000a0463  beq          x20, x0, 0x000003c8  # target 0x000003c8
    3c4: ff1ff06f  jal          x0, 0x000003b4  # target 0x000003b4
loc_3c8:
    3c8: 0ff0000f  fence        0xf, 0xf
    3cc: 00008067  jalr         x0, 0(x1)
loc_3d0:
    3d0: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    3d4: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x00000784
    3d8: 007a7d13  andi         x26, x20, 7
    3dc: ff8a7a13  andi         x20, x20, -8
    3e0: 01af8ab3  add          x21, x31, x26
    3e4: 007afb93  andi         x23, x21, 7
    3e8: 003ada93  srli         x21, x21, 3
    3ec: 00ba9a93  slli         x21, x21, 11
    3f0: 014a8ab3  add          x21, x21, x20
    3f4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003f4
    3f8: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000040c
    3fc: 001b9b93  slli         x23, x23, 1
    400: 017b0b33  add          x22, x22, x23
    404: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    408: 00008067  jalr         x0, 0(x1)
    40c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    410: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    414: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    418: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_41c:
    41c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    420: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    424: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    428: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    42c: 015a6463  bltu         x20, x21, 0x00000434  # target 0x00000434
    430: fedff06f  jal          x0, 0x0000041c  # target 0x0000041c
loc_434:
    434: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    438: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    43c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    440: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    444: 015a6463  bltu         x20, x21, 0x0000044c  # target 0x0000044c
    448: fedff06f  jal          x0, 0x00000434  # target 0x00000434
loc_44c:
    44c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    450: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    454: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    458: 014a1a13  slli         x20, x20, 20
    45c: 014a5a13  srli         x20, x20, 20
    460: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_464:
    464: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    468: 000b0463  beq          x22, x0, 0x00000470  # target 0x00000470
    46c: ff9ff06f  jal          x0, 0x00000464  # target 0x00000464
loc_470:
    470: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    474: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    478: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    47c: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    480: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    484: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    488: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    48c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    490: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    494: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    498: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    49c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    4a0: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    4a4: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    4a8: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    4ac: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    4b0: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    4b4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    4b8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    4bc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    4c0: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_4c4:
    4c4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    4c8: 000b0463  beq          x22, x0, 0x000004d0  # target 0x000004d0
    4cc: ff9ff06f  jal          x0, 0x000004c4  # target 0x000004c4
loc_4d0:
    4d0: 00008067  jalr         x0, 0(x1)
    4d4:           j FW_NCRISC+4   # return to firmware, linked at install
