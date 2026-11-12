# llama3 8b-bf16 decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000202b7  lui          x5, 0x00020  # x5 = 0x00020000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x0001f800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0001f800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     28: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00022000
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
     60: 00011637  lui          x12, 0x00011  # x12 = 0x00011000
     64: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00011000
     68: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     6c: 89458593  addi         x11, x11, -1900  # x11 = 0xffb00894 · riscv_local_mem + 0x894
     70: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     74: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     78: 89858593  addi         x11, x11, -1896  # x11 = 0xffb00898 · riscv_local_mem + 0x898
     7c: 00015637  lui          x12, 0x00015  # x12 = 0x00015000
     80: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00015000
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
     c0: 285278e3  bgeu         x4, x5, 0x00000b50  # target 0x00000b50
     c4: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     c8: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
     cc: 00325293  srli         x5, x4, 3
     d0: 00727313  andi         x6, x4, 7
     d4: 00731313  slli         x6, x6, 7
     d8: 00131313  slli         x6, x6, 1
     dc: 279000ef  jal          x1, 0x00000b54  # target 0x00000b54; x1 = 0x000000e0
     e0: 291000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x000000e4
     e4: 00028f93  addi         x31, x5, 0
     e8: 2a5000ef  jal          x1, 0x00000b8c  # target 0x00000b8c; x1 = 0x000000ec
     ec: 000a8393  addi         x7, x21, 0
     f0: 000b0413  addi         x8, x22, 0
     f4: 00038f93  addi         x31, x7, 0
     f8: 00040f13  addi         x30, x8, 0
     fc: 00037eb7  lui          x29, 0x00037  # x29 = 0x00037000 · arc_apb_reset_unit + 0x7000
    100: 2d9000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000104
    104: 00028f93  addi         x31, x5, 0
    108: 375000ef  jal          x1, 0x00000c7c  # target 0x00000c7c; x1 = 0x0000010c
    10c: 000a8393  addi         x7, x21, 0
    110: 000b0413  addi         x8, x22, 0
    114: 00038f93  addi         x31, x7, 0
    118: 00040f13  addi         x30, x8, 0
    11c: 00038eb7  lui          x29, 0x00038  # x29 = 0x00038000 · arc_apb_reset_unit + 0x8000
    120: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00037800 · arc_apb_reset_unit + 0x7800
    124: 2b5000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000128
    128: 249000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x0000012c
    12c: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    130: 90448493  addi         x9, x9, -1788  # x9 = 0x0000e904
    134: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e904
    138: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
    13c: 02945433  divu         x8, x8, x9
    140: 00941413  slli         x8, x8, 9
    144: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
loc_148:
    148: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    14c: 8d068693  addi         x13, x13, -1840  # x13 = 0x000008d0
    150: 00d47c63  bgeu         x8, x13, 0x00000168  # target 0x00000168
    154: 02f00613  addi         x12, x0, 47  # x12 = 0x0000002f
    158: 02c454b3  divu         x9, x8, x12
    15c: 02c485b3  mul          x11, x9, x12
    160: 40b405b3  sub          x11, x8, x11
    164: 01c0006f  jal          x0, 0x00000180  # target 0x00000180
loc_168:
    168: 40d406b3  sub          x13, x8, x13
    16c: 02e00613  addi         x12, x0, 46  # x12 = 0x0000002e
    170: 02c6d4b3  divu         x9, x13, x12
    174: 02c485b3  mul          x11, x9, x12
    178: 40b685b3  sub          x11, x13, x11
    17c: 03048493  addi         x9, x9, 48
loc_180:
    180: 07f40513  addi         x10, x8, 127
    184: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    188: 8d078793  addi         x15, x15, -1840  # x15 = 0x000008d0
    18c: 00f57c63  bgeu         x10, x15, 0x000001a4  # target 0x000001a4
    190: 02f00713  addi         x14, x0, 47  # x14 = 0x0000002f
    194: 02e55633  divu         x12, x10, x14
    198: 02e606b3  mul          x13, x12, x14
    19c: 40d506b3  sub          x13, x10, x13
    1a0: 01c0006f  jal          x0, 0x000001bc  # target 0x000001bc
loc_1a4:
    1a4: 40f507b3  sub          x15, x10, x15
    1a8: 02e00713  addi         x14, x0, 46  # x14 = 0x0000002e
    1ac: 02e7d633  divu         x12, x15, x14
    1b0: 02e606b3  mul          x13, x12, x14
    1b4: 40d786b3  sub          x13, x15, x13
    1b8: 03060613  addi         x12, x12, 48
loc_1bc:
    1bc: 00048513  addi         x10, x9, 0
    1c0: 195000ef  jal          x1, 0x00000b54  # target 0x00000b54; x1 = 0x000001c4
    1c4: 1ad000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x000001c8
    1c8: 00023737  lui          x14, 0x00023  # x14 = 0x00023000
    1cc: 80070713  addi         x14, x14, -2048  # x14 = 0x00022800
loc_1d0:
    1d0: 00050f93  addi         x31, x10, 0
    1d4: 2f5000ef  jal          x1, 0x00000cc8  # target 0x00000cc8; x1 = 0x000001d8
    1d8: 000a8793  addi         x15, x21, 0
    1dc: 000b0813  addi         x16, x22, 0
    1e0: 00078f93  addi         x31, x15, 0
    1e4: 00080f13  addi         x30, x16, 0
    1e8: 00070e93  addi         x29, x14, 0
    1ec: 1ed000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000001f0
    1f0: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    1f4: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    1f8: 00f70733  add          x14, x14, x15
    1fc: 00150513  addi         x10, x10, 1
    200: fca678e3  bgeu         x12, x10, 0x000001d0  # target 0x000001d0
    204: 16d000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x00000208
    208: 00048513  addi         x10, x9, 0
    20c: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    210: 00839693  slli         x13, x7, 8
    214: 00020737  lui          x14, 0x00020  # x14 = 0x00020000
    218: 80070713  addi         x14, x14, -2048  # x14 = 0x0001f800
    21c: 00e686b3  add          x13, x13, x14
loc_220:
    220: 02e00713  addi         x14, x0, 46  # x14 = 0x0000002e
    224: 03000793  addi         x15, x0, 48  # x15 = 0x00000030
    228: 00f57463  bgeu         x10, x15, 0x00000230  # target 0x00000230
    22c: 00170713  addi         x14, x14, 1  # x14 = 0x0000002f
loc_230:
    230: 40b70733  sub          x14, x14, x11
    234: 00f5f793  andi         x15, x11, 15
    238: 40f007b3  sub          x15, x0, x15
    23c: 01078793  addi         x15, x15, 16
    240: 00e7f463  bgeu         x15, x14, 0x00000248  # target 0x00000248
    244: 00078713  addi         x14, x15, 0
loc_248:
    248: 03f67793  andi         x15, x12, 63
    24c: 40f007b3  sub          x15, x0, x15
    250: 04078793  addi         x15, x15, 64
    254: 00e7f463  bgeu         x15, x14, 0x0000025c  # target 0x0000025c
    258: 00078713  addi         x14, x15, 0
loc_25c:
    25c: 40950833  sub          x16, x10, x9
    260: 00b81813  slli         x16, x16, 11
    264: 00f5f793  andi         x15, x11, 15
    268: 00179793  slli         x15, x15, 1
    26c: 0105fa13  andi         x20, x11, 16
    270: 005a1a13  slli         x20, x20, 5
    274: 0147e7b3  or           x15, x15, x20
    278: 1e05fa13  andi         x20, x11, 480
    27c: 0147e7b3  or           x15, x15, x20
    280: 0095da13  srli         x20, x11, 9
    284: 00aa1a13  slli         x20, x20, 10
    288: 0147e7b3  or           x15, x15, x20
    28c: 00f80833  add          x16, x16, x15
    290: 00023a37  lui          x20, 0x00023  # x20 = 0x00023000
    294: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00022800
    298: 01480833  add          x16, x16, x20
    29c: 00161893  slli         x17, x12, 1
    2a0: 00d888b3  add          x17, x17, x13
    2a4: 04064913  xori         x18, x12, 64
    2a8: 00191913  slli         x18, x18, 1
    2ac: 00d90933  add          x18, x18, x13
    2b0: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2b4: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    2b8: 01490933  add          x18, x18, x20
    2bc: 04067993  andi         x19, x12, 64
    2c0: 00999993  slli         x19, x19, 9
    2c4: 00080f93  addi         x31, x16, 0
    2c8: 00088f13  addi         x30, x17, 0
    2cc: 00090e93  addi         x29, x18, 0
    2d0: 00070e13  addi         x28, x14, 0
    2d4: 00098d93  addi         x27, x19, 0
loc_2d8:
    2d8: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    2dc: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    2e0: 01ba4a33  xor          x20, x20, x27
    2e4: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    2e8: 002f8f93  addi         x31, x31, 2
    2ec: 002f0f13  addi         x30, x30, 2
    2f0: 002e8e93  addi         x29, x29, 2
    2f4: fffe0e13  addi         x28, x28, -1
    2f8: fe0e10e3  bne          x28, x0, 0x000002d8  # target 0x000002d8
    2fc: 00e60633  add          x12, x12, x14
    300: 00e585b3  add          x11, x11, x14
    304: 02e00793  addi         x15, x0, 46  # x15 = 0x0000002e
    308: 03000993  addi         x19, x0, 48  # x19 = 0x00000030
    30c: 01357463  bgeu         x10, x19, 0x00000314  # target 0x00000314
    310: 00178793  addi         x15, x15, 1  # x15 = 0x0000002f
loc_314:
    314: 00f59663  bne          x11, x15, 0x00000320  # target 0x00000320
    318: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    31c: 00150513  addi         x10, x10, 1
loc_320:
    320: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    324: eef66ee3  bltu         x12, x15, 0x00000220  # target 0x00000220
    328: 08040413  addi         x8, x8, 128
    32c: 00138393  addi         x7, x7, 1
    330: 00400493  addi         x9, x0, 4  # x9 = 0x00000004
    334: e0939ae3  bne          x7, x9, 0x00000148  # target 0x00000148
    338: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    33c: 90448493  addi         x9, x9, -1788  # x9 = 0x0000e904
    340: 0004a403  lw           x8, 0(x9)  # param attention_core; 0x0000e904
    344: 00c00493  addi         x9, x0, 12  # x9 = 0x0000000c
    348: 02945433  divu         x8, x8, x9
    34c: 00045413  srli         x8, x8, 0
    350: 00741413  slli         x8, x8, 7
    354: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    358: 2a000693  addi         x13, x0, 672  # x13 = 0x000002a0
    35c: 00d47c63  bgeu         x8, x13, 0x00000374  # target 0x00000374
    360: 00c00613  addi         x12, x0, 12  # x12 = 0x0000000c
    364: 02c454b3  divu         x9, x8, x12
    368: 02c485b3  mul          x11, x9, x12
    36c: 40b405b3  sub          x11, x8, x11
    370: 01c0006f  jal          x0, 0x0000038c  # target 0x0000038c
loc_374:
    374: 40d406b3  sub          x13, x8, x13
    378: 00b00613  addi         x12, x0, 11  # x12 = 0x0000000b
    37c: 02c6d4b3  divu         x9, x13, x12
    380: 02c485b3  mul          x11, x9, x12
    384: 40b685b3  sub          x11, x13, x11
    388: 03848493  addi         x9, x9, 56
loc_38c:
    38c: 07f40513  addi         x10, x8, 127
    390: 2a000793  addi         x15, x0, 672  # x15 = 0x000002a0
    394: 00f57c63  bgeu         x10, x15, 0x000003ac  # target 0x000003ac
    398: 00c00713  addi         x14, x0, 12  # x14 = 0x0000000c
    39c: 02e55633  divu         x12, x10, x14
    3a0: 02e606b3  mul          x13, x12, x14
    3a4: 40d506b3  sub          x13, x10, x13
    3a8: 01c0006f  jal          x0, 0x000003c4  # target 0x000003c4
loc_3ac:
    3ac: 40f507b3  sub          x15, x10, x15
    3b0: 00b00713  addi         x14, x0, 11  # x14 = 0x0000000b
    3b4: 02e7d633  divu         x12, x15, x14
    3b8: 02e606b3  mul          x13, x12, x14
    3bc: 40d786b3  sub          x13, x15, x13
    3c0: 03860613  addi         x12, x12, 56
loc_3c4:
    3c4: 00048513  addi         x10, x9, 0
    3c8: 78c000ef  jal          x1, 0x00000b54  # target 0x00000b54; x1 = 0x000003cc
    3cc: 7a4000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x000003d0
    3d0: 00023737  lui          x14, 0x00023  # x14 = 0x00023000
    3d4: 80070713  addi         x14, x14, -2048  # x14 = 0x00022800
loc_3d8:
    3d8: 00050f93  addi         x31, x10, 0
    3dc: 139000ef  jal          x1, 0x00000d14  # target 0x00000d14; x1 = 0x000003e0
    3e0: 000a8793  addi         x15, x21, 0
    3e4: 000b0813  addi         x16, x22, 0
    3e8: 00078f93  addi         x31, x15, 0
    3ec: 00080f13  addi         x30, x16, 0
    3f0: 00070e93  addi         x29, x14, 0
    3f4: 7e4000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000003f8
    3f8: 00050f93  addi         x31, x10, 0
    3fc: 165000ef  jal          x1, 0x00000d60  # target 0x00000d60; x1 = 0x00000400
    400: 000a8793  addi         x15, x21, 0
    404: 000b0813  addi         x16, x22, 0
    408: 0000a8b7  lui          x17, 0x0000a  # x17 = 0x0000a000
    40c: 00e888b3  add          x17, x17, x14
    410: 00078f93  addi         x31, x15, 0
    414: 00080f13  addi         x30, x16, 0
    418: 00088e93  addi         x29, x17, 0
    41c: 7bc000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000420
    420: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    424: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    428: 00f70733  add          x14, x14, x15
    42c: 00150513  addi         x10, x10, 1
    430: faa674e3  bgeu         x12, x10, 0x000003d8  # target 0x000003d8
    434: 73c000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x00000438
    438: 00048513  addi         x10, x9, 0
    43c: 00000613  addi         x12, x0, 0  # x12 = 0x00000000
    440: 00839693  slli         x13, x7, 8
    444: 00020737  lui          x14, 0x00020  # x14 = 0x00020000
    448: 80070713  addi         x14, x14, -2048  # x14 = 0x0001f800
    44c: 00e686b3  add          x13, x13, x14
loc_450:
    450: 00b00713  addi         x14, x0, 11  # x14 = 0x0000000b
    454: 03800793  addi         x15, x0, 56  # x15 = 0x00000038
    458: 00f57463  bgeu         x10, x15, 0x00000460  # target 0x00000460
    45c: 00170713  addi         x14, x14, 1  # x14 = 0x0000000c
loc_460:
    460: 40b70733  sub          x14, x14, x11
    464: 00f5f793  andi         x15, x11, 15
    468: 40f007b3  sub          x15, x0, x15
    46c: 01078793  addi         x15, x15, 16
    470: 00e7f463  bgeu         x15, x14, 0x00000478  # target 0x00000478
    474: 00078713  addi         x14, x15, 0
loc_478:
    478: 03f67793  andi         x15, x12, 63
    47c: 40f007b3  sub          x15, x0, x15
    480: 04078793  addi         x15, x15, 64
    484: 00e7f463  bgeu         x15, x14, 0x0000048c  # target 0x0000048c
    488: 00078713  addi         x14, x15, 0
loc_48c:
    48c: 40950833  sub          x16, x10, x9
    490: 00b81813  slli         x16, x16, 11
    494: 00f5f793  andi         x15, x11, 15
    498: 00179793  slli         x15, x15, 1
    49c: 0105fa13  andi         x20, x11, 16
    4a0: 005a1a13  slli         x20, x20, 5
    4a4: 0147e7b3  or           x15, x15, x20
    4a8: 1e05fa13  andi         x20, x11, 480
    4ac: 0147e7b3  or           x15, x15, x20
    4b0: 0095da13  srli         x20, x11, 9
    4b4: 00aa1a13  slli         x20, x20, 10
    4b8: 0147e7b3  or           x15, x15, x20
    4bc: 00f80833  add          x16, x16, x15
    4c0: 00023a37  lui          x20, 0x00023  # x20 = 0x00023000
    4c4: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00022800
    4c8: 01480833  add          x16, x16, x20
    4cc: 00161893  slli         x17, x12, 1
    4d0: 00d888b3  add          x17, x17, x13
    4d4: 04064913  xori         x18, x12, 64
    4d8: 00191913  slli         x18, x18, 1
    4dc: 00d90933  add          x18, x18, x13
    4e0: 00001a37  lui          x20, 0x00001  # x20 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4e4: 800a0a13  addi         x20, x20, -2048  # x20 = 0x00000800
    4e8: 01490933  add          x18, x18, x20
    4ec: 04067993  andi         x19, x12, 64
    4f0: 00999993  slli         x19, x19, 9
    4f4: 0000aa37  lui          x20, 0x0000a  # x20 = 0x0000a000
    4f8: 010a0a33  add          x20, x20, x16
    4fc: 00161a93  slli         x21, x12, 1
    500: 00037b37  lui          x22, 0x00037  # x22 = 0x00037000 · arc_apb_reset_unit + 0x7000
    504: 800b0b13  addi         x22, x22, -2048  # x22 = 0x00036800 · arc_apb_reset_unit + 0x6800
    508: 016a8ab3  add          x21, x21, x22
    50c: ffc10113  addi         x2, x2, -4
    510: 01412023  sw           x20, 0(x2)  # Address depends on runtime register values
    514: 00080f93  addi         x31, x16, 0
    518: 00088f13  addi         x30, x17, 0
    51c: 00090e93  addi         x29, x18, 0
    520: 00070e13  addi         x28, x14, 0
    524: 00098d93  addi         x27, x19, 0
    528: 000a0d13  addi         x26, x20, 0
    52c: 000a8c93  addi         x25, x21, 0
loc_530:
    530: 000fda03  lhu          x20, 0(x31)  # Address depends on runtime register values
    534: 014f1023  sh           x20, 0(x30)  # Address depends on runtime register values
    538: 01ba4a33  xor          x20, x20, x27
    53c: 014e9023  sh           x20, 0(x29)  # Address depends on runtime register values
    540: 000d5a03  lhu          x20, 0(x26)  # Address depends on runtime register values
    544: 014c9023  sh           x20, 0(x25)  # Address depends on runtime register values
    548: 002d0d13  addi         x26, x26, 2
    54c: 002c8c93  addi         x25, x25, 2
    550: 002f8f93  addi         x31, x31, 2
    554: 002f0f13  addi         x30, x30, 2
    558: 002e8e93  addi         x29, x29, 2
    55c: fffe0e13  addi         x28, x28, -1
    560: fc0e18e3  bne          x28, x0, 0x00000530  # target 0x00000530
    564: 00012a03  lw           x20, 0(x2)  # Address depends on runtime register values
    568: 00410113  addi         x2, x2, 4
    56c: 00e60633  add          x12, x12, x14
    570: 00e585b3  add          x11, x11, x14
    574: 00b00793  addi         x15, x0, 11  # x15 = 0x0000000b
    578: 03800993  addi         x19, x0, 56  # x19 = 0x00000038
    57c: 01357463  bgeu         x10, x19, 0x00000584  # target 0x00000584
    580: 00178793  addi         x15, x15, 1  # x15 = 0x0000000c
loc_584:
    584: 00f59663  bne          x11, x15, 0x00000590  # target 0x00000590
    588: 00000593  addi         x11, x0, 0  # x11 = 0x00000000
    58c: 00150513  addi         x10, x10, 1
loc_590:
    590: 08000793  addi         x15, x0, 128  # x15 = 0x00000080
    594: eaf66ee3  bltu         x12, x15, 0x00000450  # target 0x00000450
    598: 000373b7  lui          x7, 0x00037  # x7 = 0x00037000 · arc_apb_reset_unit + 0x7000
    59c: 006383b3  add          x7, x7, x6
    5a0: 00038f93  addi         x31, x7, 0
    5a4: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5a8: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00020800
    5ac: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5b0: 7fc000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x000005b4
    5b4: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    5b8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00020800
    5bc: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5c0: 900f0f13  addi         x30, x30, -1792  # x30 = 0x00020900
    5c4: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5c8: 039000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x000005cc
    5cc: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    5d0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00020800
    5d4: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5d8: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00020a00
    5dc: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5e0: 021000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x000005e4
    5e4: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    5e8: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00020800
    5ec: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    5f0: b00f0f13  addi         x30, x30, -1280  # x30 = 0x00020b00
    5f4: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    5f8: 009000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x000005fc
    5fc: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    600: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00020800
    604: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    608: c00f0f13  addi         x30, x30, -1024  # x30 = 0x00020c00
    60c: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    610: 7f0000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x00000614
    614: 000383b7  lui          x7, 0x00038  # x7 = 0x00038000 · arc_apb_reset_unit + 0x8000
    618: 80038393  addi         x7, x7, -2048  # x7 = 0x00037800 · arc_apb_reset_unit + 0x7800
    61c: 006383b3  add          x7, x7, x6
    620: 00038f93  addi         x31, x7, 0
    624: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    628: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    62c: 780000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x00000630
    630: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    634: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    638: 100f0f13  addi         x30, x30, 256  # x30 = 0x00021100
    63c: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    640: 7c0000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x00000644
    644: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    648: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    64c: 200f0f13  addi         x30, x30, 512  # x30 = 0x00021200
    650: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    654: 7ac000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x00000658
    658: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    65c: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    660: 300f0f13  addi         x30, x30, 768  # x30 = 0x00021300
    664: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    668: 798000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x0000066c
    66c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    670: 00021f37  lui          x30, 0x00021  # x30 = 0x00021000
    674: 400f0f13  addi         x30, x30, 1024  # x30 = 0x00021400
    678: 04000e93  addi         x29, x0, 64  # x29 = 0x00000040
    67c: 784000ef  jal          x1, 0x00000e00  # target 0x00000e00; x1 = 0x00000680
    680: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    684: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    688: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    68c: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    690: 00520233  add          x4, x4, x5
    694: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    698: 80030313  addi         x6, x6, -2048  # x6 = 0x00021800
    69c: 00626663  bltu         x4, x6, 0x000006a8  # target 0x000006a8
    6a0: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    6a4: 40720233  sub          x4, x4, x7
loc_6a8:
    6a8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6ac: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    6b0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    6b4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6b8: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    6bc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    6c0: 00420213  addi         x4, x4, 4
    6c4: 01021213  slli         x4, x4, 16
    6c8: 01025213  srli         x4, x4, 16
    6cc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6d0: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    6d4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    6d8: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    6dc: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    6e0: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    6e4: 0ff0000f  fence        0xf, 0xf
    6e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6ec: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    6f0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    6f4: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_6f8:
    6f8: ffb4f437  lui          x8, 0xffb4f  # x8 = 0xffb4f000
    6fc: 02840413  addi         x8, x8, 40  # x8 = 0xffb4f028
    700: 00045283  lhu          x5, 0(x8)  # 0xffb4f028
    704: 40428333  sub          x6, x5, x4
    708: 01031313  slli         x6, x6, 16
    70c: 01035313  srli         x6, x6, 16
    710: 00737663  bgeu         x6, x7, 0x0000071c  # target 0x0000071c
    714: 0ff0000f  fence        0xf, 0xf
    718: fe1ff06f  jal          x0, 0x000006f8  # target 0x000006f8
loc_71c:
    71c: 0ff0000f  fence        0xf, 0xf
    720: 0000f3b7  lui          x7, 0x0000f  # x7 = 0x0000f000
    724: 90438393  addi         x7, x7, -1788  # x7 = 0x0000e904
    728: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x0000e904
    72c: 00c00393  addi         x7, x0, 12  # x7 = 0x0000000c
    730: 02725233  divu         x4, x4, x7
    734: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    738: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    73c: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    740: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    744: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    748: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    74c: 00747a63  bgeu         x8, x7, 0x00000760  # target 0x00000760
    750: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    754: 08000413  addi         x8, x0, 128  # x8 = 0x00000080
    758: 00747463  bgeu         x8, x7, 0x00000760  # target 0x00000760
    75c: 00c00313  addi         x6, x0, 12  # x6 = 0x0000000c
loc_760:
    760: 0000f4b7  lui          x9, 0x0000f  # x9 = 0x0000f000
    764: 90848493  addi         x9, x9, -1784  # x9 = 0x0000e908
    768: 0004a383  lw           x7, 0(x9)  # param attention_phase; 0x0000e908
    76c: 79000593  addi         x11, x0, 1936  # x11 = 0x00000790
    770: 0005a483  lw           x9, 0(x11)  # param kv_blocks; 0x00000790
    774: 00100413  addi         x8, x0, 1  # x8 = 0x00000001
    778: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
    77c: 00957a63  bgeu         x10, x9, 0x00000790  # target 0x00000790
    780: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    784: 08000513  addi         x10, x0, 128  # x10 = 0x00000080
    788: 00957463  bgeu         x10, x9, 0x00000790  # target 0x00000790
    78c: 00c00413  addi         x8, x0, 12  # x8 = 0x0000000c
loc_790:
    790: 008282b3  add          x5, x5, x8
    794: fff28293  addi         x5, x5, -1
    798: 407282b3  sub          x5, x5, x7
    79c: 0282d2b3  divu         x5, x5, x8
    7a0: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    7a4: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7a8: 0005a383  lw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888
    7ac: 00002437  lui          x8, 0x00002  # x8 = 0x00002000
    7b0: 008383b3  add          x7, x7, x8
    7b4: 000114b7  lui          x9, 0x00011  # x9 = 0x00011000
    7b8: 0093e663  bltu         x7, x9, 0x000007c4  # target 0x000007c4
    7bc: 00002537  lui          x10, 0x00002  # x10 = 0x00002000
    7c0: 40a383b3  sub          x7, x7, x10
loc_7c4:
    7c4: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
    7c8: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
    7cc: 0075a023  sw           x7, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    7d0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7d4: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7d8: 00042383  lw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c
    7dc: 00438393  addi         x7, x7, 4
    7e0: 01039393  slli         x7, x7, 16
    7e4: 0103d393  srli         x7, x7, 16
    7e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7ec: 88c40413  addi         x8, x8, -1908  # x8 = 0xffb0088c · riscv_local_mem + 0x88c
    7f0: 00742023  sw           x7, 0(x8)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    7f4: ffb48437  lui          x8, 0xffb48  # x8 = 0xffb48000
    7f8: 02840413  addi         x8, x8, 40  # x8 = 0xffb48028
    7fc: 00742023  sw           x7, 0(x8)  # 0xffb48028; write runtime value
    800: 0ff0000f  fence        0xf, 0xf
    804: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    808: 00028413  addi         x8, x5, 0
loc_80c:
    80c: 3483f263  bgeu         x7, x8, 0x00000b50  # target 0x00000b50
    810: 00025493  srli         x9, x4, 0
    814: 00a49493  slli         x9, x9, 10
    818: 02638533  mul          x10, x7, x6
    81c: 0000f637  lui          x12, 0x0000f  # x12 = 0x0000f000
    820: 90860613  addi         x12, x12, -1784  # x12 = 0x0000e908
    824: 00062583  lw           x11, 0(x12)  # param attention_phase; 0x0000e908
    828: 00b50533  add          x10, x10, x11
    82c: 00251513  slli         x10, x10, 2
    830: 00a484b3  add          x9, x9, x10
    834: 320000ef  jal          x1, 0x00000b54  # target 0x00000b54; x1 = 0x00000838
    838: 338000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x0000083c
    83c: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    840: 89480813  addi         x16, x16, -1900  # x16 = 0xffb00894 · riscv_local_mem + 0x894
    844: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x894 · 0xffb00894
loc_848:
    848: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    84c: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    850: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    854: 40c586b3  sub          x13, x11, x12
    858: 01069693  slli         x13, x13, 16
    85c: 0106d693  srli         x13, x13, 16
    860: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    864: 40d70733  sub          x14, x14, x13
    868: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    86c: 00f77663  bgeu         x14, x15, 0x00000878  # target 0x00000878
    870: 0ff0000f  fence        0xf, 0xf
    874: fd5ff06f  jal          x0, 0x00000848  # target 0x00000848
loc_878:
    878: 0ff0000f  fence        0xf, 0xf
    87c: 00048593  addi         x11, x9, 0
    880: 00058f93  addi         x31, x11, 0
    884: 598000ef  jal          x1, 0x00000e1c  # target 0x00000e1c; x1 = 0x00000888
    888: 000a8613  addi         x12, x21, 0
    88c: 000b0693  addi         x13, x22, 0
    890: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    894: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    898: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    89c: 00060f93  addi         x31, x12, 0
    8a0: 00068f13  addi         x30, x13, 0
    8a4: 00070e93  addi         x29, x14, 0
    8a8: 330000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000008ac
    8ac: 00148593  addi         x11, x9, 1
    8b0: 00058f93  addi         x31, x11, 0
    8b4: 568000ef  jal          x1, 0x00000e1c  # target 0x00000e1c; x1 = 0x000008b8
    8b8: 000a8613  addi         x12, x21, 0
    8bc: 000b0693  addi         x13, x22, 0
    8c0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    8c4: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    8c8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    8cc: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8d0: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    8d4: 00f70733  add          x14, x14, x15
    8d8: 00060f93  addi         x31, x12, 0
    8dc: 00068f13  addi         x30, x13, 0
    8e0: 00070e93  addi         x29, x14, 0
    8e4: 2f4000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000008e8
    8e8: 00248593  addi         x11, x9, 2
    8ec: 00058f93  addi         x31, x11, 0
    8f0: 52c000ef  jal          x1, 0x00000e1c  # target 0x00000e1c; x1 = 0x000008f4
    8f4: 000a8613  addi         x12, x21, 0
    8f8: 000b0693  addi         x13, x22, 0
    8fc: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    900: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    904: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    908: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    90c: 00f70733  add          x14, x14, x15
    910: 00060f93  addi         x31, x12, 0
    914: 00068f13  addi         x30, x13, 0
    918: 00070e93  addi         x29, x14, 0
    91c: 2bc000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000920
    920: 00348593  addi         x11, x9, 3
    924: 00058f93  addi         x31, x11, 0
    928: 4f4000ef  jal          x1, 0x00000e1c  # target 0x00000e1c; x1 = 0x0000092c
    92c: 000a8613  addi         x12, x21, 0
    930: 000b0693  addi         x13, x22, 0
    934: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    938: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    93c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    940: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    944: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    948: 00f70733  add          x14, x14, x15
    94c: 00060f93  addi         x31, x12, 0
    950: 00068f13  addi         x30, x13, 0
    954: 00070e93  addi         x29, x14, 0
    958: 280000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x0000095c
    95c: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    960: 89c80813  addi         x16, x16, -1892  # x16 = 0xffb0089c · riscv_local_mem + 0x89c
    964: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x89c · 0xffb0089c
loc_968:
    968: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    96c: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    970: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    974: 40c586b3  sub          x13, x11, x12
    978: 01069693  slli         x13, x13, 16
    97c: 0106d693  srli         x13, x13, 16
    980: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    984: 40d70733  sub          x14, x14, x13
    988: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    98c: 00f77663  bgeu         x14, x15, 0x00000998  # target 0x00000998
    990: 0ff0000f  fence        0xf, 0xf
    994: fd5ff06f  jal          x0, 0x00000968  # target 0x00000968
loc_998:
    998: 0ff0000f  fence        0xf, 0xf
    99c: 00048593  addi         x11, x9, 0
    9a0: 00058f93  addi         x31, x11, 0
    9a4: 4c4000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x000009a8
    9a8: 000a8613  addi         x12, x21, 0
    9ac: 000b0693  addi         x13, x22, 0
    9b0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9b4: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    9b8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    9bc: 00060f93  addi         x31, x12, 0
    9c0: 00068f13  addi         x30, x13, 0
    9c4: 00070e93  addi         x29, x14, 0
    9c8: 210000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x000009cc
    9cc: 00148593  addi         x11, x9, 1
    9d0: 00058f93  addi         x31, x11, 0
    9d4: 494000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x000009d8
    9d8: 000a8613  addi         x12, x21, 0
    9dc: 000b0693  addi         x13, x22, 0
    9e0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    9e4: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    9e8: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    9ec: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9f0: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    9f4: 00f70733  add          x14, x14, x15
    9f8: 00060f93  addi         x31, x12, 0
    9fc: 00068f13  addi         x30, x13, 0
    a00: 00070e93  addi         x29, x14, 0
    a04: 1d4000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000a08
    a08: 00248593  addi         x11, x9, 2
    a0c: 00058f93  addi         x31, x11, 0
    a10: 458000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x00000a14
    a14: 000a8613  addi         x12, x21, 0
    a18: 000b0693  addi         x13, x22, 0
    a1c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a20: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    a24: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    a28: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a2c: 00f70733  add          x14, x14, x15
    a30: 00060f93  addi         x31, x12, 0
    a34: 00068f13  addi         x30, x13, 0
    a38: 00070e93  addi         x29, x14, 0
    a3c: 19c000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000a40
    a40: 00348593  addi         x11, x9, 3
    a44: 00058f93  addi         x31, x11, 0
    a48: 420000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x00000a4c
    a4c: 000a8613  addi         x12, x21, 0
    a50: 000b0693  addi         x13, x22, 0
    a54: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a58: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    a5c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    a60: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    a64: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    a68: 00f70733  add          x14, x14, x15
    a6c: 00060f93  addi         x31, x12, 0
    a70: 00068f13  addi         x30, x13, 0
    a74: 00070e93  addi         x29, x14, 0
    a78: 160000ef  jal          x1, 0x00000bd8  # target 0x00000bd8; x1 = 0x00000a7c
    a7c: 0f4000ef  jal          x1, 0x00000b70  # target 0x00000b70; x1 = 0x00000a80
    a80: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a84: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    a88: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890
    a8c: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    a90: 00c585b3  add          x11, x11, x12
    a94: 000156b7  lui          x13, 0x00015  # x13 = 0x00015000
    a98: 00d5e663  bltu         x11, x13, 0x00000aa4  # target 0x00000aa4
    a9c: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    aa0: 40e585b3  sub          x11, x11, x14
loc_aa4:
    aa4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    aa8: 89078793  addi         x15, x15, -1904  # x15 = 0xffb00890 · riscv_local_mem + 0x890
    aac: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x890 · 0xffb00890; write runtime value
    ab0: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    ab4: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    ab8: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894
    abc: 00458593  addi         x11, x11, 4
    ac0: 01059593  slli         x11, x11, 16
    ac4: 0105d593  srli         x11, x11, 16
    ac8: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    acc: 89460613  addi         x12, x12, -1900  # x12 = 0xffb00894 · riscv_local_mem + 0x894
    ad0: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x894 · 0xffb00894; write runtime value
    ad4: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    ad8: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    adc: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    ae0: 0ff0000f  fence        0xf, 0xf
    ae4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ae8: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    aec: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898
    af0: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    af4: 00c585b3  add          x11, x11, x12
    af8: 000196b7  lui          x13, 0x00019  # x13 = 0x00019000
    afc: 00d5e663  bltu         x11, x13, 0x00000b08  # target 0x00000b08
    b00: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    b04: 40e585b3  sub          x11, x11, x14
loc_b08:
    b08: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    b0c: 89878793  addi         x15, x15, -1896  # x15 = 0xffb00898 · riscv_local_mem + 0x898
    b10: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    b14: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b18: 89c60613  addi         x12, x12, -1892  # x12 = 0xffb0089c · riscv_local_mem + 0x89c
    b1c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x89c · 0xffb0089c
    b20: 00458593  addi         x11, x11, 4
    b24: 01059593  slli         x11, x11, 16
    b28: 0105d593  srli         x11, x11, 16
    b2c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b30: 89c60613  addi         x12, x12, -1892  # x12 = 0xffb0089c · riscv_local_mem + 0x89c
    b34: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    b38: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    b3c: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    b40: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    b44: 0ff0000f  fence        0xf, 0xf
    b48: 00138393  addi         x7, x7, 1
    b4c: cc1ff06f  jal          x0, 0x0000080c  # target 0x0000080c
loc_b50:
    b50: 3640006f  jal          x0, 0x00000eb4  # target 0x00000eb4
loc_b54:
    b54: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    b58: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    b5c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    b60: 000a0463  beq          x20, x0, 0x00000b68  # target 0x00000b68
    b64: ff1ff06f  jal          x0, 0x00000b54  # target 0x00000b54
loc_b68:
    b68: 0ff0000f  fence        0xf, 0xf
    b6c: 00008067  jalr         x0, 0(x1)
loc_b70:
    b70: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    b74: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    b78: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    b7c: 000a0463  beq          x20, x0, 0x00000b84  # target 0x00000b84
    b80: ff1ff06f  jal          x0, 0x00000b70  # target 0x00000b70
loc_b84:
    b84: 0ff0000f  fence        0xf, 0xf
    b88: 00008067  jalr         x0, 0(x1)
loc_b8c:
    b8c: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    b90: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
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
    bd8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bdc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    be0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    be4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    be8: 015a6463  bltu         x20, x21, 0x00000bf0  # target 0x00000bf0
    bec: fedff06f  jal          x0, 0x00000bd8  # target 0x00000bd8
loc_bf0:
    bf0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bf4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    bf8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    bfc: 014a1a13  slli         x20, x20, 20
    c00: 014a5a13  srli         x20, x20, 20
    c04: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_c08:
    c08: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    c0c: 000b0463  beq          x22, x0, 0x00000c14  # target 0x00000c14
    c10: ff9ff06f  jal          x0, 0x00000c08  # target 0x00000c08
loc_c14:
    c14: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    c18: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    c1c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    c20: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    c24: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    c28: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    c2c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    c30: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    c34: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    c38: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    c3c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    c40: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    c44: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    c48: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    c4c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    c50: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    c54: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    c58: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    c5c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    c60: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    c64: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    c68: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_c6c:
    c6c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    c70: 000b0463  beq          x22, x0, 0x00000c78  # target 0x00000c78
    c74: ff9ff06f  jal          x0, 0x00000c6c  # target 0x00000c6c
loc_c78:
    c78: 00008067  jalr         x0, 0(x1)
loc_c7c:
    c7c: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    c80: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    c84: 007a7d13  andi         x26, x20, 7
    c88: ff8a7a13  andi         x20, x20, -8
    c8c: 01af8ab3  add          x21, x31, x26
    c90: 007afb93  andi         x23, x21, 7
    c94: 003ada93  srli         x21, x21, 3
    c98: 00ba9a93  slli         x21, x21, 11
    c9c: 014a8ab3  add          x21, x21, x20
    ca0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ca0
    ca4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000cb8
    ca8: 001b9b93  slli         x23, x23, 1
    cac: 017b0b33  add          x22, x22, x23
    cb0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    cb4: 00008067  jalr         x0, 0(x1)
    cb8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    cbc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    cc0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    cc4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_cc8:
    cc8: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    ccc: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_q_compact; 0x00000798
    cd0: 007a7d13  andi         x26, x20, 7
    cd4: ff8a7a13  andi         x20, x20, -8
    cd8: 01af8ab3  add          x21, x31, x26
    cdc: 007afb93  andi         x23, x21, 7
    ce0: 003ada93  srli         x21, x21, 3
    ce4: 00ba9a93  slli         x21, x21, 11
    ce8: 014a8ab3  add          x21, x21, x20
    cec: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000cec
    cf0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d04
    cf4: 001b9b93  slli         x23, x23, 1
    cf8: 017b0b33  add          x22, x22, x23
    cfc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d00: 00008067  jalr         x0, 0(x1)
    d04: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d08: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d0c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d10: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d14:
    d14: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    d18: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_k_compact; 0x0000079c
    d1c: 007a7d13  andi         x26, x20, 7
    d20: ff8a7a13  andi         x20, x20, -8
    d24: 01af8ab3  add          x21, x31, x26
    d28: 007afb93  andi         x23, x21, 7
    d2c: 003ada93  srli         x21, x21, 3
    d30: 00ba9a93  slli         x21, x21, 11
    d34: 014a8ab3  add          x21, x21, x20
    d38: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d38
    d3c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d50
    d40: 001b9b93  slli         x23, x23, 1
    d44: 017b0b33  add          x22, x22, x23
    d48: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d4c: 00008067  jalr         x0, 0(x1)
    d50: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d54: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d58: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d5c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d60:
    d60: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    d64: 000aaa03  lw           x20, 0(x21)  # param attention_e2e_v_compact; 0x000007a0
    d68: 007a7d13  andi         x26, x20, 7
    d6c: ff8a7a13  andi         x20, x20, -8
    d70: 01af8ab3  add          x21, x31, x26
    d74: 007afb93  andi         x23, x21, 7
    d78: 003ada93  srli         x21, x21, 3
    d7c: 00ba9a93  slli         x21, x21, 11
    d80: 014a8ab3  add          x21, x21, x20
    d84: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d84
    d88: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d9c
    d8c: 001b9b93  slli         x23, x23, 1
    d90: 017b0b33  add          x22, x22, x23
    d94: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d98: 00008067  jalr         x0, 0(x1)
    d9c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    da0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    da4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    da8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_dac:
    dac: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    db0: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    db4: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    db8: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    dbc: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    dc0: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    dc4: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    dc8: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    dcc: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    dd0: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    dd4: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    dd8: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    ddc: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    de0: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    de4: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    de8: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    dec: 020f8f93  addi         x31, x31, 32
    df0: 020f0f13  addi         x30, x30, 32
    df4: ff8e8e93  addi         x29, x29, -8
    df8: fa0e9ae3  bne          x29, x0, 0x00000dac  # target 0x00000dac
    dfc: 00008067  jalr         x0, 0(x1)
loc_e00:
    e00: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    e04: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    e08: 004f8f93  addi         x31, x31, 4
    e0c: 004f0f13  addi         x30, x30, 4
    e10: fffe8e93  addi         x29, x29, -1
    e14: fe0e96e3  bne          x29, x0, 0x00000e00  # target 0x00000e00
    e18: 00008067  jalr         x0, 0(x1)
loc_e1c:
    e1c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    e20: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    e24: 007a7d13  andi         x26, x20, 7
    e28: ff8a7a13  andi         x20, x20, -8
    e2c: 01af8ab3  add          x21, x31, x26
    e30: 007afb93  andi         x23, x21, 7
    e34: 003ada93  srli         x21, x21, 3
    e38: 00ba9a93  slli         x21, x21, 11
    e3c: 014a8ab3  add          x21, x21, x20
    e40: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e40
    e44: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e58
    e48: 001b9b93  slli         x23, x23, 1
    e4c: 017b0b33  add          x22, x22, x23
    e50: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e54: 00008067  jalr         x0, 0(x1)
    e58: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e5c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e60: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e64: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e68:
    e68: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    e6c: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    e70: 007a7d13  andi         x26, x20, 7
    e74: ff8a7a13  andi         x20, x20, -8
    e78: 01af8ab3  add          x21, x31, x26
    e7c: 007afb93  andi         x23, x21, 7
    e80: 003ada93  srli         x21, x21, 3
    e84: 00ba9a93  slli         x21, x21, 11
    e88: 014a8ab3  add          x21, x21, x20
    e8c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e8c
    e90: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000ea4
    e94: 001b9b93  slli         x23, x23, 1
    e98: 017b0b33  add          x22, x22, x23
    e9c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ea0: 00008067  jalr         x0, 0(x1)
    ea4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ea8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    eac: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    eb0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
    eb4:           j FW_BRISC+4   # return to firmware, linked at install
