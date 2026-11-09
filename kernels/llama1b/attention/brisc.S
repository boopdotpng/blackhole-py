# llama3 1B decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (16): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7
# params: 0x7c0=e2e_q_heads, 0x7c4=e2e_l0_key_cache, 0x7c8=e2e_l0_value_cache, 0x7cc=e2e_context, 0x7d0=kv_blocks, 0x7d4=valid_columns, 0x7d8=attention_e2e_q_compact, 0x7dc=attention_e2e_k_compact, 0x7e0=attention_e2e_v_compact, 0x7e4=e2e_rope_cos, 0x7e8=e2e_rope_sin, 0x7ec=start_pos, 0x80c0=attention_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000992b7  lui          x5, 0x00099  # x5 = 0x00099000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00099000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     24: 0009c2b7  lui          x5, 0x0009c  # x5 = 0x0009c000
     28: 80028293  addi         x5, x5, -2048  # x5 = 0x0009b800
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x0009b800
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     40: 88838393  addi         x7, x7, -1912  # x7 = 0xffb00888 · riscv_local_mem + 0x888
     44: 00097437  lui          x8, 0x00097  # x8 = 0x00097000
     48: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00097000
     4c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     50: 88c38393  addi         x7, x7, -1908  # x7 = 0xffb0088c · riscv_local_mem + 0x88c
     54: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     58: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     5c: 89038393  addi         x7, x7, -1904  # x7 = 0xffb00890 · riscv_local_mem + 0x890
     60: 00096437  lui          x8, 0x00096  # x8 = 0x00096000
     64: 0083a023  sw           x8, 0(x7)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00096000
     68: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     6c: 89438393  addi         x7, x7, -1900  # x7 = 0xffb00894 · riscv_local_mem + 0x894
     70: 0003a023  sw           x0, 0(x7)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     74: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     78: 89848493  addi         x9, x9, -1896  # x9 = 0xffb00898 · riscv_local_mem + 0x898
     7c: 00090537  lui          x10, 0x00090  # x10 = 0x00090000
     80: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00090000
     84: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     88: 89c48493  addi         x9, x9, -1892  # x9 = 0xffb0089c · riscv_local_mem + 0x89c
     8c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
     90: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     94: 8a058593  addi         x11, x11, -1888  # x11 = 0xffb008a0 · riscv_local_mem + 0x8a0
     98: 00091637  lui          x12, 0x00091  # x12 = 0x00091000
     9c: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write 0x00091000
     a0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     a4: 8a458593  addi         x11, x11, -1884  # x11 = 0xffb008a4 · riscv_local_mem + 0x8a4
     a8: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write 0x00000000
     ac: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     b0: 8a858593  addi         x11, x11, -1880  # x11 = 0xffb008a8 · riscv_local_mem + 0x8a8
     b4: 00093637  lui          x12, 0x00093  # x12 = 0x00093000
     b8: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write 0x00093000
     bc: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     c0: 8ac58593  addi         x11, x11, -1876  # x11 = 0xffb008ac · riscv_local_mem + 0x8ac
     c4: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x8ac · 0xffb008ac; write 0x00000000
     c8: 7ec00393  addi         x7, x0, 2028  # x7 = 0x000007ec
     cc: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ec
     d0: 00425293  srli         x5, x4, 4
     d4: 00f27313  andi         x6, x4, 15
     d8: 00631313  slli         x6, x6, 6
     dc: 00131313  slli         x6, x6, 1
     e0: 2d1000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x000000e4
     e4: 2e9000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x000000e8
     e8: 00028f93  addi         x31, x5, 0
     ec: 2fd000ef  jal          x1, 0x00000be8  # target 0x00000be8; x1 = 0x000000f0
     f0: 000a8393  addi         x7, x21, 0
     f4: 000b0413  addi         x8, x22, 0
     f8: 00038f93  addi         x31, x7, 0
     fc: 00040f13  addi         x30, x8, 0
    100: 000b1eb7  lui          x29, 0x000b1  # x29 = 0x000b1000
    104: 800e8e93  addi         x29, x29, -2048  # x29 = 0x000b0800 · arc_apb_msi_fifo + 0x800
    108: 32d000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x0000010c
    10c: 00028f93  addi         x31, x5, 0
    110: 3c9000ef  jal          x1, 0x00000cd8  # target 0x00000cd8; x1 = 0x00000114
    114: 000a8393  addi         x7, x21, 0
    118: 000b0413  addi         x8, x22, 0
    11c: 00038f93  addi         x31, x7, 0
    120: 00040f13  addi         x30, x8, 0
    124: 000b1eb7  lui          x29, 0x000b1  # x29 = 0x000b1000
    128: 30d000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x0000012c
    12c: 2a1000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000130
    130: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    134: 0c048493  addi         x9, x9, 192  # x9 = 0x000080c0
    138: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x000080c0
    13c: 00741413  slli         x8, x8, 7
    140: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_144:
    144: 24000693  addi         x13, x0, 576  # x13 = 0x00000240
    148: 00d47c63  bgeu         x8, x13, 0x00000160  # target 0x00000160
    14c: 01800613  addi         x12, x0, 24  # x12 = 0x00000018
    150: 02c454b3  divu         x9, x8, x12
    154: 02c485b3  mul          x11, x9, x12
    158: 40b405b3  sub          x11, x8, x11
    15c: 01c0006f  jal          x0, 0x00000178  # target 0x00000178
loc_160:
    160: 40d406b3  sub          x13, x8, x13
    164: 01700613  addi         x12, x0, 23  # x12 = 0x00000017
    168: 02c6d4b3  divu         x9, x13, x12
    16c: 02c485b3  mul          x11, x9, x12
    170: 40b685b3  sub          x11, x13, x11
    174: 01848493  addi         x9, x9, 24
loc_178:
    178: 03f40513  addi         x10, x8, 63
    17c: 24000793  addi         x15, x0, 576  # x15 = 0x00000240
    180: 00f57c63  bgeu         x10, x15, 0x00000198  # target 0x00000198
    184: 01800713  addi         x14, x0, 24  # x14 = 0x00000018
    188: 02e55633  divu         x12, x10, x14
    18c: 02e606b3  mul          x13, x12, x14
    190: 40d506b3  sub          x13, x10, x13
    194: 01c0006f  jal          x0, 0x000001b0  # target 0x000001b0
loc_198:
    198: 40f507b3  sub          x15, x10, x15
    19c: 01700713  addi         x14, x0, 23  # x14 = 0x00000017
    1a0: 02e7d633  divu         x12, x15, x14
    1a4: 02e606b3  mul          x13, x12, x14
    1a8: 40d786b3  sub          x13, x15, x13
    1ac: 01860613  addi         x12, x12, 24
loc_1b0:
    1b0: 00048513  addi         x10, x9, 0
    1b4: 1fd000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x000001b8
    1b8: 215000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x000001bc
    1bc: 0009c737  lui          x14, 0x0009c  # x14 = 0x0009c000
loc_1c0:
    1c0: 00050f93  addi         x31, x10, 0
    1c4: 361000ef  jal          x1, 0x00000d24  # target 0x00000d24; x1 = 0x000001c8
    1c8: 000a8793  addi         x15, x21, 0
    1cc: 000b0813  addi         x16, x22, 0
    1d0: 00078f93  addi         x31, x15, 0
    1d4: 00080f13  addi         x30, x16, 0
    1d8: 00070e93  addi         x29, x14, 0
    1dc: 259000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000001e0
    1e0: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1e4: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    1e8: 00f70733  add          x14, x14, x15
    1ec: 00150513  addi         x10, x10, 1
    1f0: fca678e3  bgeu         x12, x10, 0x000001c0  # target 0x000001c0
    1f4: 1d9000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x000001f8
    1f8: 00048513  addi         x10, x9, 0
    1fc: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    200: 00739693  slli         x13, x7, 7
    204: 00099737  lui          x14, 0x00099  # x14 = 0x00099000
    208: 00e686b3  add          x13, x13, x14
loc_20c:
    20c: 01700713  addi         x14, x0, 23  # x14 = 0x00000017
    210: 01800793  addi         x15, x0, 24  # x15 = 0x00000018
    214: 00f57463  bgeu         x10, x15, 0x0000021c  # target 0x0000021c
    218: 00170713  addi         x14, x14, 1  # x14 = 0x00000018
loc_21c:
    21c: 40b70733  sub          x14, x14, x11
    220: 00f5f793  andi         x15, x11, 15
    224: 40f007b3  sub          x15, x0, x15
    228: 01078793  addi         x15, x15, 16
    22c: 00e7f463  bgeu         x15, x14, 0x00000234  # target 0x00000234
    230: 00078713  addi         x14, x15, 0
loc_234:
    234: 01f67793  andi         x15, x12, 31
    238: 40f007b3  sub          x15, x0, x15
    23c: 02078793  addi         x15, x15, 32
    240: 00e7f463  bgeu         x15, x14, 0x00000248  # target 0x00000248
    244: 00078713  addi         x14, x15, 0
loc_248:
    248: 40950833  sub          x16, x10, x9
    24c: 00b81813  slli         x16, x16, 11
    250: 00f5f793  andi         x15, x11, 15
    254: 00179793  slli         x15, x15, 1
    258: 0105fa13  andi         x20, x11, 16
    25c: 005a1a13  slli         x20, x20, 5
    260: 0147e7b3  or           x15, x15, x20
    264: 1e05fa13  andi         x20, x11, 480
    268: 0147e7b3  or           x15, x15, x20
    26c: 0095da13  srli         x20, x11, 9
    270: 00aa1a13  slli         x20, x20, 10
    274: 0147e7b3  or           x15, x15, x20
    278: 00f80833  add          x16, x16, x15
    27c: 0009ca37  lui          x20, 0x0009c  # x20 = 0x0009c000
    280: 01480833  add          x16, x16, x20
    284: 00161893  slli         x17, x12, 1
    288: 00d888b3  add          x17, x17, x13
    28c: 02064913  xori         x18, x12, 32
    290: 00191913  slli         x18, x18, 1
    294: 00d90933  add          x18, x18, x13
    298: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    29c: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2a0: 01490933  add          x18, x18, x20
    2a4: 02067993  andi         x19, x12, 32
    2a8: 00a99993  slli         x19, x19, 10
    2ac: 00080f93  addi         x31, x16, 0
    2b0: 00088f13  addi         x30, x17, 0
    2b4: 00090e93  addi         x29, x18, 0
    2b8: 00070e13  addi         x28, x14, 0
    2bc: 00098d93  addi         x27, x19, 0
loc_2c0:
    2c0: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2c4: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2c8: 01ba4a33  xor          x20, x20, x27
    2cc: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    2d0: 002f8f93  addi         x31, x31, 2
    2d4: 002f0f13  addi         x30, x30, 2
    2d8: 002e8e93  addi         x29, x29, 2
    2dc: fffe0e13  addi         x28, x28, -1
    2e0: fe0e10e3  bne          x28, x0, 0x000002c0  # target 0x000002c0
    2e4: 00e60633  add          x12, x12, x14
    2e8: 00e585b3  add          x11, x11, x14
    2ec: 01700793  addi         x15, x0, 23  # x15 = 0x00000017
    2f0: 01800993  addi         x19, x0, 24  # x19 = 0x00000018
    2f4: 01357463  bgeu         x10, x19, 0x000002fc  # target 0x000002fc
    2f8: 00178793  addi         x15, x15, 1  # x15 = 0x00000018
loc_2fc:
    2fc: 00f59663  bne          x11, x15, 0x00000308  # target 0x00000308
    300: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    304: 00150513  addi         x10, x10, 1
loc_308:
    308: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    30c: f0f660e3  bltu         x12, x15, 0x0000020c  # target 0x0000020c
    310: 04040413  addi         x8, x8, 64
    314: 00138393  addi         x7, x7, 1
    318: 00200493  addi         x9, x0, 2  # x9 = 0x00000002
    31c: e29394e3  bne          x7, x9, 0x00000144  # target 0x00000144
    320: 000084b7  lui          x9, 0x00008  # x9 = 0x00008000
    324: 0c048493  addi         x9, x9, 192  # x9 = 0x000080c0
    328: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x000080c0
    32c: 00145413  srli         x8, x8, 1
    330: 00641413  slli         x8, x8, 6
    334: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
    338: 1b000693  addi         x13, x0, 432  # x13 = 0x000001b0
    33c: 00d47c63  bgeu         x8, x13, 0x00000354  # target 0x00000354
    340: 00600613  addi         x12, x0, 6  # x12 = 0x00000006
    344: 02c454b3  divu         x9, x8, x12
    348: 02c485b3  mul          x11, x9, x12
    34c: 40b405b3  sub          x11, x8, x11
    350: 01c0006f  jal          x0, 0x0000036c  # target 0x0000036c
loc_354:
    354: 40d406b3  sub          x13, x8, x13
    358: 00500613  addi         x12, x0, 5  # x12 = 0x00000005
    35c: 02c6d4b3  divu         x9, x13, x12
    360: 02c485b3  mul          x11, x9, x12
    364: 40b685b3  sub          x11, x13, x11
    368: 04848493  addi         x9, x9, 72
loc_36c:
    36c: 03f40513  addi         x10, x8, 63
    370: 1b000793  addi         x15, x0, 432  # x15 = 0x000001b0
    374: 00f57c63  bgeu         x10, x15, 0x0000038c  # target 0x0000038c
    378: 00600713  addi         x14, x0, 6  # x14 = 0x00000006
    37c: 02e55633  divu         x12, x10, x14
    380: 02e606b3  mul          x13, x12, x14
    384: 40d506b3  sub          x13, x10, x13
    388: 01c0006f  jal          x0, 0x000003a4  # target 0x000003a4
loc_38c:
    38c: 40f507b3  sub          x15, x10, x15
    390: 00500713  addi         x14, x0, 5  # x14 = 0x00000005
    394: 02e7d633  divu         x12, x15, x14
    398: 02e606b3  mul          x13, x12, x14
    39c: 40d786b3  sub          x13, x15, x13
    3a0: 04860613  addi         x12, x12, 72
loc_3a4:
    3a4: 00048513  addi         x10, x9, 0
    3a8: 009000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x000003ac
    3ac: 021000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x000003b0
    3b0: 0009c737  lui          x14, 0x0009c  # x14 = 0x0009c000
loc_3b4:
    3b4: 00050f93  addi         x31, x10, 0
    3b8: 1b9000ef  jal          x1, 0x00000d70  # target 0x00000d70; x1 = 0x000003bc
    3bc: 000a8793  addi         x15, x21, 0
    3c0: 000b0813  addi         x16, x22, 0
    3c4: 00078f93  addi         x31, x15, 0
    3c8: 00080f13  addi         x30, x16, 0
    3cc: 00070e93  addi         x29, x14, 0
    3d0: 065000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000003d4
    3d4: 00050f93  addi         x31, x10, 0
    3d8: 1e5000ef  jal          x1, 0x00000dbc  # target 0x00000dbc; x1 = 0x000003dc
    3dc: 000a8793  addi         x15, x21, 0
    3e0: 000b0813  addi         x16, x22, 0
    3e4: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    3e8: 00e888b3  add          x17, x17, x14
    3ec: 00078f93  addi         x31, x15, 0
    3f0: 00080f13  addi         x30, x16, 0
    3f4: 00088e93  addi         x29, x17, 0
    3f8: 03d000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000003fc
    3fc: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    400: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    404: 00f70733  add          x14, x14, x15
    408: 00150513  addi         x10, x10, 1
    40c: faa674e3  bgeu         x12, x10, 0x000003b4  # target 0x000003b4
    410: 7bc000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000414
    414: 00048513  addi         x10, x9, 0
    418: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    41c: 00739693  slli         x13, x7, 7
    420: 00099737  lui          x14, 0x00099  # x14 = 0x00099000
    424: 00e686b3  add          x13, x13, x14
loc_428:
    428: 00500713  addi         x14, x0, 5  # x14 = 0x00000005
    42c: 04800793  addi         x15, x0, 72  # x15 = 0x00000048
    430: 00f57463  bgeu         x10, x15, 0x00000438  # target 0x00000438
    434: 00170713  addi         x14, x14, 1  # x14 = 0x00000006
loc_438:
    438: 40b70733  sub          x14, x14, x11
    43c: 00f5f793  andi         x15, x11, 15
    440: 40f007b3  sub          x15, x0, x15
    444: 01078793  addi         x15, x15, 16
    448: 00e7f463  bgeu         x15, x14, 0x00000450  # target 0x00000450
    44c: 00078713  addi         x14, x15, 0
loc_450:
    450: 01f67793  andi         x15, x12, 31
    454: 40f007b3  sub          x15, x0, x15
    458: 02078793  addi         x15, x15, 32
    45c: 00e7f463  bgeu         x15, x14, 0x00000464  # target 0x00000464
    460: 00078713  addi         x14, x15, 0
loc_464:
    464: 40950833  sub          x16, x10, x9
    468: 00b81813  slli         x16, x16, 11
    46c: 00f5f793  andi         x15, x11, 15
    470: 00179793  slli         x15, x15, 1
    474: 0105fa13  andi         x20, x11, 16
    478: 005a1a13  slli         x20, x20, 5
    47c: 0147e7b3  or           x15, x15, x20
    480: 1e05fa13  andi         x20, x11, 480
    484: 0147e7b3  or           x15, x15, x20
    488: 0095da13  srli         x20, x11, 9
    48c: 00aa1a13  slli         x20, x20, 10
    490: 0147e7b3  or           x15, x15, x20
    494: 00f80833  add          x16, x16, x15
    498: 0009ca37  lui          x20, 0x0009c  # x20 = 0x0009c000
    49c: 01480833  add          x16, x16, x20
    4a0: 00161893  slli         x17, x12, 1
    4a4: 00d888b3  add          x17, x17, x13
    4a8: 02064913  xori         x18, x12, 32
    4ac: 00191913  slli         x18, x18, 1
    4b0: 00d90933  add          x18, x18, x13
    4b4: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4b8: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4bc: 01490933  add          x18, x18, x20
    4c0: 02067993  andi         x19, x12, 32
    4c4: 00a99993  slli         x19, x19, 10
    4c8: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    4cc: 010a0a33  add          x20, x20, x16
    4d0: 00161a93  slli         x21, x12, 1
    4d4: 000b0b37  lui          x22, 0x000b0  # x22 = 0x000b0000 · arc_apb_msi_fifo + 0x0
    4d8: 016a8ab3  add          x21, x21, x22
    4dc: ffc10113  addi         x2, x2, -4
    4e0: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    4e4: 00080f93  addi         x31, x16, 0
    4e8: 00088f13  addi         x30, x17, 0
    4ec: 00090e93  addi         x29, x18, 0
    4f0: 00070e13  addi         x28, x14, 0
    4f4: 00098d93  addi         x27, x19, 0
    4f8: 000a0d13  addi         x26, x20, 0
    4fc: 000a8c93  addi         x25, x21, 0
loc_500:
    500: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    504: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    508: 01ba4a33  xor          x20, x20, x27
    50c: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    510: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    514: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    518: 002d0d13  addi         x26, x26, 2
    51c: 002c8c93  addi         x25, x25, 2
    520: 002f8f93  addi         x31, x31, 2
    524: 002f0f13  addi         x30, x30, 2
    528: 002e8e93  addi         x29, x29, 2
    52c: fffe0e13  addi         x28, x28, -1
    530: fc0e18e3  bne          x28, x0, 0x00000500  # target 0x00000500
    534: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    538: 00410113  addi         x2, x2, 4
    53c: 00e60633  add          x12, x12, x14
    540: 00e585b3  add          x11, x11, x14
    544: 00500793  addi         x15, x0, 5  # x15 = 0x00000005
    548: 04800993  addi         x19, x0, 72  # x19 = 0x00000048
    54c: 01357463  bgeu         x10, x19, 0x00000554  # target 0x00000554
    550: 00178793  addi         x15, x15, 1  # x15 = 0x00000006
loc_554:
    554: 00f59663  bne          x11, x15, 0x00000560  # target 0x00000560
    558: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    55c: 00150513  addi         x10, x10, 1
loc_560:
    560: 04000793  addi         x15, x0, 64  # x15 = 0x00000040
    564: ecf662e3  bltu         x12, x15, 0x00000428  # target 0x00000428
    568: 000b13b7  lui          x7, 0x000b1  # x7 = 0x000b1000
    56c: 80038393  addi         x7, x7, -2048  # x7 = 0x000b0800 · arc_apb_msi_fifo + 0x800
    570: 006383b3  add          x7, x7, x6
    574: 00038f93  addi         x31, x7, 0
    578: 0009af37  lui          x30, 0x0009a  # x30 = 0x0009a000
    57c: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    580: 089000ef  jal          x1, 0x00000e08  # target 0x00000e08; x1 = 0x00000584
    584: 0009afb7  lui          x31, 0x0009a  # x31 = 0x0009a000
    588: 0009af37  lui          x30, 0x0009a  # x30 = 0x0009a000
    58c: 080f0f13  addi         x30, x30, 128  # x30 = 0x0009a080
    590: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    594: 0c9000ef  jal          x1, 0x00000e5c  # target 0x00000e5c; x1 = 0x00000598
    598: 0009afb7  lui          x31, 0x0009a  # x31 = 0x0009a000
    59c: 0009af37  lui          x30, 0x0009a  # x30 = 0x0009a000
    5a0: 100f0f13  addi         x30, x30, 256  # x30 = 0x0009a100
    5a4: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5a8: 0b5000ef  jal          x1, 0x00000e5c  # target 0x00000e5c; x1 = 0x000005ac
    5ac: 000b13b7  lui          x7, 0x000b1  # x7 = 0x000b1000
    5b0: 006383b3  add          x7, x7, x6
    5b4: 00038f93  addi         x31, x7, 0
    5b8: 0009bf37  lui          x30, 0x0009b  # x30 = 0x0009b000
    5bc: 800f0f13  addi         x30, x30, -2048  # x30 = 0x0009a800
    5c0: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5c4: 045000ef  jal          x1, 0x00000e08  # target 0x00000e08; x1 = 0x000005c8
    5c8: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    5cc: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0009a800
    5d0: 0009bf37  lui          x30, 0x0009b  # x30 = 0x0009b000
    5d4: 880f0f13  addi         x30, x30, -1920  # x30 = 0x0009a880
    5d8: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5dc: 081000ef  jal          x1, 0x00000e5c  # target 0x00000e5c; x1 = 0x000005e0
    5e0: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    5e4: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0009a800
    5e8: 0009bf37  lui          x30, 0x0009b  # x30 = 0x0009b000
    5ec: 900f0f13  addi         x30, x30, -1792  # x30 = 0x0009a900
    5f0: 02000e93  addi         x29, x0, 32  # x29 = 0x00000020
    5f4: 069000ef  jal          x1, 0x00000e5c  # target 0x00000e5c; x1 = 0x000005f8
    5f8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5fc: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    600: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    604: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    608: 00520233  add          x4, x4, x5
    60c: 0009b337  lui          x6, 0x0009b  # x6 = 0x0009b000
    610: 00626663  bltu         x4, x6, 0x0000061c  # target 0x0000061c
    614: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    618: 40720233  sub          x4, x4, x7
loc_61c:
    61c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    620: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    624: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    628: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    62c: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    630: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    634: 00420213  addi         x4, x4, 4
    638: 01021213  slli         x4, x4, 16
    63c: 01025213  srli         x4, x4, 16
    640: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    644: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    648: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    64c: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    650: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    654: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    658: 0ff0000f  fence        0xf, 0xf
    65c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    660: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    664: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    668: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_66c:
    66c: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    670: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    674: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    678: 40428333  sub          x6, x5, x4
    67c: 01031313  slli         x6, x6, 16
    680: 01035313  srli         x6, x6, 16
    684: 00737663  bgeu         x6, x7, 0x00000690  # target 0x00000690
    688: 0ff0000f  fence        0xf, 0xf
    68c: fe1ff06f  jal          x0, 0x0000066c  # target 0x0000066c
loc_690:
    690: 0ff0000f  fence        0xf, 0xf
    694: 000083b7  lui          x7, 0x00008  # x7 = 0x00008000
    698: 0c038393  addi         x7, x7, 192  # x7 = 0x000080c0
    69c: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x000080c0
    6a0: 7d000393  addi         x7, x0, 2000  # x7 = 0x000007d0
    6a4: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x000007d0
    6a8: 7d400393  addi         x7, x0, 2004  # x7 = 0x000007d4
    6ac: 0003a303  lw           x6, 0(x7)  # param valid_columns; 0x000007d4
    6b0: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    6b4: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    6b8: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_6bc:
    6bc: ffb4d637  lui          x12, 0xffb4d  # x12 = 0xffb4d000
    6c0: 02060613  addi         x12, x12, 32  # x12 = 0xffb4d020
    6c4: 00065403  lhu          x8, 0(x12)  # 0xffb4d020
    6c8: 408384b3  sub          x9, x7, x8
    6cc: 01049493  slli         x9, x9, 16
    6d0: 0104d493  srli         x9, x9, 16
    6d4: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    6d8: 40950533  sub          x10, x10, x9
    6dc: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    6e0: 00b57663  bgeu         x10, x11, 0x000006ec  # target 0x000006ec
    6e4: 0ff0000f  fence        0xf, 0xf
    6e8: fd5ff06f  jal          x0, 0x000006bc  # target 0x000006bc
loc_6ec:
    6ec: 0ff0000f  fence        0xf, 0xf
    6f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6f4: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    6f8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    6fc: 00038413  addi         x8, x7, 0
    700: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_704:
    704: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    708: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    70c: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    710: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    714: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    718: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    71c: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    720: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    724: 02040413  addi         x8, x8, 32
    728: ff848493  addi         x9, x9, -8
    72c: fc049ce3  bne          x9, x0, 0x00000704  # target 0x00000704
    730: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    734: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    738: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    73c: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    740: 008383b3  add          x7, x7, x8
    744: 000984b7  lui          x9, 0x00098  # x9 = 0x00098000
    748: 0093e663  bltu         x7, x9, 0x00000754  # target 0x00000754
    74c: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    750: 40a383b3  sub          x7, x7, x10
loc_754:
    754: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    758: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    75c: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    760: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    764: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    768: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    76c: 00138393  addi         x7, x7, 1
    770: 01039393  slli         x7, x7, 16
    774: 0103d393  srli         x7, x7, 16
    778: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    77c: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    780: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    784: ffb4d437  lui          x8, 0xffb4d  # x8 = 0xffb4d000
    788: 02840413  addi         x8, x8, 40  # x8 = 0xffb4d028
    78c: 00742023  sw           x7, 0(x8)  # 0xffb4d028; write runtime value
    790: 0ff0000f  fence        0xf, 0xf
    794: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    798: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    79c: 00062383  lw           x7, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
loc_7a0:
    7a0: ffb4c637  lui          x12, 0xffb4c  # x12 = 0xffb4c000
    7a4: 02060613  addi         x12, x12, 32  # x12 = 0xffb4c020
    7a8: 00065403  lhu          x8, 0(x12)  # 0xffb4c020
    7ac: 408384b3  sub          x9, x7, x8
    7b0: 01049493  slli         x9, x9, 16
    7b4: 0104d493  srli         x9, x9, 16
    7b8: 00100513  addi         x10, x0, 1  # x10 = 0x00000001
    7bc: 40950533  sub          x10, x10, x9
    7c0: 00100593  addi         x11, x0, 1  # x11 = 0x00000001
    7c4: 00b57663  bgeu         x10, x11, 0x000007d0  # target 0x000007d0
    7c8: 0ff0000f  fence        0xf, 0xf
    7cc: fd5ff06f  jal          x0, 0x000007a0  # target 0x000007a0
loc_7d0:
    7d0: 0ff0000f  fence        0xf, 0xf
    7d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7d8: 89040413  addi         x8, x8, -1904  # x8 = 0xffb00890 · riscv_local_mem + 0x890
    7dc: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x890 · 0xffb00890
    7e0: 00038413  addi         x8, x7, 0
    7e4: 40000493  addi         x9, x0, 1024  # x9 = 0x00000400
loc_7e8:
    7e8: 00042023  sw           x0, 0(x8)  # Address depends on runtime register values
    7ec: 00042223  sw           x0, 4(x8)  # Address depends on runtime register values
    7f0: 00042423  sw           x0, 8(x8)  # Address depends on runtime register values
    7f4: 00042623  sw           x0, 12(x8)  # Address depends on runtime register values
    7f8: 00042823  sw           x0, 16(x8)  # Address depends on runtime register values
    7fc: 00042a23  sw           x0, 20(x8)  # Address depends on runtime register values
    800: 00042c23  sw           x0, 24(x8)  # Address depends on runtime register values
    804: 00042e23  sw           x0, 28(x8)  # Address depends on runtime register values
    808: 02040413  addi         x8, x8, 32
    80c: ff848493  addi         x9, x9, -8
    810: fc049ce3  bne          x9, x0, 0x000007e8  # target 0x000007e8
    814: 00030413  addi         x8, x6, 0
    818: 02000493  addi         x9, x0, 32  # x9 = 0x00000020
    81c: ff800537  lui          x10, 0xff800  # x10 = 0xff800000
loc_820:
    820: 02947a63  bgeu         x8, x9, 0x00000854  # target 0x00000854
    824: 00445593  srli         x11, x8, 4
    828: 00a59593  slli         x11, x11, 10
    82c: 00f47613  andi         x12, x8, 15
    830: 00261613  slli         x12, x12, 2
    834: 00c586b3  add          x13, x11, x12
    838: 00d38733  add          x14, x7, x13
    83c: 00a72023  sw           x10, 0(x14)  # Address depends on runtime register values
    840: 00d38733  add          x14, x7, x13
    844: 04070713  addi         x14, x14, 64
    848: 00a72023  sw           x10, 0(x14)  # Address depends on runtime register values
    84c: 00140413  addi         x8, x8, 1
    850: fd1ff06f  jal          x0, 0x00000820  # target 0x00000820
loc_854:
    854: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    858: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    85c: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890
    860: 00001437  lui          x8, 0x00001  # x8 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    864: 008383b3  add          x7, x7, x8
    868: 000974b7  lui          x9, 0x00097  # x9 = 0x00097000
    86c: 0093e663  bltu         x7, x9, 0x00000878  # target 0x00000878
    870: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    874: 40a383b3  sub          x7, x7, x10
loc_878:
    878: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    87c: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
    880: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    884: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    888: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    88c: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894
    890: 00138393  addi         x7, x7, 1
    894: 01039393  slli         x7, x7, 16
    898: 0103d393  srli         x7, x7, 16
    89c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    8a0: 89440413  addi         x8, x8, -1900  # x8 = 0xffb00894 · riscv_local_mem + 0x894
    8a4: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    8a8: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    8ac: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    8b0: 00742023  sw           x7, 0(x8)  # 0xffb4c028; write runtime value
    8b4: 0ff0000f  fence        0xf, 0xf
    8b8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    8bc: 00028413  addi         x8, x5, 0
loc_8c0:
    8c0: 2e83f663  bgeu         x7, x8, 0x00000bac  # target 0x00000bac
    8c4: ffb01737  lui          x14, 0xffb01  # x14 = 0xffb01000
    8c8: 89c70713  addi         x14, x14, -1892  # x14 = 0xffb0089c · riscv_local_mem + 0x89c
    8cc: 00072483  lw           x9, 0(x14)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_8d0:
    8d0: ffb48737  lui          x14, 0xffb48  # x14 = 0xffb48000
    8d4: 02070713  addi         x14, x14, 32  # x14 = 0xffb48020
    8d8: 00075503  lhu          x10, 0(x14)  # 0xffb48020
    8dc: 40a485b3  sub          x11, x9, x10
    8e0: 01059593  slli         x11, x11, 16
    8e4: 0105d593  srli         x11, x11, 16
    8e8: 00200613  addi         x12, x0, 2  # x12 = 0x00000002
    8ec: 40b60633  sub          x12, x12, x11
    8f0: 00200693  addi         x13, x0, 2  # x13 = 0x00000002
    8f4: 00d67663  bgeu         x12, x13, 0x00000900  # target 0x00000900
    8f8: 0ff0000f  fence        0xf, 0xf
    8fc: fd5ff06f  jal          x0, 0x000008d0  # target 0x000008d0
loc_900:
    900: 0ff0000f  fence        0xf, 0xf
    904: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    908: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    90c: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    910: 00001537  lui          x10, 0x00001  # x10 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    914: 00a484b3  add          x9, x9, x10
    918: 000915b7  lui          x11, 0x00091  # x11 = 0x00091000
    91c: 00b4e663  bltu         x9, x11, 0x00000928  # target 0x00000928
    920: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    924: 40c484b3  sub          x9, x9, x12
loc_928:
    928: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    92c: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    930: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    934: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    938: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    93c: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    940: 00248493  addi         x9, x9, 2
    944: 01049493  slli         x9, x9, 16
    948: 0104d493  srli         x9, x9, 16
    94c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    950: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    954: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    958: ffb48537  lui          x10, 0xffb48  # x10 = 0xffb48000
    95c: 02850513  addi         x10, x10, 40  # x10 = 0xffb48028
    960: 00952023  sw           x9, 0(x10)  # 0xffb48028; write runtime value
    964: 0ff0000f  fence        0xf, 0xf
    968: 00125493  srli         x9, x4, 1
    96c: 00949493  slli         x9, x9, 9
    970: 00139513  slli         x10, x7, 1
    974: 00a484b3  add          x9, x9, x10
    978: 238000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x0000097c
    97c: 250000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000980
    980: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    984: 8a480813  addi         x16, x16, -1884  # x16 = 0xffb008a4 · riscv_local_mem + 0x8a4
    988: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8a4 · 0xffb008a4
loc_98c:
    98c: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    990: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    994: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    998: 40c586b3  sub          x13, x11, x12
    99c: 01069693  slli         x13, x13, 16
    9a0: 0106d693  srli         x13, x13, 16
    9a4: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    9a8: 40d70733  sub          x14, x14, x13
    9ac: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    9b0: 00f77663  bgeu         x14, x15, 0x000009bc  # target 0x000009bc
    9b4: 0ff0000f  fence        0xf, 0xf
    9b8: fd5ff06f  jal          x0, 0x0000098c  # target 0x0000098c
loc_9bc:
    9bc: 0ff0000f  fence        0xf, 0xf
    9c0: 00048593  addi         x11, x9, 0
    9c4: 00058f93  addi         x31, x11, 0
    9c8: 4b0000ef  jal          x1, 0x00000e78  # target 0x00000e78; x1 = 0x000009cc
    9cc: 000a8613  addi         x12, x21, 0
    9d0: 000b0693  addi         x13, x22, 0
    9d4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9d8: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    9dc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    9e0: 00060f93  addi         x31, x12, 0
    9e4: 00068f13  addi         x30, x13, 0
    9e8: 00070e93  addi         x29, x14, 0
    9ec: 248000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000009f0
    9f0: 00148593  addi         x11, x9, 1
    9f4: 00058f93  addi         x31, x11, 0
    9f8: 480000ef  jal          x1, 0x00000e78  # target 0x00000e78; x1 = 0x000009fc
    9fc: 000a8613  addi         x12, x21, 0
    a00: 000b0693  addi         x13, x22, 0
    a04: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a08: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    a0c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    a10: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a14: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    a18: 00f70733  add          x14, x14, x15
    a1c: 00060f93  addi         x31, x12, 0
    a20: 00068f13  addi         x30, x13, 0
    a24: 00070e93  addi         x29, x14, 0
    a28: 20c000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000a2c
    a2c: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    a30: 8ac80813  addi         x16, x16, -1876  # x16 = 0xffb008ac · riscv_local_mem + 0x8ac
    a34: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x8ac · 0xffb008ac
loc_a38:
    a38: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    a3c: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    a40: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    a44: 40c586b3  sub          x13, x11, x12
    a48: 01069693  slli         x13, x13, 16
    a4c: 0106d693  srli         x13, x13, 16
    a50: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    a54: 40d70733  sub          x14, x14, x13
    a58: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    a5c: 00f77663  bgeu         x14, x15, 0x00000a68  # target 0x00000a68
    a60: 0ff0000f  fence        0xf, 0xf
    a64: fd5ff06f  jal          x0, 0x00000a38  # target 0x00000a38
loc_a68:
    a68: 0ff0000f  fence        0xf, 0xf
    a6c: 00048593  addi         x11, x9, 0
    a70: 00058f93  addi         x31, x11, 0
    a74: 450000ef  jal          x1, 0x00000ec4  # target 0x00000ec4; x1 = 0x00000a78
    a78: 000a8613  addi         x12, x21, 0
    a7c: 000b0693  addi         x13, x22, 0
    a80: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a84: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    a88: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    a8c: 00060f93  addi         x31, x12, 0
    a90: 00068f13  addi         x30, x13, 0
    a94: 00070e93  addi         x29, x14, 0
    a98: 19c000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000a9c
    a9c: 00148593  addi         x11, x9, 1
    aa0: 00058f93  addi         x31, x11, 0
    aa4: 420000ef  jal          x1, 0x00000ec4  # target 0x00000ec4; x1 = 0x00000aa8
    aa8: 000a8613  addi         x12, x21, 0
    aac: 000b0693  addi         x13, x22, 0
    ab0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ab4: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    ab8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    abc: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    ac0: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    ac4: 00f70733  add          x14, x14, x15
    ac8: 00060f93  addi         x31, x12, 0
    acc: 00068f13  addi         x30, x13, 0
    ad0: 00070e93  addi         x29, x14, 0
    ad4: 160000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000ad8
    ad8: 0f4000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000adc
    adc: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ae0: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    ae4: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0
    ae8: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    aec: 00c585b3  add          x11, x11, x12
    af0: 000936b7  lui          x13, 0x00093  # x13 = 0x00093000
    af4: 00d5e663  bltu         x11, x13, 0x00000b00  # target 0x00000b00
    af8: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    afc: 40e585b3  sub          x11, x11, x14
loc_b00:
    b00: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b04: 8a078793  addi         x15, x15, -1888  # x15 = 0xffb008a0 · riscv_local_mem + 0x8a0
    b08: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a0 · 0xffb008a0; write runtime value
    b0c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b10: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    b14: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4
    b18: 00258593  addi         x11, x11, 2
    b1c: 01059593  slli         x11, x11, 16
    b20: 0105d593  srli         x11, x11, 16
    b24: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b28: 8a460613  addi         x12, x12, -1884  # x12 = 0xffb008a4 · riscv_local_mem + 0x8a4
    b2c: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8a4 · 0xffb008a4; write runtime value
    b30: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    b34: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    b38: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    b3c: 0ff0000f  fence        0xf, 0xf
    b40: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b44: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b48: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8
    b4c: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b50: 00c585b3  add          x11, x11, x12
    b54: 000956b7  lui          x13, 0x00095  # x13 = 0x00095000
    b58: 00d5e663  bltu         x11, x13, 0x00000b64  # target 0x00000b64
    b5c: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    b60: 40e585b3  sub          x11, x11, x14
loc_b64:
    b64: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b68: 8a878793  addi         x15, x15, -1880  # x15 = 0xffb008a8 · riscv_local_mem + 0x8a8
    b6c: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x8a8 · 0xffb008a8; write runtime value
    b70: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b74: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    b78: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac
    b7c: 00258593  addi         x11, x11, 2
    b80: 01059593  slli         x11, x11, 16
    b84: 0105d593  srli         x11, x11, 16
    b88: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b8c: 8ac60613  addi         x12, x12, -1876  # x12 = 0xffb008ac · riscv_local_mem + 0x8ac
    b90: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x8ac · 0xffb008ac; write runtime value
    b94: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    b98: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    b9c: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    ba0: 0ff0000f  fence        0xf, 0xf
    ba4: 00138393  addi         x7, x7, 1
    ba8: d19ff06f  jal          x0, 0x000008c0  # target 0x000008c0
loc_bac:
    bac: 3640006f  jal          x0, 0x00000f10  # target 0x00000f10
loc_bb0:
    bb0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bb4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    bb8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    bbc: 000a0463  beq          x20, x0, 0x00000bc4  # target 0x00000bc4
    bc0: ff1ff06f  jal          x0, 0x00000bb0  # target 0x00000bb0
loc_bc4:
    bc4: 0ff0000f  fence        0xf, 0xf
    bc8: 00008067  jalr         x0, 0(x1)
loc_bcc:
    bcc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bd0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    bd4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    bd8: 000a0463  beq          x20, x0, 0x00000be0  # target 0x00000be0
    bdc: ff1ff06f  jal          x0, 0x00000bcc  # target 0x00000bcc
loc_be0:
    be0: 0ff0000f  fence        0xf, 0xf
    be4: 00008067  jalr         x0, 0(x1)
loc_be8:
    be8: 7e400a93  addi         x21, x0, 2020  # x21 = 0x000007e4
    bec: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007e4
    bf0: 007a7d13  andi         x26, x20, 7
    bf4: ff8a7a13  andi         x20, x20, -8
    bf8: 01af8ab3  add          x21, x31, x26
    bfc: 007afb93  andi         x23, x21, 7
    c00: 003ada93  srli         x21, x21, 3
    c04: 00ba9a93  slli         x21, x21, 11
    c08: 014a8ab3  add          x21, x21, x20
    c0c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c0c
    c10: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c24
    c14: 001b9b93  slli         x23, x23, 1
    c18: 017b0b33  add          x22, x22, x23
    c1c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c20: 00008067  jalr         x0, 0(x1)
    c24: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c28: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c2c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c30: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c34:
    c34: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c38: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c3c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c40: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    c44: 015a6463  bltu         x20, x21, 0x00000c4c  # target 0x00000c4c
    c48: fedff06f  jal          x0, 0x00000c34  # target 0x00000c34
loc_c4c:
    c4c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c50: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    c54: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    c58: 014a1a13  slli         x20, x20, 20
    c5c: 014a5a13  srli         x20, x20, 20
    c60: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_c64:
    c64: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    c68: 000b0463  beq          x22, x0, 0x00000c70  # target 0x00000c70
    c6c: ff9ff06f  jal          x0, 0x00000c64  # target 0x00000c64
loc_c70:
    c70: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    c74: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    c78: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    c7c: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    c80: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    c84: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    c88: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    c8c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    c90: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    c94: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    c98: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    c9c: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    ca0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    ca4: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    ca8: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    cac: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    cb0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    cb4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    cb8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    cbc: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    cc0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    cc4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_cc8:
    cc8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    ccc: 000b0463  beq          x22, x0, 0x00000cd4  # target 0x00000cd4
    cd0: ff9ff06f  jal          x0, 0x00000cc8  # target 0x00000cc8
loc_cd4:
    cd4: 00008067  jalr         x0, 0(x1)
loc_cd8:
    cd8: 7e800a93  addi         x21, x0, 2024  # x21 = 0x000007e8
    cdc: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007e8
    ce0: 007a7d13  andi         x26, x20, 7
    ce4: ff8a7a13  andi         x20, x20, -8
    ce8: 01af8ab3  add          x21, x31, x26
    cec: 007afb93  andi         x23, x21, 7
    cf0: 003ada93  srli         x21, x21, 3
    cf4: 00ba9a93  slli         x21, x21, 11
    cf8: 014a8ab3  add          x21, x21, x20
    cfc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000cfc
    d00: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d14
    d04: 001b9b93  slli         x23, x23, 1
    d08: 017b0b33  add          x22, x22, x23
    d0c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d10: 00008067  jalr         x0, 0(x1)
    d14: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d18: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d1c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d20: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d24:
    d24: 7d800a93  addi         x21, x0, 2008  # x21 = 0x000007d8
    d28: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x000007d8
    d2c: 007a7d13  andi         x26, x20, 7
    d30: ff8a7a13  andi         x20, x20, -8
    d34: 01af8ab3  add          x21, x31, x26
    d38: 007afb93  andi         x23, x21, 7
    d3c: 003ada93  srli         x21, x21, 3
    d40: 00ba9a93  slli         x21, x21, 11
    d44: 014a8ab3  add          x21, x21, x20
    d48: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d48
    d4c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d60
    d50: 001b9b93  slli         x23, x23, 1
    d54: 017b0b33  add          x22, x22, x23
    d58: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d5c: 00008067  jalr         x0, 0(x1)
    d60: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d64: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d68: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d6c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d70:
    d70: 7dc00a93  addi         x21, x0, 2012  # x21 = 0x000007dc
    d74: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x000007dc
    d78: 007a7d13  andi         x26, x20, 7
    d7c: ff8a7a13  andi         x20, x20, -8
    d80: 01af8ab3  add          x21, x31, x26
    d84: 007afb93  andi         x23, x21, 7
    d88: 003ada93  srli         x21, x21, 3
    d8c: 00ba9a93  slli         x21, x21, 11
    d90: 014a8ab3  add          x21, x21, x20
    d94: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d94
    d98: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000dac
    d9c: 001b9b93  slli         x23, x23, 1
    da0: 017b0b33  add          x22, x22, x23
    da4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    da8: 00008067  jalr         x0, 0(x1)
    dac: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    db0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    db4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    db8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_dbc:
    dbc: 7e000a93  addi         x21, x0, 2016  # x21 = 0x000007e0
    dc0: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007e0
    dc4: 007a7d13  andi         x26, x20, 7
    dc8: ff8a7a13  andi         x20, x20, -8
    dcc: 01af8ab3  add          x21, x31, x26
    dd0: 007afb93  andi         x23, x21, 7
    dd4: 003ada93  srli         x21, x21, 3
    dd8: 00ba9a93  slli         x21, x21, 11
    ddc: 014a8ab3  add          x21, x21, x20
    de0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000de0
    de4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000df8
    de8: 001b9b93  slli         x23, x23, 1
    dec: 017b0b33  add          x22, x22, x23
    df0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    df4: 00008067  jalr         x0, 0(x1)
    df8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    dfc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e00: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e04: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e08:
    e08: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    e0c: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    e10: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    e14: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    e18: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    e1c: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    e20: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    e24: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    e28: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    e2c: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    e30: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    e34: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    e38: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    e3c: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    e40: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    e44: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    e48: 020f8f93  addi         x31, x31, 32
    e4c: 020f0f13  addi         x30, x30, 32
    e50: ff8e8e93  addi         x29, x29, -8
    e54: fa0e9ae3  bne          x29, x0, 0x00000e08  # target 0x00000e08
    e58: 00008067  jalr         x0, 0(x1)
loc_e5c:
    e5c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    e60: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    e64: 004f8f93  addi         x31, x31, 4
    e68: 004f0f13  addi         x30, x30, 4
    e6c: fffe8e93  addi         x29, x29, -1
    e70: fe0e96e3  bne          x29, x0, 0x00000e5c  # target 0x00000e5c
    e74: 00008067  jalr         x0, 0(x1)
loc_e78:
    e78: 7c400a93  addi         x21, x0, 1988  # x21 = 0x000007c4
    e7c: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x000007c4
    e80: 007a7d13  andi         x26, x20, 7
    e84: ff8a7a13  andi         x20, x20, -8
    e88: 01af8ab3  add          x21, x31, x26
    e8c: 007afb93  andi         x23, x21, 7
    e90: 003ada93  srli         x21, x21, 3
    e94: 00ba9a93  slli         x21, x21, 11
    e98: 014a8ab3  add          x21, x21, x20
    e9c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e9c
    ea0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000eb4
    ea4: 001b9b93  slli         x23, x23, 1
    ea8: 017b0b33  add          x22, x22, x23
    eac: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    eb0: 00008067  jalr         x0, 0(x1)
    eb4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    eb8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ebc: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ec0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ec4:
    ec4: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    ec8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x000007c8
    ecc: 007a7d13  andi         x26, x20, 7
    ed0: ff8a7a13  andi         x20, x20, -8
    ed4: 01af8ab3  add          x21, x31, x26
    ed8: 007afb93  andi         x23, x21, 7
    edc: 003ada93  srli         x21, x21, 3
    ee0: 00ba9a93  slli         x21, x21, 11
    ee4: 014a8ab3  add          x21, x21, x20
    ee8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ee8
    eec: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f00
    ef0: 001b9b93  slli         x23, x23, 1
    ef4: 017b0b33  add          x22, x22, x23
    ef8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    efc: 00008067  jalr         x0, 0(x1)
    f00: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    f04: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f08: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    f0c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    f10:           j FW_BRISC+4   # return to firmware, linked at install
