# llama3 1b decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 0001b2b7  lui          x5, 0x0001b  # x5 = 0x0001b000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x0001a800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x0001a800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 0001b2b7  lui          x5, 0x0001b  # x5 = 0x0001b000
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x0001b000
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     3c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     40: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     44: 000152b7  lui          x5, 0x00015  # x5 = 0x00015000
     48: 80028293  addi         x5, x5, -2048  # x5 = 0x00014800
     4c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00014800
     50: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     54: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     58: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     5c: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     60: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     64: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     68: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     6c: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     70: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     74: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     78: 0063fa63  bgeu         x7, x6, 0x0000008c  # target 0x0000008c
     7c: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     80: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     84: 0063f463  bgeu         x7, x6, 0x0000008c  # target 0x0000008c
     88: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_8c:
     8c: 5a527663  bgeu         x4, x5, 0x00000638  # target 0x00000638
     90: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     94: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     98: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     9c: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_a0:
     a0: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
     a4: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
     a8: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
     ac: 40428333  sub          x6, x5, x4
     b0: 01031313  slli         x6, x6, 16
     b4: 01035313  srli         x6, x6, 16
     b8: 00737663  bgeu         x6, x7, 0x000000c4  # target 0x000000c4
     bc: 0ff0000f  fence        0xf, 0xf
     c0: fe1ff06f  jal          x0, 0x000000a0  # target 0x000000a0
loc_c4:
     c4: 0ff0000f  fence        0xf, 0xf
     c8: 0000f237  lui          x4, 0x0000f  # x4 = 0x0000f000
     cc: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
loc_d0:
     d0: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     d4: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     d8: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     dc: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     e0: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     e4: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     e8: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     ec: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     f0: 02020213  addi         x4, x4, 32
     f4: ff828293  addi         x5, x5, -8
     f8: fc029ce3  bne          x5, x0, 0x000000d0  # target 0x000000d0
     fc: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    100: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001a800
    104: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    108: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    10c: 530000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000110
    110: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    114: 820f8f93  addi         x31, x31, -2016  # x31 = 0x0001a820
    118: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    11c: 200f0f13  addi         x30, x30, 512  # x30 = 0x0000f200
    120: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    124: 518000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000128
    128: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    12c: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001a840
    130: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    134: 800f0f13  addi         x30, x30, -2048  # x30 = 0x0000f800
    138: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    13c: 500000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000140
    140: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    144: 860f8f93  addi         x31, x31, -1952  # x31 = 0x0001a860
    148: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    14c: a00f0f13  addi         x30, x30, -1536  # x30 = 0x0000fa00
    150: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    154: 4e8000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000158
    158: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    15c: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001a880
    160: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    164: 020f0f13  addi         x30, x30, 32  # x30 = 0x0000f020
    168: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    16c: 4d0000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000170
    170: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    174: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x0001a8a0
    178: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    17c: 220f0f13  addi         x30, x30, 544  # x30 = 0x0000f220
    180: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    184: 4b8000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000188
    188: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    18c: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x0001a8c0
    190: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    194: 820f0f13  addi         x30, x30, -2016  # x30 = 0x0000f820
    198: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    19c: 4a0000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x000001a0
    1a0: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    1a4: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x0001a8e0
    1a8: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    1ac: a20f0f13  addi         x30, x30, -1504  # x30 = 0x0000fa20
    1b0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1b4: 488000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x000001b8
    1b8: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    1bc: 900f8f93  addi         x31, x31, -1792  # x31 = 0x0001a900
    1c0: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    1c4: 040f0f13  addi         x30, x30, 64  # x30 = 0x0000f040
    1c8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1cc: 470000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x000001d0
    1d0: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    1d4: 920f8f93  addi         x31, x31, -1760  # x31 = 0x0001a920
    1d8: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    1dc: 240f0f13  addi         x30, x30, 576  # x30 = 0x0000f240
    1e0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1e4: 458000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x000001e8
    1e8: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    1ec: 940f8f93  addi         x31, x31, -1728  # x31 = 0x0001a940
    1f0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    1f4: 840f0f13  addi         x30, x30, -1984  # x30 = 0x0000f840
    1f8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1fc: 440000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000200
    200: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    204: 960f8f93  addi         x31, x31, -1696  # x31 = 0x0001a960
    208: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    20c: a40f0f13  addi         x30, x30, -1472  # x30 = 0x0000fa40
    210: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    214: 428000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000218
    218: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    21c: 980f8f93  addi         x31, x31, -1664  # x31 = 0x0001a980
    220: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    224: 060f0f13  addi         x30, x30, 96  # x30 = 0x0000f060
    228: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    22c: 410000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000230
    230: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    234: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x0001a9a0
    238: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    23c: 260f0f13  addi         x30, x30, 608  # x30 = 0x0000f260
    240: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    244: 3f8000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000248
    248: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    24c: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x0001a9c0
    250: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    254: 860f0f13  addi         x30, x30, -1952  # x30 = 0x0000f860
    258: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    25c: 3e0000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000260
    260: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    264: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x0001a9e0
    268: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    26c: a60f0f13  addi         x30, x30, -1440  # x30 = 0x0000fa60
    270: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    274: 3c8000ef  jal          x1, 0x0000063c  # target 0x0000063c; x1 = 0x00000278
    278: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    27c: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    280: 00525293  srli         x5, x4, 5
    284: 00129293  slli         x5, x5, 1
    288: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    28c: 90440413  addi         x8, x8, -1788  # x8 = 0x0000e904
    290: 00042383  lw           x7, 0(x8)  # param attention_core; 0x0000e904
    294: 00c00413  addi         x8, x0, 12  # x8 = 0x0000000c
    298: 0283d3b3  divu         x7, x7, x8
    29c: 0003d393  srli         x7, x7, 0
    2a0: 00939393  slli         x7, x7, 9
    2a4: 007282b3  add          x5, x5, x7
    2a8: 00f27313  andi         x6, x4, 15
    2ac: 00531313  slli         x6, x6, 5
    2b0: 01027393  andi         x7, x4, 16
    2b4: 00639393  slli         x7, x7, 6
    2b8: 00730333  add          x6, x6, x7
    2bc: 3d4000ef  jal          x1, 0x00000690  # target 0x00000690; x1 = 0x000002c0
    2c0: 3ec000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000002c4
    2c4: 00028393  addi         x7, x5, 0
    2c8: 00038f93  addi         x31, x7, 0
    2cc: 3fc000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000002d0
    2d0: 000a8413  addi         x8, x21, 0
    2d4: 000b0493  addi         x9, x22, 0
    2d8: 00640533  add          x10, x8, x6
    2dc: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    2e0: a00f8f93  addi         x31, x31, -1536  # x31 = 0x0001aa00
    2e4: 00050f13  addi         x30, x10, 0
    2e8: 00048e93  addi         x29, x9, 0
    2ec: 428000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x000002f0
    2f0: 00640533  add          x10, x8, x6
    2f4: 20050513  addi         x10, x10, 512
    2f8: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    2fc: a20f8f93  addi         x31, x31, -1504  # x31 = 0x0001aa20
    300: 00050f13  addi         x30, x10, 0
    304: 00048e93  addi         x29, x9, 0
    308: 40c000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x0000030c
    30c: 00038f93  addi         x31, x7, 0
    310: 4bc000ef  jal          x1, 0x000007cc  # target 0x000007cc; x1 = 0x00000314
    314: 000a8513  addi         x10, x21, 0
    318: 000b0593  addi         x11, x22, 0
    31c: 00650633  add          x12, x10, x6
    320: 00030fb7  lui          x31, 0x00030  # x31 = 0x00030000 · arc_apb_reset_unit + 0x0
    324: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0002f800
    328: 00060f13  addi         x30, x12, 0
    32c: 00058e93  addi         x29, x11, 0
    330: 3e4000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000334
    334: 00650633  add          x12, x10, x6
    338: 20060613  addi         x12, x12, 512
    33c: 00030fb7  lui          x31, 0x00030  # x31 = 0x00030000 · arc_apb_reset_unit + 0x0
    340: 820f8f93  addi         x31, x31, -2016  # x31 = 0x0002f820
    344: 00060f13  addi         x30, x12, 0
    348: 00058e93  addi         x29, x11, 0
    34c: 3c8000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000350
    350: 00128393  addi         x7, x5, 1
    354: 00038f93  addi         x31, x7, 0
    358: 370000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x0000035c
    35c: 000a8413  addi         x8, x21, 0
    360: 000b0493  addi         x9, x22, 0
    364: 00640533  add          x10, x8, x6
    368: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    36c: a40f8f93  addi         x31, x31, -1472  # x31 = 0x0001aa40
    370: 00050f13  addi         x30, x10, 0
    374: 00048e93  addi         x29, x9, 0
    378: 39c000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x0000037c
    37c: 00640533  add          x10, x8, x6
    380: 20050513  addi         x10, x10, 512
    384: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    388: a60f8f93  addi         x31, x31, -1440  # x31 = 0x0001aa60
    38c: 00050f13  addi         x30, x10, 0
    390: 00048e93  addi         x29, x9, 0
    394: 380000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000398
    398: 00038f93  addi         x31, x7, 0
    39c: 430000ef  jal          x1, 0x000007cc  # target 0x000007cc; x1 = 0x000003a0
    3a0: 000a8513  addi         x10, x21, 0
    3a4: 000b0593  addi         x11, x22, 0
    3a8: 00650633  add          x12, x10, x6
    3ac: 00030fb7  lui          x31, 0x00030  # x31 = 0x00030000 · arc_apb_reset_unit + 0x0
    3b0: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0002f840
    3b4: 00060f13  addi         x30, x12, 0
    3b8: 00058e93  addi         x29, x11, 0
    3bc: 358000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x000003c0
    3c0: 00650633  add          x12, x10, x6
    3c4: 20060613  addi         x12, x12, 512
    3c8: 00030fb7  lui          x31, 0x00030  # x31 = 0x00030000 · arc_apb_reset_unit + 0x0
    3cc: 860f8f93  addi         x31, x31, -1952  # x31 = 0x0002f860
    3d0: 00060f13  addi         x30, x12, 0
    3d4: 00058e93  addi         x29, x11, 0
    3d8: 33c000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x000003dc
    3dc: 2b4000ef  jal          x1, 0x00000690  # target 0x00000690; x1 = 0x000003e0
    3e0: 2cc000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000003e4
    3e4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3e8: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    3ec: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    3f0: 00120213  addi         x4, x4, 1
    3f4: 01021213  slli         x4, x4, 16
    3f8: 01025213  srli         x4, x4, 16
    3fc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    400: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    404: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    408: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    40c: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    410: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    414: 0ff0000f  fence        0xf, 0xf
    418: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    41c: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    420: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    424: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    428: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    42c: 00520233  add          x4, x4, x5
    430: 0001b337  lui          x6, 0x0001b  # x6 = 0x0001b000
    434: 00626863  bltu         x4, x6, 0x00000444  # target 0x00000444
    438: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    43c: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    440: 40720233  sub          x4, x4, x7
loc_444:
    444: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    448: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    44c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    450: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    454: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    458: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    45c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    460: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    464: 00520233  add          x4, x4, x5
    468: 0001c337  lui          x6, 0x0001c  # x6 = 0x0001c000
    46c: 80030313  addi         x6, x6, -2048  # x6 = 0x0001b800
    470: 00626863  bltu         x4, x6, 0x00000480  # target 0x00000480
    474: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    478: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    47c: 40720233  sub          x4, x4, x7
loc_480:
    480: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    484: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    488: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    48c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    490: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    494: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    498: 00120213  addi         x4, x4, 1
    49c: 01021213  slli         x4, x4, 16
    4a0: 01025213  srli         x4, x4, 16
    4a4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4a8: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4ac: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    4b0: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    4b4: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    4b8: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    4bc: 0ff0000f  fence        0xf, 0xf
    4c0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4c4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    4c8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    4cc: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_4d0:
    4d0: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    4d4: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    4d8: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    4dc: 40428333  sub          x6, x5, x4
    4e0: 01031313  slli         x6, x6, 16
    4e4: 01035313  srli         x6, x6, 16
    4e8: 00737663  bgeu         x6, x7, 0x000004f4  # target 0x000004f4
    4ec: 0ff0000f  fence        0xf, 0xf
    4f0: fe1ff06f  jal          x0, 0x000004d0  # target 0x000004d0
loc_4f4:
    4f4: 0ff0000f  fence        0xf, 0xf
    4f8: 198000ef  jal          x1, 0x00000690  # target 0x00000690; x1 = 0x000004fc
    4fc: 1b0000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000500
    500: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    504: 314000ef  jal          x1, 0x00000818  # target 0x00000818; x1 = 0x00000508
    508: 000a8213  addi         x4, x21, 0
    50c: 000b0293  addi         x5, x22, 0
    510: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    514: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    518: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    51c: 00030f93  addi         x31, x6, 0
    520: 00020f13  addi         x30, x4, 0
    524: 00028e93  addi         x29, x5, 0
    528: 340000ef  jal          x1, 0x00000868  # target 0x00000868; x1 = 0x0000052c
    52c: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    530: 2e8000ef  jal          x1, 0x00000818  # target 0x00000818; x1 = 0x00000534
    534: 000a8213  addi         x4, x21, 0
    538: 000b0293  addi         x5, x22, 0
    53c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    540: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    544: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    548: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    54c: 00730333  add          x6, x6, x7
    550: 00030f93  addi         x31, x6, 0
    554: 00020f13  addi         x30, x4, 0
    558: 00028e93  addi         x29, x5, 0
    55c: 30c000ef  jal          x1, 0x00000868  # target 0x00000868; x1 = 0x00000560
    560: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    564: 2b4000ef  jal          x1, 0x00000818  # target 0x00000818; x1 = 0x00000568
    568: 000a8213  addi         x4, x21, 0
    56c: 000b0293  addi         x5, x22, 0
    570: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    574: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    578: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    57c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    580: 00730333  add          x6, x6, x7
    584: 00030f93  addi         x31, x6, 0
    588: 00020f13  addi         x30, x4, 0
    58c: 00028e93  addi         x29, x5, 0
    590: 2d8000ef  jal          x1, 0x00000868  # target 0x00000868; x1 = 0x00000594
    594: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    598: 280000ef  jal          x1, 0x00000818  # target 0x00000818; x1 = 0x0000059c
    59c: 000a8213  addi         x4, x21, 0
    5a0: 000b0293  addi         x5, x22, 0
    5a4: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    5a8: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    5ac: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    5b0: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    5b4: 00730333  add          x6, x6, x7
    5b8: 00030f93  addi         x31, x6, 0
    5bc: 00020f13  addi         x30, x4, 0
    5c0: 00028e93  addi         x29, x5, 0
    5c4: 2a4000ef  jal          x1, 0x00000868  # target 0x00000868; x1 = 0x000005c8
    5c8: 0c8000ef  jal          x1, 0x00000690  # target 0x00000690; x1 = 0x000005cc
    5cc: 0e0000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000005d0
    5d0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5d4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    5d8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    5dc: 00420213  addi         x4, x4, 4
    5e0: 01021213  slli         x4, x4, 16
    5e4: 01025213  srli         x4, x4, 16
    5e8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5ec: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    5f0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    5f4: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    5f8: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    5fc: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    600: 0ff0000f  fence        0xf, 0xf
    604: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    608: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    60c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    610: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    614: 00520233  add          x4, x4, x5
    618: 00019337  lui          x6, 0x00019  # x6 = 0x00019000
    61c: 80030313  addi         x6, x6, -2048  # x6 = 0x00018800
    620: 00626663  bltu         x4, x6, 0x0000062c  # target 0x0000062c
    624: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    628: 40720233  sub          x4, x4, x7
loc_62c:
    62c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    630: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    634: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
loc_638:
    638: 2e80006f  jal          x0, 0x00000920  # target 0x00000920
loc_63c:
    63c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    640: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    644: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    648: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    64c: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    650: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    654: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    658: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    65c: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    660: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    664: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    668: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    66c: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    670: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    674: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    678: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    67c: 020f8f93  addi         x31, x31, 32
    680: 020f0f13  addi         x30, x30, 32
    684: ff8e8e93  addi         x29, x29, -8
    688: fa0e9ae3  bne          x29, x0, 0x0000063c  # target 0x0000063c
    68c: 00008067  jalr         x0, 0(x1)
loc_690:
    690: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    694: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    698: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    69c: 000a0463  beq          x20, x0, 0x000006a4  # target 0x000006a4
    6a0: ff1ff06f  jal          x0, 0x00000690  # target 0x00000690
loc_6a4:
    6a4: 0ff0000f  fence        0xf, 0xf
    6a8: 00008067  jalr         x0, 0(x1)
loc_6ac:
    6ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6b0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    6b4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    6b8: 000a0463  beq          x20, x0, 0x000006c0  # target 0x000006c0
    6bc: ff1ff06f  jal          x0, 0x000006ac  # target 0x000006ac
loc_6c0:
    6c0: 0ff0000f  fence        0xf, 0xf
    6c4: 00008067  jalr         x0, 0(x1)
loc_6c8:
    6c8: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    6cc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    6d0: 007a7d13  andi         x26, x20, 7
    6d4: ff8a7a13  andi         x20, x20, -8
    6d8: 01af8ab3  add          x21, x31, x26
    6dc: 007afb93  andi         x23, x21, 7
    6e0: 003ada93  srli         x21, x21, 3
    6e4: 00ba9a93  slli         x21, x21, 11
    6e8: 014a8ab3  add          x21, x21, x20
    6ec: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006ec
    6f0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000704
    6f4: 001b9b93  slli         x23, x23, 1
    6f8: 017b0b33  add          x22, x22, x23
    6fc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    700: 00008067  jalr         x0, 0(x1)
    704: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    708: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    70c: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    710: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_714:
    714: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    718: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    71c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    720: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    724: 015a6463  bltu         x20, x21, 0x0000072c  # target 0x0000072c
    728: fedff06f  jal          x0, 0x00000714  # target 0x00000714
loc_72c:
    72c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    730: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    734: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    738: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    73c: 015a6463  bltu         x20, x21, 0x00000744  # target 0x00000744
    740: fedff06f  jal          x0, 0x0000072c  # target 0x0000072c
loc_744:
    744: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    748: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    74c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    750: 014a1a13  slli         x20, x20, 20
    754: 014a5a13  srli         x20, x20, 20
    758: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_75c:
    75c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    760: 000b0463  beq          x22, x0, 0x00000768  # target 0x00000768
    764: ff9ff06f  jal          x0, 0x0000075c  # target 0x0000075c
loc_768:
    768: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    76c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    770: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    774: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    778: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    77c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    780: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    784: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    788: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    78c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    790: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    794: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    798: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    79c: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    7a0: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    7a4: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    7a8: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    7ac: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    7b0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    7b4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    7b8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_7bc:
    7bc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    7c0: 000b0463  beq          x22, x0, 0x000007c8  # target 0x000007c8
    7c4: ff9ff06f  jal          x0, 0x000007bc  # target 0x000007bc
loc_7c8:
    7c8: 00008067  jalr         x0, 0(x1)
loc_7cc:
    7cc: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    7d0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    7d4: 007a7d13  andi         x26, x20, 7
    7d8: ff8a7a13  andi         x20, x20, -8
    7dc: 01af8ab3  add          x21, x31, x26
    7e0: 007afb93  andi         x23, x21, 7
    7e4: 003ada93  srli         x21, x21, 3
    7e8: 00ba9a93  slli         x21, x21, 11
    7ec: 014a8ab3  add          x21, x21, x20
    7f0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007f0
    7f4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000808
    7f8: 001b9b93  slli         x23, x23, 1
    7fc: 017b0b33  add          x22, x22, x23
    800: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    804: 00008067  jalr         x0, 0(x1)
    808: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    80c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    810: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    814: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_818:
    818: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    81c: 900a8a93  addi         x21, x21, -1792  # x21 = 0x0000e900
    820: 000aaa03  lw           x20, 0(x21)  # param e2e_attention_partials; 0x0000e900
    824: 007a7d13  andi         x26, x20, 7
    828: ff8a7a13  andi         x20, x20, -8
    82c: 01af8ab3  add          x21, x31, x26
    830: 007afb93  andi         x23, x21, 7
    834: 003ada93  srli         x21, x21, 3
    838: 00ca9a93  slli         x21, x21, 12
    83c: 014a8ab3  add          x21, x21, x20
    840: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000840
    844: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000858
    848: 001b9b93  slli         x23, x23, 1
    84c: 017b0b33  add          x22, x22, x23
    850: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    854: 00008067  jalr         x0, 0(x1)
    858: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    85c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    860: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    864: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_868:
    868: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    86c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    870: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    874: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    878: 015a6463  bltu         x20, x21, 0x00000880  # target 0x00000880
    87c: fedff06f  jal          x0, 0x00000868  # target 0x00000868
loc_880:
    880: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    884: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    888: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    88c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    890: 015a6463  bltu         x20, x21, 0x00000898  # target 0x00000898
    894: fedff06f  jal          x0, 0x00000880  # target 0x00000880
loc_898:
    898: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    89c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    8a0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    8a4: 014a1a13  slli         x20, x20, 20
    8a8: 014a5a13  srli         x20, x20, 20
    8ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_8b0:
    8b0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    8b4: 000b0463  beq          x22, x0, 0x000008bc  # target 0x000008bc
    8b8: ff9ff06f  jal          x0, 0x000008b0  # target 0x000008b0
loc_8bc:
    8bc: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    8c0: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    8c4: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    8c8: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    8cc: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    8d0: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    8d4: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    8d8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    8dc: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    8e0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    8e4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    8e8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    8ec: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8f0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00001000
    8f4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    8f8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    8fc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    900: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    904: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    908: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    90c: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_910:
    910: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    914: 000b0463  beq          x22, x0, 0x0000091c  # target 0x0000091c
    918: ff9ff06f  jal          x0, 0x00000910  # target 0x00000910
loc_91c:
    91c: 00008067  jalr         x0, 0(x1)
    920:           j FW_NCRISC+4   # return to firmware, linked at install
