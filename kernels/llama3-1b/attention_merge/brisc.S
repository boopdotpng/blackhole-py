# llama3 1b decode: attention_merge, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (8): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9
# params: 0x780=attention_partial_tiles, 0x784=e2e_context, 0x788=kv_blocks, 0xea40=merge_head
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
      4: 87830313  addi         x6, x6, -1928  # x6 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
      c: 00732023  sw           x7, 0(x6)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0000f000
     10: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
     14: 87c30313  addi         x6, x6, -1924  # x6 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00032023  sw           x0, 0(x6)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: 78800413  addi         x8, x0, 1928  # x8 = 0x00000788
     20: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000788
     24: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     28: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     2c: 0063fa63  bgeu         x7, x6, 0x00000040  # target 0x00000040
     30: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     34: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     38: 0063f463  bgeu         x7, x6, 0x00000040  # target 0x00000040
     3c: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_40:
     40: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     44: a4030313  addi         x6, x6, -1472  # x6 = 0x0000ea40
     48: 00032203  lw           x4, 0(x6)  # param merge_head; 0x0000ea40
     4c: 03000313  addi         x6, x0, 48  # x6 = 0x00000030
     50: 02620233  mul          x4, x4, x6
     54: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     58: 87c58593  addi         x11, x11, -1924  # x11 = 0xffb0087c · riscv_local_mem + 0x87c
     5c: 0005a303  lw           x6, 0(x11)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_60:
     60: ffb485b7  lui          x11, 0xffb48  # x11 = 0xffb48000
     64: 02058593  addi         x11, x11, 32  # x11 = 0xffb48020
     68: 0005d383  lhu          x7, 0(x11)  # 0xffb48020
     6c: 40730433  sub          x8, x6, x7
     70: 01041413  slli         x8, x8, 16
     74: 01045413  srli         x8, x8, 16
     78: 00800493  addi         x9, x0, 8  # x9 = 0x00000008
     7c: 408484b3  sub          x9, x9, x8
     80: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
     84: 00a4f663  bgeu         x9, x10, 0x00000090  # target 0x00000090
     88: 0ff0000f  fence        0xf, 0xf
     8c: fd5ff06f  jal          x0, 0x00000060  # target 0x00000060
loc_90:
     90: 0ff0000f  fence        0xf, 0xf
     94: 2f4000ef  jal          x1, 0x00000388  # target 0x00000388; x1 = 0x00000098
     98: 30c000ef  jal          x1, 0x000003a4  # target 0x000003a4; x1 = 0x0000009c
     9c: 00020313  addi         x6, x4, 0
     a0: 00030f93  addi         x31, x6, 0
     a4: 31c000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x000000a8
     a8: 000a8393  addi         x7, x21, 0
     ac: 000b0413  addi         x8, x22, 0
     b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     b4: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
     b8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
     bc: 00038f93  addi         x31, x7, 0
     c0: 00040f13  addi         x30, x8, 0
     c4: 00048e93  addi         x29, x9, 0
     c8: 344000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x000000cc
     cc: 00120313  addi         x6, x4, 1
     d0: 00030f93  addi         x31, x6, 0
     d4: 2ec000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x000000d8
     d8: 000a8393  addi         x7, x21, 0
     dc: 000b0413  addi         x8, x22, 0
     e0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     e4: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
     e8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
     ec: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     f0: 00a484b3  add          x9, x9, x10
     f4: 00038f93  addi         x31, x7, 0
     f8: 00040f13  addi         x30, x8, 0
     fc: 00048e93  addi         x29, x9, 0
    100: 30c000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x00000104
    104: 00220313  addi         x6, x4, 2
    108: 00030f93  addi         x31, x6, 0
    10c: 2b4000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x00000110
    110: 000a8393  addi         x7, x21, 0
    114: 000b0413  addi         x8, x22, 0
    118: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    11c: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    120: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    124: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    128: 00a484b3  add          x9, x9, x10
    12c: 00038f93  addi         x31, x7, 0
    130: 00040f13  addi         x30, x8, 0
    134: 00048e93  addi         x29, x9, 0
    138: 2d4000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x0000013c
    13c: 00320313  addi         x6, x4, 3
    140: 00030f93  addi         x31, x6, 0
    144: 27c000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x00000148
    148: 000a8393  addi         x7, x21, 0
    14c: 000b0413  addi         x8, x22, 0
    150: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    154: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    158: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    15c: 00003537  lui          x10, 0x00003  # x10 = 0x00003000
    160: 00a484b3  add          x9, x9, x10
    164: 00038f93  addi         x31, x7, 0
    168: 00040f13  addi         x30, x8, 0
    16c: 00048e93  addi         x29, x9, 0
    170: 29c000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x00000174
    174: 230000ef  jal          x1, 0x000003a4  # target 0x000003a4; x1 = 0x00000178
    178: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    17c: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    180: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878
    184: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    188: 00730333  add          x6, x6, x7
    18c: 00017437  lui          x8, 0x00017  # x8 = 0x00017000
    190: 00836663  bltu         x6, x8, 0x0000019c  # target 0x0000019c
    194: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    198: 40930333  sub          x6, x6, x9
loc_19c:
    19c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    1a0: 87850513  addi         x10, x10, -1928  # x10 = 0xffb00878 · riscv_local_mem + 0x878
    1a4: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    1a8: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    1ac: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    1b0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c
    1b4: 00430313  addi         x6, x6, 4
    1b8: 01031313  slli         x6, x6, 16
    1bc: 01035313  srli         x6, x6, 16
    1c0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    1c4: 87c38393  addi         x7, x7, -1924  # x7 = 0xffb0087c · riscv_local_mem + 0x87c
    1c8: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    1cc: ffb483b7  lui          x7, 0xffb48  # x7 = 0xffb48000
    1d0: 02838393  addi         x7, x7, 40  # x7 = 0xffb48028
    1d4: 0063a023  sw           x6, 0(x7)  # 0xffb48028; write runtime value
    1d8: 0ff0000f  fence        0xf, 0xf
    1dc: 00420213  addi         x4, x4, 4
    1e0: fff28293  addi         x5, x5, -1
    1e4: 00000313  addi         x6, x0, 0  # x6 = 0x00000000
    1e8: 00028393  addi         x7, x5, 0
loc_1ec:
    1ec: 18737c63  bgeu         x6, x7, 0x00000384  # target 0x00000384
    1f0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    1f4: 87c68693  addi         x13, x13, -1924  # x13 = 0xffb0087c · riscv_local_mem + 0x87c
    1f8: 0006a403  lw           x8, 0(x13)  # riscv_local_mem + 0x87c · 0xffb0087c
loc_1fc:
    1fc: ffb486b7  lui          x13, 0xffb48  # x13 = 0xffb48000
    200: 02068693  addi         x13, x13, 32  # x13 = 0xffb48020
    204: 0006d483  lhu          x9, 0(x13)  # 0xffb48020
    208: 40940533  sub          x10, x8, x9
    20c: 01051513  slli         x10, x10, 16
    210: 01055513  srli         x10, x10, 16
    214: 00800593  addi         x11, x0, 8  # x11 = 0x00000008
    218: 40a585b3  sub          x11, x11, x10
    21c: 00400613  addi         x12, x0, 4  # x12 = 0x00000004
    220: 00c5f663  bgeu         x11, x12, 0x0000022c  # target 0x0000022c
    224: 0ff0000f  fence        0xf, 0xf
    228: fd5ff06f  jal          x0, 0x000001fc  # target 0x000001fc
loc_22c:
    22c: 0ff0000f  fence        0xf, 0xf
    230: 158000ef  jal          x1, 0x00000388  # target 0x00000388; x1 = 0x00000234
    234: 170000ef  jal          x1, 0x000003a4  # target 0x000003a4; x1 = 0x00000238
    238: 00220413  addi         x8, x4, 2
    23c: 00040f93  addi         x31, x8, 0
    240: 180000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x00000244
    244: 000a8493  addi         x9, x21, 0
    248: 000b0513  addi         x10, x22, 0
    24c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    250: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    254: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    258: 00048f93  addi         x31, x9, 0
    25c: 00050f13  addi         x30, x10, 0
    260: 00058e93  addi         x29, x11, 0
    264: 1a8000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x00000268
    268: 00320413  addi         x8, x4, 3
    26c: 00040f93  addi         x31, x8, 0
    270: 150000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x00000274
    274: 000a8493  addi         x9, x21, 0
    278: 000b0513  addi         x10, x22, 0
    27c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    280: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    284: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    288: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    28c: 00c585b3  add          x11, x11, x12
    290: 00048f93  addi         x31, x9, 0
    294: 00050f13  addi         x30, x10, 0
    298: 00058e93  addi         x29, x11, 0
    29c: 170000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x000002a0
    2a0: 00020413  addi         x8, x4, 0
    2a4: 00040f93  addi         x31, x8, 0
    2a8: 118000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x000002ac
    2ac: 000a8493  addi         x9, x21, 0
    2b0: 000b0513  addi         x10, x22, 0
    2b4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    2b8: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    2bc: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    2c0: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    2c4: 00c585b3  add          x11, x11, x12
    2c8: 00048f93  addi         x31, x9, 0
    2cc: 00050f13  addi         x30, x10, 0
    2d0: 00058e93  addi         x29, x11, 0
    2d4: 138000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x000002d8
    2d8: 00120413  addi         x8, x4, 1
    2dc: 00040f93  addi         x31, x8, 0
    2e0: 0e0000ef  jal          x1, 0x000003c0  # target 0x000003c0; x1 = 0x000002e4
    2e4: 000a8493  addi         x9, x21, 0
    2e8: 000b0513  addi         x10, x22, 0
    2ec: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    2f0: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    2f4: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    2f8: 00003637  lui          x12, 0x00003  # x12 = 0x00003000
    2fc: 00c585b3  add          x11, x11, x12
    300: 00048f93  addi         x31, x9, 0
    304: 00050f13  addi         x30, x10, 0
    308: 00058e93  addi         x29, x11, 0
    30c: 100000ef  jal          x1, 0x0000040c  # target 0x0000040c; x1 = 0x00000310
    310: 094000ef  jal          x1, 0x000003a4  # target 0x000003a4; x1 = 0x00000314
    314: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    318: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    31c: 00062403  lw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878
    320: 000044b7  lui          x9, 0x00004  # x9 = 0x00004000
    324: 00940433  add          x8, x8, x9
    328: 00017537  lui          x10, 0x00017  # x10 = 0x00017000
    32c: 00a46663  bltu         x8, x10, 0x00000338  # target 0x00000338
    330: 000085b7  lui          x11, 0x00008  # x11 = 0x00008000
    334: 40b40433  sub          x8, x8, x11
loc_338:
    338: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    33c: 87860613  addi         x12, x12, -1928  # x12 = 0xffb00878 · riscv_local_mem + 0x878
    340: 00862023  sw           x8, 0(x12)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    344: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    348: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    34c: 0004a403  lw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c
    350: 00440413  addi         x8, x8, 4
    354: 01041413  slli         x8, x8, 16
    358: 01045413  srli         x8, x8, 16
    35c: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
    360: 87c48493  addi         x9, x9, -1924  # x9 = 0xffb0087c · riscv_local_mem + 0x87c
    364: 0084a023  sw           x8, 0(x9)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    368: ffb484b7  lui          x9, 0xffb48  # x9 = 0xffb48000
    36c: 02848493  addi         x9, x9, 40  # x9 = 0xffb48028
    370: 0084a023  sw           x8, 0(x9)  # 0xffb48028; write runtime value
    374: 0ff0000f  fence        0xf, 0xf
    378: 00420213  addi         x4, x4, 4
    37c: 00130313  addi         x6, x6, 1
    380: e6dff06f  jal          x0, 0x000001ec  # target 0x000001ec
loc_384:
    384: 1280006f  jal          x0, 0x000004ac  # target 0x000004ac
loc_388:
    388: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    38c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    390: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    394: 000a0463  beq          x20, x0, 0x0000039c  # target 0x0000039c
    398: ff1ff06f  jal          x0, 0x00000388  # target 0x00000388
loc_39c:
    39c: 0ff0000f  fence        0xf, 0xf
    3a0: 00008067  jalr         x0, 0(x1)
loc_3a4:
    3a4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    3a8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    3ac: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    3b0: 000a0463  beq          x20, x0, 0x000003b8  # target 0x000003b8
    3b4: ff1ff06f  jal          x0, 0x000003a4  # target 0x000003a4
loc_3b8:
    3b8: 0ff0000f  fence        0xf, 0xf
    3bc: 00008067  jalr         x0, 0(x1)
loc_3c0:
    3c0: 78000a93  addi         x21, x0, 1920  # x21 = 0x00000780
    3c4: 000aaa03  lw           x20, 0(x21)  # param attention_partial_tiles; 0x00000780
    3c8: 007a7d13  andi         x26, x20, 7
    3cc: ff8a7a13  andi         x20, x20, -8
    3d0: 01af8ab3  add          x21, x31, x26
    3d4: 007afb93  andi         x23, x21, 7
    3d8: 003ada93  srli         x21, x21, 3
    3dc: 00ca9a93  slli         x21, x21, 12
    3e0: 014a8ab3  add          x21, x21, x20
    3e4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000003e4
    3e8: 018b0b13  addi         x22, x22, 24  # x22 = 0x000003fc
    3ec: 001b9b93  slli         x23, x23, 1
    3f0: 017b0b33  add          x22, x22, x23
    3f4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    3f8: 00008067  jalr         x0, 0(x1)
    3fc: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    400: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    404: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    408: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_40c:
    40c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    410: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    414: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    418: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    41c: 015a6463  bltu         x20, x21, 0x00000424  # target 0x00000424
    420: fedff06f  jal          x0, 0x0000040c  # target 0x0000040c
loc_424:
    424: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    428: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    42c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    430: 014a1a13  slli         x20, x20, 20
    434: 014a5a13  srli         x20, x20, 20
    438: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_43c:
    43c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    440: 000b0463  beq          x22, x0, 0x00000448  # target 0x00000448
    444: ff9ff06f  jal          x0, 0x0000043c  # target 0x0000043c
loc_448:
    448: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    44c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    450: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    454: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    458: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    45c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    460: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    464: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    468: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    46c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    470: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    474: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    478: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    47c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00001000
    480: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    484: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    488: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    48c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    490: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    494: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    498: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_49c:
    49c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    4a0: 000b0463  beq          x22, x0, 0x000004a8  # target 0x000004a8
    4a4: ff9ff06f  jal          x0, 0x0000049c  # target 0x0000049c
loc_4a8:
    4a8: 00008067  jalr         x0, 0(x1)
    4ac:           j FW_BRISC+4   # return to firmware, linked at install
