# llama3 8b-bf16 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00021800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00021800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00022000
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     3c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     40: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     44: 0001a2b7  lui          x5, 0x0001a  # x5 = 0x0001a000
     48: 80028293  addi         x5, x5, -2048  # x5 = 0x00019800
     4c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00019800
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
     8c: 0a5276e3  bgeu         x4, x5, 0x00000938  # target 0x00000938
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
     cc: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     d0: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
loc_d4:
     d4: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     d8: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     dc: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     e0: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     e4: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     e8: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     ec: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     f0: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     f4: 02020213  addi         x4, x4, 32
     f8: ff828293  addi         x5, x5, -8
     fc: fc029ce3  bne          x5, x0, 0x000000d4  # target 0x000000d4
    100: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    104: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00021800
    108: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    10c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    110: 02d000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000114
    114: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    118: 820f8f93  addi         x31, x31, -2016  # x31 = 0x00021820
    11c: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    120: 200f0f13  addi         x30, x30, 512  # x30 = 0x0000f200
    124: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    128: 015000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x0000012c
    12c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    130: 840f8f93  addi         x31, x31, -1984  # x31 = 0x00021840
    134: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    138: 800f0f13  addi         x30, x30, -2048  # x30 = 0x0000f800
    13c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    140: 7fc000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000144
    144: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    148: 860f8f93  addi         x31, x31, -1952  # x31 = 0x00021860
    14c: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    150: a00f0f13  addi         x30, x30, -1536  # x30 = 0x0000fa00
    154: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    158: 7e4000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x0000015c
    15c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    160: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00021880
    164: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    168: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    16c: 7d0000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000170
    170: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    174: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000218a0
    178: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    17c: 200f0f13  addi         x30, x30, 512  # x30 = 0x00010200
    180: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    184: 7b8000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000188
    188: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    18c: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000218c0
    190: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    194: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00010800
    198: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    19c: 7a0000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000001a0
    1a0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1a4: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000218e0
    1a8: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    1ac: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00010a00
    1b0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1b4: 788000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000001b8
    1b8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1bc: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00021900
    1c0: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    1c4: 020f0f13  addi         x30, x30, 32  # x30 = 0x0000f020
    1c8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1cc: 770000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000001d0
    1d0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1d4: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00021920
    1d8: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    1dc: 220f0f13  addi         x30, x30, 544  # x30 = 0x0000f220
    1e0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1e4: 758000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000001e8
    1e8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1ec: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00021940
    1f0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    1f4: 820f0f13  addi         x30, x30, -2016  # x30 = 0x0000f820
    1f8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1fc: 740000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000200
    200: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    204: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00021960
    208: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    20c: a20f0f13  addi         x30, x30, -1504  # x30 = 0x0000fa20
    210: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    214: 728000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000218
    218: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    21c: 980f8f93  addi         x31, x31, -1664  # x31 = 0x00021980
    220: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    224: 020f0f13  addi         x30, x30, 32  # x30 = 0x00010020
    228: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    22c: 710000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000230
    230: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    234: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x000219a0
    238: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    23c: 220f0f13  addi         x30, x30, 544  # x30 = 0x00010220
    240: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    244: 6f8000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000248
    248: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    24c: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000219c0
    250: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    254: 820f0f13  addi         x30, x30, -2016  # x30 = 0x00010820
    258: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    25c: 6e0000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000260
    260: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    264: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000219e0
    268: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    26c: a20f0f13  addi         x30, x30, -1504  # x30 = 0x00010a20
    270: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    274: 6c8000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000278
    278: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    27c: a00f8f93  addi         x31, x31, -1536  # x31 = 0x00021a00
    280: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    284: 040f0f13  addi         x30, x30, 64  # x30 = 0x0000f040
    288: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    28c: 6b0000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000290
    290: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    294: a20f8f93  addi         x31, x31, -1504  # x31 = 0x00021a20
    298: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    29c: 240f0f13  addi         x30, x30, 576  # x30 = 0x0000f240
    2a0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2a4: 698000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000002a8
    2a8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2ac: a40f8f93  addi         x31, x31, -1472  # x31 = 0x00021a40
    2b0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2b4: 840f0f13  addi         x30, x30, -1984  # x30 = 0x0000f840
    2b8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2bc: 680000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000002c0
    2c0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2c4: a60f8f93  addi         x31, x31, -1440  # x31 = 0x00021a60
    2c8: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2cc: a40f0f13  addi         x30, x30, -1472  # x30 = 0x0000fa40
    2d0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2d4: 668000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000002d8
    2d8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2dc: a80f8f93  addi         x31, x31, -1408  # x31 = 0x00021a80
    2e0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2e4: 040f0f13  addi         x30, x30, 64  # x30 = 0x00010040
    2e8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2ec: 650000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000002f0
    2f0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2f4: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x00021aa0
    2f8: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2fc: 240f0f13  addi         x30, x30, 576  # x30 = 0x00010240
    300: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    304: 638000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000308
    308: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    30c: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x00021ac0
    310: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    314: 840f0f13  addi         x30, x30, -1984  # x30 = 0x00010840
    318: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    31c: 620000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000320
    320: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    324: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x00021ae0
    328: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    32c: a40f0f13  addi         x30, x30, -1472  # x30 = 0x00010a40
    330: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    334: 608000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000338
    338: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    33c: b00f8f93  addi         x31, x31, -1280  # x31 = 0x00021b00
    340: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    344: 060f0f13  addi         x30, x30, 96  # x30 = 0x0000f060
    348: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    34c: 5f0000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000350
    350: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    354: b20f8f93  addi         x31, x31, -1248  # x31 = 0x00021b20
    358: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    35c: 260f0f13  addi         x30, x30, 608  # x30 = 0x0000f260
    360: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    364: 5d8000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000368
    368: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    36c: b40f8f93  addi         x31, x31, -1216  # x31 = 0x00021b40
    370: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    374: 860f0f13  addi         x30, x30, -1952  # x30 = 0x0000f860
    378: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    37c: 5c0000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000380
    380: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    384: b60f8f93  addi         x31, x31, -1184  # x31 = 0x00021b60
    388: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    38c: a60f0f13  addi         x30, x30, -1440  # x30 = 0x0000fa60
    390: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    394: 5a8000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x00000398
    398: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    39c: b80f8f93  addi         x31, x31, -1152  # x31 = 0x00021b80
    3a0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    3a4: 060f0f13  addi         x30, x30, 96  # x30 = 0x00010060
    3a8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3ac: 590000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000003b0
    3b0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3b4: ba0f8f93  addi         x31, x31, -1120  # x31 = 0x00021ba0
    3b8: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    3bc: 260f0f13  addi         x30, x30, 608  # x30 = 0x00010260
    3c0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3c4: 578000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000003c8
    3c8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3cc: bc0f8f93  addi         x31, x31, -1088  # x31 = 0x00021bc0
    3d0: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    3d4: 860f0f13  addi         x30, x30, -1952  # x30 = 0x00010860
    3d8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3dc: 560000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000003e0
    3e0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3e4: be0f8f93  addi         x31, x31, -1056  # x31 = 0x00021be0
    3e8: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    3ec: a60f0f13  addi         x30, x30, -1440  # x30 = 0x00010a60
    3f0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3f4: 548000ef  jal          x1, 0x0000093c  # target 0x0000093c; x1 = 0x000003f8
    3f8: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    3fc: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    400: 00525293  srli         x5, x4, 5
    404: 00229293  slli         x5, x5, 2
    408: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    40c: 90440413  addi         x8, x8, -1788  # x8 = 0x0000e904
    410: 00042383  lw           x7, 0(x8)  # param attention_core; 0x0000e904
    414: 00c00413  addi         x8, x0, 12  # x8 = 0x0000000c
    418: 0283d3b3  divu         x7, x7, x8
    41c: 0003d393  srli         x7, x7, 0
    420: 00a39393  slli         x7, x7, 10
    424: 007282b3  add          x5, x5, x7
    428: 00f27313  andi         x6, x4, 15
    42c: 00531313  slli         x6, x6, 5
    430: 01027393  andi         x7, x4, 16
    434: 00639393  slli         x7, x7, 6
    438: 00730333  add          x6, x6, x7
    43c: 554000ef  jal          x1, 0x00000990  # target 0x00000990; x1 = 0x00000440
    440: 56c000ef  jal          x1, 0x000009ac  # target 0x000009ac; x1 = 0x00000444
    444: 00028393  addi         x7, x5, 0
    448: 00038f93  addi         x31, x7, 0
    44c: 57c000ef  jal          x1, 0x000009c8  # target 0x000009c8; x1 = 0x00000450
    450: 000a8413  addi         x8, x21, 0
    454: 000b0493  addi         x9, x22, 0
    458: 00640533  add          x10, x8, x6
    45c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    460: c00f8f93  addi         x31, x31, -1024  # x31 = 0x00021c00
    464: 00050f13  addi         x30, x10, 0
    468: 00048e93  addi         x29, x9, 0
    46c: 5a8000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000470
    470: 00640533  add          x10, x8, x6
    474: 20050513  addi         x10, x10, 512
    478: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    47c: c20f8f93  addi         x31, x31, -992  # x31 = 0x00021c20
    480: 00050f13  addi         x30, x10, 0
    484: 00048e93  addi         x29, x9, 0
    488: 58c000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x0000048c
    48c: 00038f93  addi         x31, x7, 0
    490: 63c000ef  jal          x1, 0x00000acc  # target 0x00000acc; x1 = 0x00000494
    494: 000a8513  addi         x10, x21, 0
    498: 000b0593  addi         x11, x22, 0
    49c: 00650633  add          x12, x10, x6
    4a0: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    4a4: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00036800 · arc_apb_reset_unit + 0x6800
    4a8: 00060f13  addi         x30, x12, 0
    4ac: 00058e93  addi         x29, x11, 0
    4b0: 564000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x000004b4
    4b4: 00650633  add          x12, x10, x6
    4b8: 20060613  addi         x12, x12, 512
    4bc: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    4c0: 820f8f93  addi         x31, x31, -2016  # x31 = 0x00036820 · arc_apb_reset_unit + 0x6820
    4c4: 00060f13  addi         x30, x12, 0
    4c8: 00058e93  addi         x29, x11, 0
    4cc: 548000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x000004d0
    4d0: 00128393  addi         x7, x5, 1
    4d4: 00038f93  addi         x31, x7, 0
    4d8: 4f0000ef  jal          x1, 0x000009c8  # target 0x000009c8; x1 = 0x000004dc
    4dc: 000a8413  addi         x8, x21, 0
    4e0: 000b0493  addi         x9, x22, 0
    4e4: 00640533  add          x10, x8, x6
    4e8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    4ec: c40f8f93  addi         x31, x31, -960  # x31 = 0x00021c40
    4f0: 00050f13  addi         x30, x10, 0
    4f4: 00048e93  addi         x29, x9, 0
    4f8: 51c000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x000004fc
    4fc: 00640533  add          x10, x8, x6
    500: 20050513  addi         x10, x10, 512
    504: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    508: c60f8f93  addi         x31, x31, -928  # x31 = 0x00021c60
    50c: 00050f13  addi         x30, x10, 0
    510: 00048e93  addi         x29, x9, 0
    514: 500000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000518
    518: 00038f93  addi         x31, x7, 0
    51c: 5b0000ef  jal          x1, 0x00000acc  # target 0x00000acc; x1 = 0x00000520
    520: 000a8513  addi         x10, x21, 0
    524: 000b0593  addi         x11, x22, 0
    528: 00650633  add          x12, x10, x6
    52c: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    530: 840f8f93  addi         x31, x31, -1984  # x31 = 0x00036840 · arc_apb_reset_unit + 0x6840
    534: 00060f13  addi         x30, x12, 0
    538: 00058e93  addi         x29, x11, 0
    53c: 4d8000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000540
    540: 00650633  add          x12, x10, x6
    544: 20060613  addi         x12, x12, 512
    548: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    54c: 860f8f93  addi         x31, x31, -1952  # x31 = 0x00036860 · arc_apb_reset_unit + 0x6860
    550: 00060f13  addi         x30, x12, 0
    554: 00058e93  addi         x29, x11, 0
    558: 4bc000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x0000055c
    55c: 00228393  addi         x7, x5, 2
    560: 00038f93  addi         x31, x7, 0
    564: 464000ef  jal          x1, 0x000009c8  # target 0x000009c8; x1 = 0x00000568
    568: 000a8413  addi         x8, x21, 0
    56c: 000b0493  addi         x9, x22, 0
    570: 00640533  add          x10, x8, x6
    574: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    578: c80f8f93  addi         x31, x31, -896  # x31 = 0x00021c80
    57c: 00050f13  addi         x30, x10, 0
    580: 00048e93  addi         x29, x9, 0
    584: 490000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000588
    588: 00640533  add          x10, x8, x6
    58c: 20050513  addi         x10, x10, 512
    590: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    594: ca0f8f93  addi         x31, x31, -864  # x31 = 0x00021ca0
    598: 00050f13  addi         x30, x10, 0
    59c: 00048e93  addi         x29, x9, 0
    5a0: 474000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x000005a4
    5a4: 00038f93  addi         x31, x7, 0
    5a8: 524000ef  jal          x1, 0x00000acc  # target 0x00000acc; x1 = 0x000005ac
    5ac: 000a8513  addi         x10, x21, 0
    5b0: 000b0593  addi         x11, x22, 0
    5b4: 00650633  add          x12, x10, x6
    5b8: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    5bc: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00036880 · arc_apb_reset_unit + 0x6880
    5c0: 00060f13  addi         x30, x12, 0
    5c4: 00058e93  addi         x29, x11, 0
    5c8: 44c000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x000005cc
    5cc: 00650633  add          x12, x10, x6
    5d0: 20060613  addi         x12, x12, 512
    5d4: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    5d8: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000368a0 · arc_apb_reset_unit + 0x68a0
    5dc: 00060f13  addi         x30, x12, 0
    5e0: 00058e93  addi         x29, x11, 0
    5e4: 430000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x000005e8
    5e8: 00328393  addi         x7, x5, 3
    5ec: 00038f93  addi         x31, x7, 0
    5f0: 3d8000ef  jal          x1, 0x000009c8  # target 0x000009c8; x1 = 0x000005f4
    5f4: 000a8413  addi         x8, x21, 0
    5f8: 000b0493  addi         x9, x22, 0
    5fc: 00640533  add          x10, x8, x6
    600: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    604: cc0f8f93  addi         x31, x31, -832  # x31 = 0x00021cc0
    608: 00050f13  addi         x30, x10, 0
    60c: 00048e93  addi         x29, x9, 0
    610: 404000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000614
    614: 00640533  add          x10, x8, x6
    618: 20050513  addi         x10, x10, 512
    61c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    620: ce0f8f93  addi         x31, x31, -800  # x31 = 0x00021ce0
    624: 00050f13  addi         x30, x10, 0
    628: 00048e93  addi         x29, x9, 0
    62c: 3e8000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000630
    630: 00038f93  addi         x31, x7, 0
    634: 498000ef  jal          x1, 0x00000acc  # target 0x00000acc; x1 = 0x00000638
    638: 000a8513  addi         x10, x21, 0
    63c: 000b0593  addi         x11, x22, 0
    640: 00650633  add          x12, x10, x6
    644: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    648: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000368c0 · arc_apb_reset_unit + 0x68c0
    64c: 00060f13  addi         x30, x12, 0
    650: 00058e93  addi         x29, x11, 0
    654: 3c0000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000658
    658: 00650633  add          x12, x10, x6
    65c: 20060613  addi         x12, x12, 512
    660: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    664: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000368e0 · arc_apb_reset_unit + 0x68e0
    668: 00060f13  addi         x30, x12, 0
    66c: 00058e93  addi         x29, x11, 0
    670: 3a4000ef  jal          x1, 0x00000a14  # target 0x00000a14; x1 = 0x00000674
    674: 31c000ef  jal          x1, 0x00000990  # target 0x00000990; x1 = 0x00000678
    678: 334000ef  jal          x1, 0x000009ac  # target 0x000009ac; x1 = 0x0000067c
    67c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    680: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    684: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    688: 00120213  addi         x4, x4, 1
    68c: 01021213  slli         x4, x4, 16
    690: 01025213  srli         x4, x4, 16
    694: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    698: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    69c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    6a0: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    6a4: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    6a8: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    6ac: 0ff0000f  fence        0xf, 0xf
    6b0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6b4: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    6b8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    6bc: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6c0: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    6c4: 00520233  add          x4, x4, x5
    6c8: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    6cc: 00626863  bltu         x4, x6, 0x000006dc  # target 0x000006dc
    6d0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6d4: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    6d8: 40720233  sub          x4, x4, x7
loc_6dc:
    6dc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6e0: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    6e4: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    6e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6ec: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    6f0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    6f4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6f8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    6fc: 00520233  add          x4, x4, x5
    700: 00023337  lui          x6, 0x00023  # x6 = 0x00023000
    704: 80030313  addi         x6, x6, -2048  # x6 = 0x00022800
    708: 00626863  bltu         x4, x6, 0x00000718  # target 0x00000718
    70c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    710: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    714: 40720233  sub          x4, x4, x7
loc_718:
    718: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    71c: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    720: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    724: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    728: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    72c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    730: 00120213  addi         x4, x4, 1
    734: 01021213  slli         x4, x4, 16
    738: 01025213  srli         x4, x4, 16
    73c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    740: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    744: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    748: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    74c: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    750: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    754: 0ff0000f  fence        0xf, 0xf
    758: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    75c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    760: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    764: 00600393  addi         x7, x0, 6  # x7 = 0x00000006
loc_768:
    768: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    76c: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    770: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    774: 40428333  sub          x6, x5, x4
    778: 01031313  slli         x6, x6, 16
    77c: 01035313  srli         x6, x6, 16
    780: 00737663  bgeu         x6, x7, 0x0000078c  # target 0x0000078c
    784: 0ff0000f  fence        0xf, 0xf
    788: fe1ff06f  jal          x0, 0x00000768  # target 0x00000768
loc_78c:
    78c: 0ff0000f  fence        0xf, 0xf
    790: 200000ef  jal          x1, 0x00000990  # target 0x00000990; x1 = 0x00000794
    794: 218000ef  jal          x1, 0x000009ac  # target 0x000009ac; x1 = 0x00000798
    798: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    79c: 37c000ef  jal          x1, 0x00000b18  # target 0x00000b18; x1 = 0x000007a0
    7a0: 000a8213  addi         x4, x21, 0
    7a4: 000b0293  addi         x5, x22, 0
    7a8: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    7ac: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    7b0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    7b4: 00030f93  addi         x31, x6, 0
    7b8: 00020f13  addi         x30, x4, 0
    7bc: 00028e93  addi         x29, x5, 0
    7c0: 3a8000ef  jal          x1, 0x00000b68  # target 0x00000b68; x1 = 0x000007c4
    7c4: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    7c8: 350000ef  jal          x1, 0x00000b18  # target 0x00000b18; x1 = 0x000007cc
    7cc: 000a8213  addi         x4, x21, 0
    7d0: 000b0293  addi         x5, x22, 0
    7d4: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    7d8: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    7dc: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    7e0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7e4: 00730333  add          x6, x6, x7
    7e8: 00030f93  addi         x31, x6, 0
    7ec: 00020f13  addi         x30, x4, 0
    7f0: 00028e93  addi         x29, x5, 0
    7f4: 374000ef  jal          x1, 0x00000b68  # target 0x00000b68; x1 = 0x000007f8
    7f8: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    7fc: 31c000ef  jal          x1, 0x00000b18  # target 0x00000b18; x1 = 0x00000800
    800: 000a8213  addi         x4, x21, 0
    804: 000b0293  addi         x5, x22, 0
    808: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    80c: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    810: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    814: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    818: 00730333  add          x6, x6, x7
    81c: 00030f93  addi         x31, x6, 0
    820: 00020f13  addi         x30, x4, 0
    824: 00028e93  addi         x29, x5, 0
    828: 340000ef  jal          x1, 0x00000b68  # target 0x00000b68; x1 = 0x0000082c
    82c: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    830: 2e8000ef  jal          x1, 0x00000b18  # target 0x00000b18; x1 = 0x00000834
    834: 000a8213  addi         x4, x21, 0
    838: 000b0293  addi         x5, x22, 0
    83c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    840: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    844: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    848: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    84c: 00730333  add          x6, x6, x7
    850: 00030f93  addi         x31, x6, 0
    854: 00020f13  addi         x30, x4, 0
    858: 00028e93  addi         x29, x5, 0
    85c: 30c000ef  jal          x1, 0x00000b68  # target 0x00000b68; x1 = 0x00000860
    860: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
    864: 2b4000ef  jal          x1, 0x00000b18  # target 0x00000b18; x1 = 0x00000868
    868: 000a8213  addi         x4, x21, 0
    86c: 000b0293  addi         x5, x22, 0
    870: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    874: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    878: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    87c: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    880: 00730333  add          x6, x6, x7
    884: 00030f93  addi         x31, x6, 0
    888: 00020f13  addi         x30, x4, 0
    88c: 00028e93  addi         x29, x5, 0
    890: 2d8000ef  jal          x1, 0x00000b68  # target 0x00000b68; x1 = 0x00000894
    894: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
    898: 280000ef  jal          x1, 0x00000b18  # target 0x00000b18; x1 = 0x0000089c
    89c: 000a8213  addi         x4, x21, 0
    8a0: 000b0293  addi         x5, x22, 0
    8a4: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    8a8: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    8ac: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    8b0: 000053b7  lui          x7, 0x00005  # x7 = 0x00005000
    8b4: 00730333  add          x6, x6, x7
    8b8: 00030f93  addi         x31, x6, 0
    8bc: 00020f13  addi         x30, x4, 0
    8c0: 00028e93  addi         x29, x5, 0
    8c4: 2a4000ef  jal          x1, 0x00000b68  # target 0x00000b68; x1 = 0x000008c8
    8c8: 0c8000ef  jal          x1, 0x00000990  # target 0x00000990; x1 = 0x000008cc
    8cc: 0e0000ef  jal          x1, 0x000009ac  # target 0x000009ac; x1 = 0x000008d0
    8d0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    8d4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    8d8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    8dc: 00620213  addi         x4, x4, 6
    8e0: 01021213  slli         x4, x4, 16
    8e4: 01025213  srli         x4, x4, 16
    8e8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    8ec: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    8f0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    8f4: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    8f8: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    8fc: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    900: 0ff0000f  fence        0xf, 0xf
    904: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    908: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    90c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    910: 000062b7  lui          x5, 0x00006  # x5 = 0x00006000
    914: 00520233  add          x4, x4, x5
    918: 00020337  lui          x6, 0x00020  # x6 = 0x00020000
    91c: 80030313  addi         x6, x6, -2048  # x6 = 0x0001f800
    920: 00626663  bltu         x4, x6, 0x0000092c  # target 0x0000092c
    924: 000063b7  lui          x7, 0x00006  # x7 = 0x00006000
    928: 40720233  sub          x4, x4, x7
loc_92c:
    92c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    930: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    934: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
loc_938:
    938: 2e80006f  jal          x0, 0x00000c20  # target 0x00000c20
loc_93c:
    93c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    940: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    944: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    948: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    94c: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    950: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    954: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    958: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    95c: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    960: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    964: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    968: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    96c: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    970: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    974: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    978: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    97c: 020f8f93  addi         x31, x31, 32
    980: 020f0f13  addi         x30, x30, 32
    984: ff8e8e93  addi         x29, x29, -8
    988: fa0e9ae3  bne          x29, x0, 0x0000093c  # target 0x0000093c
    98c: 00008067  jalr         x0, 0(x1)
loc_990:
    990: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    994: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    998: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    99c: 000a0463  beq          x20, x0, 0x000009a4  # target 0x000009a4
    9a0: ff1ff06f  jal          x0, 0x00000990  # target 0x00000990
loc_9a4:
    9a4: 0ff0000f  fence        0xf, 0xf
    9a8: 00008067  jalr         x0, 0(x1)
loc_9ac:
    9ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9b0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    9b4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    9b8: 000a0463  beq          x20, x0, 0x000009c0  # target 0x000009c0
    9bc: ff1ff06f  jal          x0, 0x000009ac  # target 0x000009ac
loc_9c0:
    9c0: 0ff0000f  fence        0xf, 0xf
    9c4: 00008067  jalr         x0, 0(x1)
loc_9c8:
    9c8: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    9cc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    9d0: 007a7d13  andi         x26, x20, 7
    9d4: ff8a7a13  andi         x20, x20, -8
    9d8: 01af8ab3  add          x21, x31, x26
    9dc: 007afb93  andi         x23, x21, 7
    9e0: 003ada93  srli         x21, x21, 3
    9e4: 00ba9a93  slli         x21, x21, 11
    9e8: 014a8ab3  add          x21, x21, x20
    9ec: 00000b17  auipc        x22, 0x00000  # x22 = 0x000009ec
    9f0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000a04
    9f4: 001b9b93  slli         x23, x23, 1
    9f8: 017b0b33  add          x22, x22, x23
    9fc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    a00: 00008067  jalr         x0, 0(x1)
    a04: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    a08: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    a0c: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    a10: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_a14:
    a14: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    a18: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    a1c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    a20: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    a24: 015a6463  bltu         x20, x21, 0x00000a2c  # target 0x00000a2c
    a28: fedff06f  jal          x0, 0x00000a14  # target 0x00000a14
loc_a2c:
    a2c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    a30: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    a34: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    a38: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    a3c: 015a6463  bltu         x20, x21, 0x00000a44  # target 0x00000a44
    a40: fedff06f  jal          x0, 0x00000a2c  # target 0x00000a2c
loc_a44:
    a44: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    a48: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    a4c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    a50: 014a1a13  slli         x20, x20, 20
    a54: 014a5a13  srli         x20, x20, 20
    a58: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_a5c:
    a5c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    a60: 000b0463  beq          x22, x0, 0x00000a68  # target 0x00000a68
    a64: ff9ff06f  jal          x0, 0x00000a5c  # target 0x00000a5c
loc_a68:
    a68: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    a6c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    a70: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    a74: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    a78: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    a7c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    a80: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    a84: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    a88: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    a8c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    a90: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    a94: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    a98: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    a9c: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    aa0: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    aa4: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    aa8: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    aac: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    ab0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    ab4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    ab8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_abc:
    abc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    ac0: 000b0463  beq          x22, x0, 0x00000ac8  # target 0x00000ac8
    ac4: ff9ff06f  jal          x0, 0x00000abc  # target 0x00000abc
loc_ac8:
    ac8: 00008067  jalr         x0, 0(x1)
loc_acc:
    acc: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    ad0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    ad4: 007a7d13  andi         x26, x20, 7
    ad8: ff8a7a13  andi         x20, x20, -8
    adc: 01af8ab3  add          x21, x31, x26
    ae0: 007afb93  andi         x23, x21, 7
    ae4: 003ada93  srli         x21, x21, 3
    ae8: 00ba9a93  slli         x21, x21, 11
    aec: 014a8ab3  add          x21, x21, x20
    af0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000af0
    af4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b08
    af8: 001b9b93  slli         x23, x23, 1
    afc: 017b0b33  add          x22, x22, x23
    b00: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b04: 00008067  jalr         x0, 0(x1)
    b08: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b0c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b10: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    b14: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_b18:
    b18: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    b1c: 900a8a93  addi         x21, x21, -1792  # x21 = 0x0000e900
    b20: 000aaa03  lw           x20, 0(x21)  # param e2e_attention_partials; 0x0000e900
    b24: 007a7d13  andi         x26, x20, 7
    b28: ff8a7a13  andi         x20, x20, -8
    b2c: 01af8ab3  add          x21, x31, x26
    b30: 007afb93  andi         x23, x21, 7
    b34: 003ada93  srli         x21, x21, 3
    b38: 00ca9a93  slli         x21, x21, 12
    b3c: 014a8ab3  add          x21, x21, x20
    b40: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000b40
    b44: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b58
    b48: 001b9b93  slli         x23, x23, 1
    b4c: 017b0b33  add          x22, x22, x23
    b50: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b54: 00008067  jalr         x0, 0(x1)
    b58: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b5c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b60: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    b64: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_b68:
    b68: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    b6c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    b70: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    b74: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    b78: 015a6463  bltu         x20, x21, 0x00000b80  # target 0x00000b80
    b7c: fedff06f  jal          x0, 0x00000b68  # target 0x00000b68
loc_b80:
    b80: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    b84: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    b88: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    b8c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    b90: 015a6463  bltu         x20, x21, 0x00000b98  # target 0x00000b98
    b94: fedff06f  jal          x0, 0x00000b80  # target 0x00000b80
loc_b98:
    b98: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    b9c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    ba0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    ba4: 014a1a13  slli         x20, x20, 20
    ba8: 014a5a13  srli         x20, x20, 20
    bac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_bb0:
    bb0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    bb4: 000b0463  beq          x22, x0, 0x00000bbc  # target 0x00000bbc
    bb8: ff9ff06f  jal          x0, 0x00000bb0  # target 0x00000bb0
loc_bbc:
    bbc: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    bc0: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    bc4: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    bc8: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    bcc: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    bd0: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    bd4: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    bd8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    bdc: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    be0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    be4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    be8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    bec: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    bf0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00001000
    bf4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    bf8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    bfc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    c00: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    c04: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    c08: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    c0c: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_c10:
    c10: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    c14: 000b0463  beq          x22, x0, 0x00000c1c  # target 0x00000c1c
    c18: ff9ff06f  jal          x0, 0x00000c10  # target 0x00000c10
loc_c1c:
    c1c: 00008067  jalr         x0, 0(x1)
    c20:           j FW_NCRISC+4   # return to firmware, linked at install
