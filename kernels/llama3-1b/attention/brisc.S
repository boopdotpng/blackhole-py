# llama3 1b decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000192b7  lui          x5, 0x00019  # x5 = 0x00019000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00018800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00018800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     28: 0001b2b7  lui          x5, 0x0001b  # x5 = 0x0001b000
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0001b000
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     40: 88838393  addi         x7, x7, -1912  # x7 = 0xffb00888 · riscv_local_mem + 0x888
     44: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
     48: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x0000f000
     4c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     50: 88c38393  addi         x7, x7, -1908  # x7 = 0xffb0088c · riscv_local_mem + 0x88c
     54: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     58: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     5c: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
     60: 00010637  lui          x12, 0x00010  # x12 = 0x00010000
     64: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00010000
     68: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     6c: 89458593  addi         x11, x11, -1900  # x11 = 0xffb00894 · riscv_local_mem + 0x894
     70: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     74: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     78: 89858593  addi         x11, x11, -1896  # x11 = 0xffb00898 · riscv_local_mem + 0x898
     7c: 00012637  lui          x12, 0x00012  # x12 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     80: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00012000
     84: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     88: 89c58593  addi         x11, x11, -1892  # x11 = 0xffb0089c · riscv_local_mem + 0x89c
     8c: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
     90: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     94: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     98: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     9c: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     a0: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     a4: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     a8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     ac: 0063fa63  bgeu         x7, x6, 0x000000c0  # target 0x000000c0
     b0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     b4: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     b8: 0063f463  bgeu         x7, x6, 0x000000c0  # target 0x000000c0
     bc: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_c0:
     c0: 1a5270e3  bgeu         x4, x5, 0x00000a60  # target 0x00000a60
     c4: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     c8: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
     cc: 00425293  srli         x5, x4, 4
     d0: 00f27313  andi         x6, x4, 15
     d4: 00631313  slli         x6, x6, 6
     d8: 00131313  slli         x6, x6, 1
     dc: 189000ef  jal          x1, 0x00000a64  # target 0x00000a64; x1 = 0x000000e0
     e0: 1a1000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x000000e4
     e4: 00028f93  addi         x31, x5, 0
     e8: 1b5000ef  jal          x1, 0x00000a9c  # target 0x00000a9c; x1 = 0x000000ec
     ec: 000a8393  addi         x7, x21, 0
     f0: 000b0413  addi         x8, x22, 0
     f4: 00038f93  addi         x31, x7, 0
     f8: 00040f13  addi         x30, x8, 0
     fc: 00030eb7  lui          x29, 0x00030  # x29 = 0x00030000 · arc_apb_reset_unit + 0x0
    100: 1e9000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x00000104
    104: 00028f93  addi         x31, x5, 0
    108: 285000ef  jal          x1, 0x00000b8c  # target 0x00000b8c; x1 = 0x0000010c
    10c: 000a8393  addi         x7, x21, 0
    110: 000b0413  addi         x8, x22, 0
    114: 00038f93  addi         x31, x7, 0
    118: 00040f13  addi         x30, x8, 0
    11c: 00031eb7  lui          x29, 0x00031  # x29 = 0x00031000 · arc_apb_reset_unit + 0x1000
    120: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00030800 · arc_apb_reset_unit + 0x800
    124: 1c5000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x00000128
    128: 159000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x0000012c
    12c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    130: 90448493  addi         x9, x9, -1788  # x9 = 0x0000e904
    134: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e904
    138: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
    13c: 02945433  divu         x8, x8, x9
    140: 00841413  slli         x8, x8, 8
    144: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_148:
    148: 24000693  addi         x13, x0, 576  # x13 = 0x00000240
    14c: 00d47c63  bgeu         x8, x13, 0x00000164  # target 0x00000164
    150: 01800613  addi         x12, x0, 24  # x12 = 0x00000018
    154: 02c454b3  divu         x9, x8, x12
    158: 02c485b3  mul          x11, x9, x12
    15c: 40b405b3  sub          x11, x8, x11
    160: 01c0006f  jal          x0, 0x0000017c  # target 0x0000017c
loc_164:
    164: 40d406b3  sub          x13, x8, x13
    168: 01700613  addi         x12, x0, 23  # x12 = 0x00000017
    16c: 02c6d4b3  divu         x9, x13, x12
    170: 02c485b3  mul          x11, x9, x12
    174: 40b685b3  sub          x11, x13, x11
    178: 01848493  addi         x9, x9, 24
loc_17c:
    17c: 03f40513  addi         x10, x8, 63
    180: 24000793  addi         x15, x0, 576  # x15 = 0x00000240
    184: 00f57c63  bgeu         x10, x15, 0x0000019c  # target 0x0000019c
    188: 01800713  addi         x14, x0, 24  # x14 = 0x00000018
    18c: 02e55633  divu         x12, x10, x14
    190: 02e606b3  mul          x13, x12, x14
    194: 40d506b3  sub          x13, x10, x13
    198: 01c0006f  jal          x0, 0x000001b4  # target 0x000001b4
loc_19c:
    19c: 40f507b3  sub          x15, x10, x15
    1a0: 01700713  addi         x14, x0, 23  # x14 = 0x00000017
    1a4: 02e7d633  divu         x12, x15, x14
    1a8: 02e606b3  mul          x13, x12, x14
    1ac: 40d786b3  sub          x13, x15, x13
    1b0: 01860613  addi         x12, x12, 24
loc_1b4:
    1b4: 00048513  addi         x10, x9, 0
    1b8: 0ad000ef  jal          x1, 0x00000a64  # target 0x00000a64; x1 = 0x000001bc
    1bc: 0c5000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x000001c0
    1c0: 0001c737  lui          x14, 0x0001c  # x14 = 0x0001c000
    1c4: 80070713  addi         x14, x14, -2048  # x14 = 0x0001b800
loc_1c8:
    1c8: 00050f93  addi         x31, x10, 0
    1cc: 20d000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000001d0
    1d0: 000a8793  addi         x15, x21, 0
    1d4: 000b0813  addi         x16, x22, 0
    1d8: 00078f93  addi         x31, x15, 0
    1dc: 00080f13  addi         x30, x16, 0
    1e0: 00070e93  addi         x29, x14, 0
    1e4: 105000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x000001e8
    1e8: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1ec: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    1f0: 00f70733  add          x14, x14, x15
    1f4: 00150513  addi         x10, x10, 1
    1f8: fca678e3  bgeu         x12, x10, 0x000001c8  # target 0x000001c8
    1fc: 085000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x00000200
    200: 00048513  addi         x10, x9, 0
    204: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    208: 00739693  slli         x13, x7, 7
    20c: 00019737  lui          x14, 0x00019  # x14 = 0x00019000
    210: 80070713  addi         x14, x14, -2048  # x14 = 0x00018800
    214: 00e686b3  add          x13, x13, x14
loc_218:
    218: 01700713  addi         x14, x0, 23  # x14 = 0x00000017
    21c: 01800793  addi         x15, x0, 24  # x15 = 0x00000018
    220: 00f57463  bgeu         x10, x15, 0x00000228  # target 0x00000228
    224: 00170713  addi         x14, x14, 1  # x14 = 0x00000018
loc_228:
    228: 40b70733  sub          x14, x14, x11
    22c: 00f5f793  andi         x15, x11, 15
    230: 40f007b3  sub          x15, x0, x15
    234: 01078793  addi         x15, x15, 16
    238: 00e7f463  bgeu         x15, x14, 0x00000240  # target 0x00000240
    23c: 00078713  addi         x14, x15, 0
loc_240:
    240: 01f67793  andi         x15, x12, 31
    244: 40f007b3  sub          x15, x0, x15
    248: 02078793  addi         x15, x15, 32
    24c: 00e7f463  bgeu         x15, x14, 0x00000254  # target 0x00000254
    250: 00078713  addi         x14, x15, 0
loc_254:
    254: 40950833  sub          x16, x10, x9
    258: 00b81813  slli         x16, x16, 11
    25c: 00f5f793  andi         x15, x11, 15
    260: 00179793  slli         x15, x15, 1
    264: 0105fa13  andi         x20, x11, 16
    268: 005a1a13  slli         x20, x20, 5
    26c: 0147e7b3  or           x15, x15, x20
    270: 1e05fa13  andi         x20, x11, 480
    274: 0147e7b3  or           x15, x15, x20
    278: 0095da13  srli         x20, x11, 9
    27c: 00aa1a13  slli         x20, x20, 10
    280: 0147e7b3  or           x15, x15, x20
    284: 00f80833  add          x16, x16, x15
    288: 0001ca37  lui          x20, 0x0001c  # x20 = 0x0001c000
    28c: 800a0a13  addi         x20, x20, -2048  # x20 = 0x0001b800
    290: 01480833  add          x16, x16, x20
    294: 00161893  slli         x17, x12, 1
    298: 00d888b3  add          x17, x17, x13
    29c: 02064913  xori         x18, x12, 32
    2a0: 00191913  slli         x18, x18, 1
    2a4: 00d90933  add          x18, x18, x13
    2a8: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2ac: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2b0: 01490933  add          x18, x18, x20
    2b4: 02067993  andi         x19, x12, 32
    2b8: 00a99993  slli         x19, x19, 10
    2bc: 00080f93  addi         x31, x16, 0
    2c0: 00088f13  addi         x30, x17, 0
    2c4: 00090e93  addi         x29, x18, 0
    2c8: 00070e13  addi         x28, x14, 0
    2cc: 00098d93  addi         x27, x19, 0
loc_2d0:
    2d0: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2d4: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2d8: 01ba4a33  xor          x20, x20, x27
    2dc: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    2e0: 002f8f93  addi         x31, x31, 2
    2e4: 002f0f13  addi         x30, x30, 2
    2e8: 002e8e93  addi         x29, x29, 2
    2ec: fffe0e13  addi         x28, x28, -1
    2f0: fe0e10e3  bne          x28, x0, 0x000002d0  # target 0x000002d0
    2f4: 00e60633  add          x12, x12, x14
    2f8: 00e585b3  add          x11, x11, x14
    2fc: 01700793  addi         x15, x0, 23  # x15 = 0x00000017
    300: 01800993  addi         x19, x0, 24  # x19 = 0x00000018
    304: 01357463  bgeu         x10, x19, 0x0000030c  # target 0x0000030c
    308: 00178793  addi         x15, x15, 1  # x15 = 0x00000018
loc_30c:
    30c: 00f59663  bne          x11, x15, 0x00000318  # target 0x00000318
    310: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    314: 00150513  addi         x10, x10, 1
loc_318:
    318: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    31c: eef66ee3  bltu         x12, x15, 0x00000218  # target 0x00000218
    320: 04040413  addi         x8, x8, 64
    324: 00138393  addi         x7, x7, 1
    328: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    32c: e0939ee3  bne          x7, x9, 0x00000148  # target 0x00000148
    330: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    334: 90448493  addi         x9, x9, -1788  # x9 = 0x0000e904
    338: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e904
    33c: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
    340: 02945433  divu         x8, x8, x9
    344: 00045413  srli         x8, x8, 0
    348: 00641413  slli         x8, x8, 6
    34c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    350: 1b000693  addi         x13, x0, 432  # x13 = 0x000001b0
    354: 00d47c63  bgeu         x8, x13, 0x0000036c  # target 0x0000036c
    358: 00600613  addi         x12, x0, 6  # x12 = 0x00000006
    35c: 02c454b3  divu         x9, x8, x12
    360: 02c485b3  mul          x11, x9, x12
    364: 40b405b3  sub          x11, x8, x11
    368: 01c0006f  jal          x0, 0x00000384  # target 0x00000384
loc_36c:
    36c: 40d406b3  sub          x13, x8, x13
    370: 00500613  addi         x12, x0, 5  # x12 = 0x00000005
    374: 02c6d4b3  divu         x9, x13, x12
    378: 02c485b3  mul          x11, x9, x12
    37c: 40b685b3  sub          x11, x13, x11
    380: 04848493  addi         x9, x9, 72
loc_384:
    384: 03f40513  addi         x10, x8, 63
    388: 1b000793  addi         x15, x0, 432  # x15 = 0x000001b0
    38c: 00f57c63  bgeu         x10, x15, 0x000003a4  # target 0x000003a4
    390: 00600713  addi         x14, x0, 6  # x14 = 0x00000006
    394: 02e55633  divu         x12, x10, x14
    398: 02e606b3  mul          x13, x12, x14
    39c: 40d506b3  sub          x13, x10, x13
    3a0: 01c0006f  jal          x0, 0x000003bc  # target 0x000003bc
loc_3a4:
    3a4: 40f507b3  sub          x15, x10, x15
    3a8: 00500713  addi         x14, x0, 5  # x14 = 0x00000005
    3ac: 02e7d633  divu         x12, x15, x14
    3b0: 02e606b3  mul          x13, x12, x14
    3b4: 40d786b3  sub          x13, x15, x13
    3b8: 04860613  addi         x12, x12, 72
loc_3bc:
    3bc: 00048513  addi         x10, x9, 0
    3c0: 6a4000ef  jal          x1, 0x00000a64  # target 0x00000a64; x1 = 0x000003c4
    3c4: 6bc000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x000003c8
    3c8: 0001c737  lui          x14, 0x0001c  # x14 = 0x0001c000
    3cc: 80070713  addi         x14, x14, -2048  # x14 = 0x0001b800
loc_3d0:
    3d0: 00050f93  addi         x31, x10, 0
    3d4: 051000ef  jal          x1, 0x00000c24  # target 0x00000c24; x1 = 0x000003d8
    3d8: 000a8793  addi         x15, x21, 0
    3dc: 000b0813  addi         x16, x22, 0
    3e0: 00078f93  addi         x31, x15, 0
    3e4: 00080f13  addi         x30, x16, 0
    3e8: 00070e93  addi         x29, x14, 0
    3ec: 6fc000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x000003f0
    3f0: 00050f93  addi         x31, x10, 0
    3f4: 07d000ef  jal          x1, 0x00000c70  # target 0x00000c70; x1 = 0x000003f8
    3f8: 000a8793  addi         x15, x21, 0
    3fc: 000b0813  addi         x16, x22, 0
    400: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    404: 00e888b3  add          x17, x17, x14
    408: 00078f93  addi         x31, x15, 0
    40c: 00080f13  addi         x30, x16, 0
    410: 00088e93  addi         x29, x17, 0
    414: 6d4000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x00000418
    418: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    41c: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    420: 00f70733  add          x14, x14, x15
    424: 00150513  addi         x10, x10, 1
    428: faa674e3  bgeu         x12, x10, 0x000003d0  # target 0x000003d0
    42c: 654000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x00000430
    430: 00048513  addi         x10, x9, 0
    434: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    438: 00739693  slli         x13, x7, 7
    43c: 00019737  lui          x14, 0x00019  # x14 = 0x00019000
    440: 80070713  addi         x14, x14, -2048  # x14 = 0x00018800
    444: 00e686b3  add          x13, x13, x14
loc_448:
    448: 00500713  addi         x14, x0, 5  # x14 = 0x00000005
    44c: 04800793  addi         x15, x0, 72  # x15 = 0x00000048
    450: 00f57463  bgeu         x10, x15, 0x00000458  # target 0x00000458
    454: 00170713  addi         x14, x14, 1  # x14 = 0x00000006
loc_458:
    458: 40b70733  sub          x14, x14, x11
    45c: 00f5f793  andi         x15, x11, 15
    460: 40f007b3  sub          x15, x0, x15
    464: 01078793  addi         x15, x15, 16
    468: 00e7f463  bgeu         x15, x14, 0x00000470  # target 0x00000470
    46c: 00078713  addi         x14, x15, 0
loc_470:
    470: 01f67793  andi         x15, x12, 31
    474: 40f007b3  sub          x15, x0, x15
    478: 02078793  addi         x15, x15, 32
    47c: 00e7f463  bgeu         x15, x14, 0x00000484  # target 0x00000484
    480: 00078713  addi         x14, x15, 0
loc_484:
    484: 40950833  sub          x16, x10, x9
    488: 00b81813  slli         x16, x16, 11
    48c: 00f5f793  andi         x15, x11, 15
    490: 00179793  slli         x15, x15, 1
    494: 0105fa13  andi         x20, x11, 16
    498: 005a1a13  slli         x20, x20, 5
    49c: 0147e7b3  or           x15, x15, x20
    4a0: 1e05fa13  andi         x20, x11, 480
    4a4: 0147e7b3  or           x15, x15, x20
    4a8: 0095da13  srli         x20, x11, 9
    4ac: 00aa1a13  slli         x20, x20, 10
    4b0: 0147e7b3  or           x15, x15, x20
    4b4: 00f80833  add          x16, x16, x15
    4b8: 0001ca37  lui          x20, 0x0001c  # x20 = 0x0001c000
    4bc: 800a0a13  addi         x20, x20, -2048  # x20 = 0x0001b800
    4c0: 01480833  add          x16, x16, x20
    4c4: 00161893  slli         x17, x12, 1
    4c8: 00d888b3  add          x17, x17, x13
    4cc: 02064913  xori         x18, x12, 32
    4d0: 00191913  slli         x18, x18, 1
    4d4: 00d90933  add          x18, x18, x13
    4d8: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4dc: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4e0: 01490933  add          x18, x18, x20
    4e4: 02067993  andi         x19, x12, 32
    4e8: 00a99993  slli         x19, x19, 10
    4ec: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    4f0: 010a0a33  add          x20, x20, x16
    4f4: 00161a93  slli         x21, x12, 1
    4f8: 00030b37  lui          x22, 0x00030  # x22 = 0x00030000 · arc_apb_reset_unit + 0x0
    4fc: 800b0b13  addi         x22, x22, -2048  # x22 = 0x0002f800
    500: 016a8ab3  add          x21, x21, x22
    504: ffc10113  addi         x2, x2, -4
    508: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    50c: 00080f93  addi         x31, x16, 0
    510: 00088f13  addi         x30, x17, 0
    514: 00090e93  addi         x29, x18, 0
    518: 00070e13  addi         x28, x14, 0
    51c: 00098d93  addi         x27, x19, 0
    520: 000a0d13  addi         x26, x20, 0
    524: 000a8c93  addi         x25, x21, 0
loc_528:
    528: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    52c: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    530: 01ba4a33  xor          x20, x20, x27
    534: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    538: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    53c: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    540: 002d0d13  addi         x26, x26, 2
    544: 002c8c93  addi         x25, x25, 2
    548: 002f8f93  addi         x31, x31, 2
    54c: 002f0f13  addi         x30, x30, 2
    550: 002e8e93  addi         x29, x29, 2
    554: fffe0e13  addi         x28, x28, -1
    558: fc0e18e3  bne          x28, x0, 0x00000528  # target 0x00000528
    55c: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    560: 00410113  addi         x2, x2, 4
    564: 00e60633  add          x12, x12, x14
    568: 00e585b3  add          x11, x11, x14
    56c: 00500793  addi         x15, x0, 5  # x15 = 0x00000005
    570: 04800993  addi         x19, x0, 72  # x19 = 0x00000048
    574: 01357463  bgeu         x10, x19, 0x0000057c  # target 0x0000057c
    578: 00178793  addi         x15, x15, 1  # x15 = 0x00000006
loc_57c:
    57c: 00f59663  bne          x11, x15, 0x00000588  # target 0x00000588
    580: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    584: 00150513  addi         x10, x10, 1
loc_588:
    588: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    58c: eaf66ee3  bltu         x12, x15, 0x00000448  # target 0x00000448
    590: 000303b7  lui          x7, 0x00030  # x7 = 0x00030000 · arc_apb_reset_unit + 0x0
    594: 006383b3  add          x7, x7, x6
    598: 00038f93  addi         x31, x7, 0
    59c: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    5a0: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00019800
    5a4: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5a8: 714000ef  jal          x1, 0x00000cbc  # target 0x00000cbc; x1 = 0x000005ac
    5ac: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    5b0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00019800
    5b4: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    5b8: 880f0f13  addi         x30, x30, -1920  # x30 = 0x00019880
    5bc: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5c0: 750000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x000005c4
    5c4: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    5c8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00019800
    5cc: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    5d0: 900f0f13  addi         x30, x30, -1792  # x30 = 0x00019900
    5d4: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5d8: 738000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x000005dc
    5dc: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    5e0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00019800
    5e4: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    5e8: 980f0f13  addi         x30, x30, -1664  # x30 = 0x00019980
    5ec: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5f0: 720000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x000005f4
    5f4: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    5f8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00019800
    5fc: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    600: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00019a00
    604: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    608: 708000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x0000060c
    60c: 000313b7  lui          x7, 0x00031  # x7 = 0x00031000 · arc_apb_reset_unit + 0x1000
    610: 80038393  addi         x7, x7, -2048  # x7 = 0x00030800 · arc_apb_reset_unit + 0x800
    614: 006383b3  add          x7, x7, x6
    618: 00038f93  addi         x31, x7, 0
    61c: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    620: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    624: 698000ef  jal          x1, 0x00000cbc  # target 0x00000cbc; x1 = 0x00000628
    628: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    62c: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    630: 080f0f13  addi         x30, x30, 128  # x30 = 0x0001a080
    634: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    638: 6d8000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x0000063c
    63c: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    640: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    644: 100f0f13  addi         x30, x30, 256  # x30 = 0x0001a100
    648: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    64c: 6c4000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x00000650
    650: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    654: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    658: 180f0f13  addi         x30, x30, 384  # x30 = 0x0001a180
    65c: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    660: 6b0000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x00000664
    664: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    668: 0001af37  lui          x30, 0x0001a  # x30 = 0x0001a000
    66c: 200f0f13  addi         x30, x30, 512  # x30 = 0x0001a200
    670: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    674: 69c000ef  jal          x1, 0x00000d10  # target 0x00000d10; x1 = 0x00000678
    678: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    67c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    680: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    684: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    688: 00520233  add          x4, x4, x5
    68c: 0001b337  lui          x6, 0x0001b  # x6 = 0x0001b000
    690: 80030313  addi         x6, x6, -2048  # x6 = 0x0001a800
    694: 00626663  bltu         x4, x6, 0x000006a0  # target 0x000006a0
    698: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    69c: 40720233  sub          x4, x4, x7
loc_6a0:
    6a0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6a4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    6a8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    6ac: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6b0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    6b4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    6b8: 00420213  addi         x4, x4, 4
    6bc: 01021213  slli         x4, x4, 16
    6c0: 01025213  srli         x4, x4, 16
    6c4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6c8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    6cc: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    6d0: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    6d4: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    6d8: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    6dc: 0ff0000f  fence        0xf, 0xf
    6e0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6e4: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    6e8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    6ec: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_6f0:
    6f0: ffb4f437  lui          x8, 0xffb4f  # x8 = 0xffb4f000
    6f4: 02840413  addi         x8, x8, 40  # x8 = 0xffb4f028
    6f8: 00045283  lhu          x5, 0(x8)  # 0xffb4f028
    6fc: 40428333  sub          x6, x5, x4
    700: 01031313  slli         x6, x6, 16
    704: 01035313  srli         x6, x6, 16
    708: 00737663  bgeu         x6, x7, 0x00000714  # target 0x00000714
    70c: 0ff0000f  fence        0xf, 0xf
    710: fe1ff06f  jal          x0, 0x000006f0  # target 0x000006f0
loc_714:
    714: 0ff0000f  fence        0xf, 0xf
    718: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    71c: 90438393  addi         x7, x7, -1788  # x7 = 0x0000e904
    720: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x0000e904
    724: 00c00393  addi         x7, x0, 12  # x7 = 0x0000000c
    728: 02725233  divu         x4, x4, x7
    72c: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    730: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    734: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    738: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    73c: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    740: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    744: 00747a63  bgeu         x8, x7, 0x00000758  # target 0x00000758
    748: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    74c: 08000413  addi         x8, x0, 128  # x8 = 0x00000080
    750: 00747463  bgeu         x8, x7, 0x00000758  # target 0x00000758
    754: 00c00313  addi         x6, x0, 12  # x6 = 0x0000000c
loc_758:
    758: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    75c: 90848493  addi         x9, x9, -1784  # x9 = 0x0000e908
    760: 0004a383  lw           x7, 0(x9)  # param attention_phase; 0x0000e908
    764: 79000593  addi         x11, x0, 1936  # x11 = 0x00000790
    768: 0005a483  lw           x9, 0(x11)  # param kv_blocks; 0x00000790
    76c: 00100413  addi         x8, x0, 1  # x8 = 0x00000001
    770: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
    774: 00957a63  bgeu         x10, x9, 0x00000788  # target 0x00000788
    778: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    77c: 08000513  addi         x10, x0, 128  # x10 = 0x00000080
    780: 00957463  bgeu         x10, x9, 0x00000788  # target 0x00000788
    784: 00c00413  addi         x8, x0, 12  # x8 = 0x0000000c
loc_788:
    788: 008282b3  add          x5, x5, x8
    78c: fff28293  addi         x5, x5, -1
    790: 407282b3  sub          x5, x5, x7
    794: 0282d2b3  divu         x5, x5, x8
    798: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    79c: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7a0: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    7a4: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7a8: 008383b3  add          x7, x7, x8
    7ac: 000104b7  lui          x9, 0x00010  # x9 = 0x00010000
    7b0: 0093e663  bltu         x7, x9, 0x000007bc  # target 0x000007bc
    7b4: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7b8: 40a383b3  sub          x7, x7, x10
loc_7bc:
    7bc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    7c0: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7c4: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    7c8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7cc: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7d0: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    7d4: 00238393  addi         x7, x7, 2
    7d8: 01039393  slli         x7, x7, 16
    7dc: 0103d393  srli         x7, x7, 16
    7e0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7e4: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7e8: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    7ec: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    7f0: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    7f4: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    7f8: 0ff0000f  fence        0xf, 0xf
    7fc: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    800: 00028413  addi         x8, x5, 0
loc_804:
    804: 2483fe63  bgeu         x7, x8, 0x00000a60  # target 0x00000a60
    808: 00025493  srli         x9, x4, 0
    80c: 00949493  slli         x9, x9, 9
    810: 02638533  mul          x10, x7, x6
    814: 0000f637  lui          x12, 0x0000f  # x12 = 0x0000f000
    818: 90860613  addi         x12, x12, -1784  # x12 = 0x0000e908
    81c: 00062583  lw           x11, 0(x12)  # param attention_phase; 0x0000e908
    820: 00b50533  add          x10, x10, x11
    824: 00151513  slli         x10, x10, 1
    828: 00a484b3  add          x9, x9, x10
    82c: 238000ef  jal          x1, 0x00000a64  # target 0x00000a64; x1 = 0x00000830
    830: 250000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x00000834
    834: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    838: 89480813  addi         x16, x16, -1900  # x16 = 0xffb00894 · riscv_local_mem + 0x894
    83c: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x894 · 0xffb00894
loc_840:
    840: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    844: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    848: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    84c: 40c586b3  sub          x13, x11, x12
    850: 01069693  slli         x13, x13, 16
    854: 0106d693  srli         x13, x13, 16
    858: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    85c: 40d70733  sub          x14, x14, x13
    860: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    864: 00f77663  bgeu         x14, x15, 0x00000870  # target 0x00000870
    868: 0ff0000f  fence        0xf, 0xf
    86c: fd5ff06f  jal          x0, 0x00000840  # target 0x00000840
loc_870:
    870: 0ff0000f  fence        0xf, 0xf
    874: 00048593  addi         x11, x9, 0
    878: 00058f93  addi         x31, x11, 0
    87c: 4b0000ef  jal          x1, 0x00000d2c  # target 0x00000d2c; x1 = 0x00000880
    880: 000a8613  addi         x12, x21, 0
    884: 000b0693  addi         x13, x22, 0
    888: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    88c: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    890: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    894: 00060f93  addi         x31, x12, 0
    898: 00068f13  addi         x30, x13, 0
    89c: 00070e93  addi         x29, x14, 0
    8a0: 248000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x000008a4
    8a4: 00148593  addi         x11, x9, 1
    8a8: 00058f93  addi         x31, x11, 0
    8ac: 480000ef  jal          x1, 0x00000d2c  # target 0x00000d2c; x1 = 0x000008b0
    8b0: 000a8613  addi         x12, x21, 0
    8b4: 000b0693  addi         x13, x22, 0
    8b8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    8bc: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    8c0: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    8c4: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8c8: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    8cc: 00f70733  add          x14, x14, x15
    8d0: 00060f93  addi         x31, x12, 0
    8d4: 00068f13  addi         x30, x13, 0
    8d8: 00070e93  addi         x29, x14, 0
    8dc: 20c000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x000008e0
    8e0: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    8e4: 89c80813  addi         x16, x16, -1892  # x16 = 0xffb0089c · riscv_local_mem + 0x89c
    8e8: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_8ec:
    8ec: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    8f0: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    8f4: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    8f8: 40c586b3  sub          x13, x11, x12
    8fc: 01069693  slli         x13, x13, 16
    900: 0106d693  srli         x13, x13, 16
    904: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    908: 40d70733  sub          x14, x14, x13
    90c: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    910: 00f77663  bgeu         x14, x15, 0x0000091c  # target 0x0000091c
    914: 0ff0000f  fence        0xf, 0xf
    918: fd5ff06f  jal          x0, 0x000008ec  # target 0x000008ec
loc_91c:
    91c: 0ff0000f  fence        0xf, 0xf
    920: 00048593  addi         x11, x9, 0
    924: 00058f93  addi         x31, x11, 0
    928: 450000ef  jal          x1, 0x00000d78  # target 0x00000d78; x1 = 0x0000092c
    92c: 000a8613  addi         x12, x21, 0
    930: 000b0693  addi         x13, x22, 0
    934: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    938: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    93c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    940: 00060f93  addi         x31, x12, 0
    944: 00068f13  addi         x30, x13, 0
    948: 00070e93  addi         x29, x14, 0
    94c: 19c000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x00000950
    950: 00148593  addi         x11, x9, 1
    954: 00058f93  addi         x31, x11, 0
    958: 420000ef  jal          x1, 0x00000d78  # target 0x00000d78; x1 = 0x0000095c
    95c: 000a8613  addi         x12, x21, 0
    960: 000b0693  addi         x13, x22, 0
    964: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    968: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    96c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    970: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    974: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    978: 00f70733  add          x14, x14, x15
    97c: 00060f93  addi         x31, x12, 0
    980: 00068f13  addi         x30, x13, 0
    984: 00070e93  addi         x29, x14, 0
    988: 160000ef  jal          x1, 0x00000ae8  # target 0x00000ae8; x1 = 0x0000098c
    98c: 0f4000ef  jal          x1, 0x00000a80  # target 0x00000a80; x1 = 0x00000990
    990: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    994: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    998: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    99c: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9a0: 00c585b3  add          x11, x11, x12
    9a4: 000126b7  lui          x13, 0x00012  # x13 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    9a8: 00d5e663  bltu         x11, x13, 0x000009b4  # target 0x000009b4
    9ac: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    9b0: 40e585b3  sub          x11, x11, x14
loc_9b4:
    9b4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9b8: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    9bc: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    9c0: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    9c4: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    9c8: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
    9cc: 00258593  addi         x11, x11, 2
    9d0: 01059593  slli         x11, x11, 16
    9d4: 0105d593  srli         x11, x11, 16
    9d8: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    9dc: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    9e0: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    9e4: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    9e8: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    9ec: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    9f0: 0ff0000f  fence        0xf, 0xf
    9f4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9f8: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    9fc: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    a00: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a04: 00c585b3  add          x11, x11, x12
    a08: 000146b7  lui          x13, 0x00014  # x13 = 0x00014000
    a0c: 00d5e663  bltu         x11, x13, 0x00000a18  # target 0x00000a18
    a10: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    a14: 40e585b3  sub          x11, x11, x14
loc_a18:
    a18: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a1c: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    a20: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    a24: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    a28: 89c60613  addi         x12, x12, -1892  # x12 = 0xffb0089c · riscv_local_mem + 0x89c
    a2c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x89c · 0xffb0089c
    a30: 00258593  addi         x11, x11, 2
    a34: 01059593  slli         x11, x11, 16
    a38: 0105d593  srli         x11, x11, 16
    a3c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    a40: 89c60613  addi         x12, x12, -1892  # x12 = 0xffb0089c · riscv_local_mem + 0x89c
    a44: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    a48: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    a4c: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    a50: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    a54: 0ff0000f  fence        0xf, 0xf
    a58: 00138393  addi         x7, x7, 1
    a5c: da9ff06f  jal          x0, 0x00000804  # target 0x00000804
loc_a60:
    a60: 3640006f  jal          x0, 0x00000dc4  # target 0x00000dc4
loc_a64:
    a64: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a68: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    a6c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    a70: 000a0463  beq          x20, x0, 0x00000a78  # target 0x00000a78
    a74: ff1ff06f  jal          x0, 0x00000a64  # target 0x00000a64
loc_a78:
    a78: 0ff0000f  fence        0xf, 0xf
    a7c: 00008067  jalr         x0, 0(x1)
loc_a80:
    a80: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a84: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    a88: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    a8c: 000a0463  beq          x20, x0, 0x00000a94  # target 0x00000a94
    a90: ff1ff06f  jal          x0, 0x00000a80  # target 0x00000a80
loc_a94:
    a94: 0ff0000f  fence        0xf, 0xf
    a98: 00008067  jalr         x0, 0(x1)
loc_a9c:
    a9c: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    aa0: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    aa4: 007a7d13  andi         x26, x20, 7
    aa8: ff8a7a13  andi         x20, x20, -8
    aac: 01af8ab3  add          x21, x31, x26
    ab0: 007afb93  andi         x23, x21, 7
    ab4: 003ada93  srli         x21, x21, 3
    ab8: 00ba9a93  slli         x21, x21, 11
    abc: 014a8ab3  add          x21, x21, x20
    ac0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ac0
    ac4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000ad8
    ac8: 001b9b93  slli         x23, x23, 1
    acc: 017b0b33  add          x22, x22, x23
    ad0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ad4: 00008067  jalr         x0, 0(x1)
    ad8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    adc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ae0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ae4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ae8:
    ae8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    aec: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    af0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    af4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    af8: 015a6463  bltu         x20, x21, 0x00000b00  # target 0x00000b00
    afc: fedff06f  jal          x0, 0x00000ae8  # target 0x00000ae8
loc_b00:
    b00: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    b04: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    b08: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    b0c: 014a1a13  slli         x20, x20, 20
    b10: 014a5a13  srli         x20, x20, 20
    b14: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_b18:
    b18: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    b1c: 000b0463  beq          x22, x0, 0x00000b24  # target 0x00000b24
    b20: ff9ff06f  jal          x0, 0x00000b18  # target 0x00000b18
loc_b24:
    b24: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    b28: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    b2c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    b30: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    b34: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    b38: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    b3c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    b40: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    b44: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    b48: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    b4c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    b50: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    b54: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b58: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    b5c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    b60: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    b64: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    b68: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    b6c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    b70: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    b74: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    b78: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_b7c:
    b7c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    b80: 000b0463  beq          x22, x0, 0x00000b88  # target 0x00000b88
    b84: ff9ff06f  jal          x0, 0x00000b7c  # target 0x00000b7c
loc_b88:
    b88: 00008067  jalr         x0, 0(x1)
loc_b8c:
    b8c: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    b90: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    b94: 007a7d13  andi         x26, x20, 7
    b98: ff8a7a13  andi         x20, x20, -8
    b9c: 01af8ab3  add          x21, x31, x26
    ba0: 007afb93  andi         x23, x21, 7
    ba4: 003ada93  srli         x21, x21, 3
    ba8: 00ba9a93  slli         x21, x21, 11
    bac: 014a8ab3  add          x21, x21, x20
    bb0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000bb0
    bb4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000bc8
    bb8: 001b9b93  slli         x23, x23, 1
    bbc: 017b0b33  add          x22, x22, x23
    bc0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    bc4: 00008067  jalr         x0, 0(x1)
    bc8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    bcc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    bd0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    bd4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_bd8:
    bd8: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    bdc: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x00000798
    be0: 007a7d13  andi         x26, x20, 7
    be4: ff8a7a13  andi         x20, x20, -8
    be8: 01af8ab3  add          x21, x31, x26
    bec: 007afb93  andi         x23, x21, 7
    bf0: 003ada93  srli         x21, x21, 3
    bf4: 00ba9a93  slli         x21, x21, 11
    bf8: 014a8ab3  add          x21, x21, x20
    bfc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000bfc
    c00: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c14
    c04: 001b9b93  slli         x23, x23, 1
    c08: 017b0b33  add          x22, x22, x23
    c0c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c10: 00008067  jalr         x0, 0(x1)
    c14: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c18: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c1c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c20: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c24:
    c24: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    c28: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x0000079c
    c2c: 007a7d13  andi         x26, x20, 7
    c30: ff8a7a13  andi         x20, x20, -8
    c34: 01af8ab3  add          x21, x31, x26
    c38: 007afb93  andi         x23, x21, 7
    c3c: 003ada93  srli         x21, x21, 3
    c40: 00ba9a93  slli         x21, x21, 11
    c44: 014a8ab3  add          x21, x21, x20
    c48: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c48
    c4c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c60
    c50: 001b9b93  slli         x23, x23, 1
    c54: 017b0b33  add          x22, x22, x23
    c58: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c5c: 00008067  jalr         x0, 0(x1)
    c60: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c64: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c68: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c6c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c70:
    c70: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    c74: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007a0
    c78: 007a7d13  andi         x26, x20, 7
    c7c: ff8a7a13  andi         x20, x20, -8
    c80: 01af8ab3  add          x21, x31, x26
    c84: 007afb93  andi         x23, x21, 7
    c88: 003ada93  srli         x21, x21, 3
    c8c: 00ba9a93  slli         x21, x21, 11
    c90: 014a8ab3  add          x21, x21, x20
    c94: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c94
    c98: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000cac
    c9c: 001b9b93  slli         x23, x23, 1
    ca0: 017b0b33  add          x22, x22, x23
    ca4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ca8: 00008067  jalr         x0, 0(x1)
    cac: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    cb0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    cb4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    cb8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_cbc:
    cbc: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    cc0: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    cc4: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    cc8: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    ccc: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    cd0: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    cd4: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    cd8: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    cdc: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    ce0: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    ce4: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    ce8: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    cec: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    cf0: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    cf4: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    cf8: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    cfc: 020f8f93  addi         x31, x31, 32
    d00: 020f0f13  addi         x30, x30, 32
    d04: ff8e8e93  addi         x29, x29, -8
    d08: fa0e9ae3  bne          x29, x0, 0x00000cbc  # target 0x00000cbc
    d0c: 00008067  jalr         x0, 0(x1)
loc_d10:
    d10: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    d14: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    d18: 004f8f93  addi         x31, x31, 4
    d1c: 004f0f13  addi         x30, x30, 4
    d20: fffe8e93  addi         x29, x29, -1
    d24: fe0e96e3  bne          x29, x0, 0x00000d10  # target 0x00000d10
    d28: 00008067  jalr         x0, 0(x1)
loc_d2c:
    d2c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    d30: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    d34: 007a7d13  andi         x26, x20, 7
    d38: ff8a7a13  andi         x20, x20, -8
    d3c: 01af8ab3  add          x21, x31, x26
    d40: 007afb93  andi         x23, x21, 7
    d44: 003ada93  srli         x21, x21, 3
    d48: 00ba9a93  slli         x21, x21, 11
    d4c: 014a8ab3  add          x21, x21, x20
    d50: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d50
    d54: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d68
    d58: 001b9b93  slli         x23, x23, 1
    d5c: 017b0b33  add          x22, x22, x23
    d60: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d64: 00008067  jalr         x0, 0(x1)
    d68: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d6c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d70: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d74: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d78:
    d78: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    d7c: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    d80: 007a7d13  andi         x26, x20, 7
    d84: ff8a7a13  andi         x20, x20, -8
    d88: 01af8ab3  add          x21, x31, x26
    d8c: 007afb93  andi         x23, x21, 7
    d90: 003ada93  srli         x21, x21, 3
    d94: 00ba9a93  slli         x21, x21, 11
    d98: 014a8ab3  add          x21, x21, x20
    d9c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d9c
    da0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000db4
    da4: 001b9b93  slli         x23, x23, 1
    da8: 017b0b33  add          x22, x22, x23
    dac: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    db0: 00008067  jalr         x0, 0(x1)
    db4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    db8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    dbc: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    dc0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    dc4:           j FW_BRISC+4   # return to firmware, linked at install
