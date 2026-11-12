# llama3 8b-fp8 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (96): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5 7,6 7,7 7,8 7,9 7,10 7,11 10,2 10,3 10,4 10,5 10,6 10,7 10,8 10,9 10,10 10,11 11,2 11,3 11,4 11,5 11,6 11,7 11,8 11,9 11,10 11,11 12,2 12,3 12,4 12,5 12,6 12,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=e2e_attention_partials, 0xe904=attention_core, 0xe908=attention_phase
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
      c: 88028293  addi         x5, x5, -1920  # x5 = 0x00021880
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00021880
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
     2c: 08028293  addi         x5, x5, 128  # x5 = 0x00022080
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00022080
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 0001a2b7  lui          x5, 0x0001a  # x5 = 0x0001a000
     4c: 88028293  addi         x5, x5, -1920  # x5 = 0x00019880
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00019880
     54: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     58: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     5c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     60: 0000f337  lui          x6, 0x0000f  # x6 = 0x0000f000
     64: 90830313  addi         x6, x6, -1784  # x6 = 0x0000e908
     68: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x0000e908
     6c: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     70: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     74: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     78: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     7c: 0063fa63  bgeu         x7, x6, 0x00000090  # target 0x00000090
     80: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     84: 08000393  addi         x7, x0, 128  # x7 = 0x00000080
     88: 0063f463  bgeu         x7, x6, 0x00000090  # target 0x00000090
     8c: 00c00293  addi         x5, x0, 12  # x5 = 0x0000000c
loc_90:
     90: 0a527ee3  bgeu         x4, x5, 0x0000094c  # target 0x0000094c
     94: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     98: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     9c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     a0: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_a4:
     a4: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
     a8: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
     ac: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
     b0: 40428333  sub          x6, x5, x4
     b4: 01031313  slli         x6, x6, 16
     b8: 01035313  srli         x6, x6, 16
     bc: 00737663  bgeu         x6, x7, 0x000000c8  # target 0x000000c8
     c0: 0ff0000f  fence        0xf, 0xf
     c4: fe1ff06f  jal          x0, 0x000000a4  # target 0x000000a4
loc_c8:
     c8: 0ff0000f  fence        0xf, 0xf
     cc: 0000f237  lui          x4, 0x0000f  # x4 = 0x0000f000
     d0: 08020213  addi         x4, x4, 128  # x4 = 0x0000f080
     d4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     d8: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
loc_dc:
     dc: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     e0: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     e4: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     e8: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     ec: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     f0: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     f4: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     f8: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     fc: 02020213  addi         x4, x4, 32
    100: ff828293  addi         x5, x5, -8
    104: fc029ce3  bne          x5, x0, 0x000000dc  # target 0x000000dc
    108: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    10c: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00021880
    110: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    114: 080f0f13  addi         x30, x30, 128  # x30 = 0x0000f080
    118: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    11c: 035000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000120
    120: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    124: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000218a0
    128: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    12c: 280f0f13  addi         x30, x30, 640  # x30 = 0x0000f280
    130: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    134: 01d000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000138
    138: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    13c: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000218c0
    140: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    144: 880f0f13  addi         x30, x30, -1920  # x30 = 0x0000f880
    148: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    14c: 005000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000150
    150: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    154: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000218e0
    158: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    15c: a80f0f13  addi         x30, x30, -1408  # x30 = 0x0000fa80
    160: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    164: 7ec000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000168
    168: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    16c: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00021900
    170: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    174: 080f0f13  addi         x30, x30, 128  # x30 = 0x00010080
    178: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    17c: 7d4000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000180
    180: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    184: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00021920
    188: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    18c: 280f0f13  addi         x30, x30, 640  # x30 = 0x00010280
    190: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    194: 7bc000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000198
    198: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    19c: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00021940
    1a0: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    1a4: 880f0f13  addi         x30, x30, -1920  # x30 = 0x00010880
    1a8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1ac: 7a4000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000001b0
    1b0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1b4: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00021960
    1b8: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    1bc: a80f0f13  addi         x30, x30, -1408  # x30 = 0x00010a80
    1c0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1c4: 78c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000001c8
    1c8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1cc: 980f8f93  addi         x31, x31, -1664  # x31 = 0x00021980
    1d0: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    1d4: 0a0f0f13  addi         x30, x30, 160  # x30 = 0x0000f0a0
    1d8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1dc: 774000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000001e0
    1e0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1e4: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x000219a0
    1e8: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    1ec: 2a0f0f13  addi         x30, x30, 672  # x30 = 0x0000f2a0
    1f0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1f4: 75c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000001f8
    1f8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    1fc: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000219c0
    200: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    204: 8a0f0f13  addi         x30, x30, -1888  # x30 = 0x0000f8a0
    208: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    20c: 744000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000210
    210: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    214: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000219e0
    218: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    21c: aa0f0f13  addi         x30, x30, -1376  # x30 = 0x0000faa0
    220: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    224: 72c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000228
    228: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    22c: a00f8f93  addi         x31, x31, -1536  # x31 = 0x00021a00
    230: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    234: 0a0f0f13  addi         x30, x30, 160  # x30 = 0x000100a0
    238: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    23c: 714000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000240
    240: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    244: a20f8f93  addi         x31, x31, -1504  # x31 = 0x00021a20
    248: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    24c: 2a0f0f13  addi         x30, x30, 672  # x30 = 0x000102a0
    250: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    254: 6fc000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000258
    258: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    25c: a40f8f93  addi         x31, x31, -1472  # x31 = 0x00021a40
    260: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    264: 8a0f0f13  addi         x30, x30, -1888  # x30 = 0x000108a0
    268: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    26c: 6e4000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000270
    270: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    274: a60f8f93  addi         x31, x31, -1440  # x31 = 0x00021a60
    278: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    27c: aa0f0f13  addi         x30, x30, -1376  # x30 = 0x00010aa0
    280: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    284: 6cc000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000288
    288: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    28c: a80f8f93  addi         x31, x31, -1408  # x31 = 0x00021a80
    290: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    294: 0c0f0f13  addi         x30, x30, 192  # x30 = 0x0000f0c0
    298: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    29c: 6b4000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000002a0
    2a0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2a4: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x00021aa0
    2a8: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    2ac: 2c0f0f13  addi         x30, x30, 704  # x30 = 0x0000f2c0
    2b0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2b4: 69c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000002b8
    2b8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2bc: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x00021ac0
    2c0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2c4: 8c0f0f13  addi         x30, x30, -1856  # x30 = 0x0000f8c0
    2c8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2cc: 684000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000002d0
    2d0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2d4: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x00021ae0
    2d8: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2dc: ac0f0f13  addi         x30, x30, -1344  # x30 = 0x0000fac0
    2e0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2e4: 66c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000002e8
    2e8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    2ec: b00f8f93  addi         x31, x31, -1280  # x31 = 0x00021b00
    2f0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    2f4: 0c0f0f13  addi         x30, x30, 192  # x30 = 0x000100c0
    2f8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2fc: 654000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000300
    300: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    304: b20f8f93  addi         x31, x31, -1248  # x31 = 0x00021b20
    308: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    30c: 2c0f0f13  addi         x30, x30, 704  # x30 = 0x000102c0
    310: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    314: 63c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000318
    318: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    31c: b40f8f93  addi         x31, x31, -1216  # x31 = 0x00021b40
    320: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    324: 8c0f0f13  addi         x30, x30, -1856  # x30 = 0x000108c0
    328: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    32c: 624000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000330
    330: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    334: b60f8f93  addi         x31, x31, -1184  # x31 = 0x00021b60
    338: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    33c: ac0f0f13  addi         x30, x30, -1344  # x30 = 0x00010ac0
    340: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    344: 60c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000348
    348: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    34c: b80f8f93  addi         x31, x31, -1152  # x31 = 0x00021b80
    350: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    354: 0e0f0f13  addi         x30, x30, 224  # x30 = 0x0000f0e0
    358: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    35c: 5f4000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000360
    360: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    364: ba0f8f93  addi         x31, x31, -1120  # x31 = 0x00021ba0
    368: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    36c: 2e0f0f13  addi         x30, x30, 736  # x30 = 0x0000f2e0
    370: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    374: 5dc000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000378
    378: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    37c: bc0f8f93  addi         x31, x31, -1088  # x31 = 0x00021bc0
    380: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    384: 8e0f0f13  addi         x30, x30, -1824  # x30 = 0x0000f8e0
    388: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    38c: 5c4000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000390
    390: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    394: be0f8f93  addi         x31, x31, -1056  # x31 = 0x00021be0
    398: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    39c: ae0f0f13  addi         x30, x30, -1312  # x30 = 0x0000fae0
    3a0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3a4: 5ac000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000003a8
    3a8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3ac: c00f8f93  addi         x31, x31, -1024  # x31 = 0x00021c00
    3b0: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    3b4: 0e0f0f13  addi         x30, x30, 224  # x30 = 0x000100e0
    3b8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3bc: 594000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000003c0
    3c0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3c4: c20f8f93  addi         x31, x31, -992  # x31 = 0x00021c20
    3c8: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    3cc: 2e0f0f13  addi         x30, x30, 736  # x30 = 0x000102e0
    3d0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3d4: 57c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000003d8
    3d8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3dc: c40f8f93  addi         x31, x31, -960  # x31 = 0x00021c40
    3e0: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    3e4: 8e0f0f13  addi         x30, x30, -1824  # x30 = 0x000108e0
    3e8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3ec: 564000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x000003f0
    3f0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    3f4: c60f8f93  addi         x31, x31, -928  # x31 = 0x00021c60
    3f8: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    3fc: ae0f0f13  addi         x30, x30, -1312  # x30 = 0x00010ae0
    400: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    404: 54c000ef  jal          x1, 0x00000950  # target 0x00000950; x1 = 0x00000408
    408: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    40c: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    410: 00525293  srli         x5, x4, 5
    414: 00229293  slli         x5, x5, 2
    418: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    41c: 90440413  addi         x8, x8, -1788  # x8 = 0x0000e904
    420: 00042383  lw           x7, 0(x8)  # param attention_core; 0x0000e904
    424: 00c00413  addi         x8, x0, 12  # x8 = 0x0000000c
    428: 0283d3b3  divu         x7, x7, x8
    42c: 0003d393  srli         x7, x7, 0
    430: 00a39393  slli         x7, x7, 10
    434: 007282b3  add          x5, x5, x7
    438: 00f27313  andi         x6, x4, 15
    43c: 00531313  slli         x6, x6, 5
    440: 01027393  andi         x7, x4, 16
    444: 00639393  slli         x7, x7, 6
    448: 00730333  add          x6, x6, x7
    44c: 558000ef  jal          x1, 0x000009a4  # target 0x000009a4; x1 = 0x00000450
    450: 570000ef  jal          x1, 0x000009c0  # target 0x000009c0; x1 = 0x00000454
    454: 00028393  addi         x7, x5, 0
    458: 00038f93  addi         x31, x7, 0
    45c: 580000ef  jal          x1, 0x000009dc  # target 0x000009dc; x1 = 0x00000460
    460: 000a8413  addi         x8, x21, 0
    464: 000b0493  addi         x9, x22, 0
    468: 00640533  add          x10, x8, x6
    46c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    470: c80f8f93  addi         x31, x31, -896  # x31 = 0x00021c80
    474: 00050f13  addi         x30, x10, 0
    478: 00048e93  addi         x29, x9, 0
    47c: 5ac000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000480
    480: 00640533  add          x10, x8, x6
    484: 20050513  addi         x10, x10, 512
    488: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    48c: ca0f8f93  addi         x31, x31, -864  # x31 = 0x00021ca0
    490: 00050f13  addi         x30, x10, 0
    494: 00048e93  addi         x29, x9, 0
    498: 590000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x0000049c
    49c: 00038f93  addi         x31, x7, 0
    4a0: 640000ef  jal          x1, 0x00000ae0  # target 0x00000ae0; x1 = 0x000004a4
    4a4: 000a8513  addi         x10, x21, 0
    4a8: 000b0593  addi         x11, x22, 0
    4ac: 00650633  add          x12, x10, x6
    4b0: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    4b4: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00036880 · arc_apb_reset_unit + 0x6880
    4b8: 00060f13  addi         x30, x12, 0
    4bc: 00058e93  addi         x29, x11, 0
    4c0: 568000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x000004c4
    4c4: 00650633  add          x12, x10, x6
    4c8: 20060613  addi         x12, x12, 512
    4cc: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    4d0: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000368a0 · arc_apb_reset_unit + 0x68a0
    4d4: 00060f13  addi         x30, x12, 0
    4d8: 00058e93  addi         x29, x11, 0
    4dc: 54c000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x000004e0
    4e0: 00128393  addi         x7, x5, 1
    4e4: 00038f93  addi         x31, x7, 0
    4e8: 4f4000ef  jal          x1, 0x000009dc  # target 0x000009dc; x1 = 0x000004ec
    4ec: 000a8413  addi         x8, x21, 0
    4f0: 000b0493  addi         x9, x22, 0
    4f4: 00640533  add          x10, x8, x6
    4f8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    4fc: cc0f8f93  addi         x31, x31, -832  # x31 = 0x00021cc0
    500: 00050f13  addi         x30, x10, 0
    504: 00048e93  addi         x29, x9, 0
    508: 520000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x0000050c
    50c: 00640533  add          x10, x8, x6
    510: 20050513  addi         x10, x10, 512
    514: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    518: ce0f8f93  addi         x31, x31, -800  # x31 = 0x00021ce0
    51c: 00050f13  addi         x30, x10, 0
    520: 00048e93  addi         x29, x9, 0
    524: 504000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000528
    528: 00038f93  addi         x31, x7, 0
    52c: 5b4000ef  jal          x1, 0x00000ae0  # target 0x00000ae0; x1 = 0x00000530
    530: 000a8513  addi         x10, x21, 0
    534: 000b0593  addi         x11, x22, 0
    538: 00650633  add          x12, x10, x6
    53c: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    540: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000368c0 · arc_apb_reset_unit + 0x68c0
    544: 00060f13  addi         x30, x12, 0
    548: 00058e93  addi         x29, x11, 0
    54c: 4dc000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000550
    550: 00650633  add          x12, x10, x6
    554: 20060613  addi         x12, x12, 512
    558: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    55c: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000368e0 · arc_apb_reset_unit + 0x68e0
    560: 00060f13  addi         x30, x12, 0
    564: 00058e93  addi         x29, x11, 0
    568: 4c0000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x0000056c
    56c: 00228393  addi         x7, x5, 2
    570: 00038f93  addi         x31, x7, 0
    574: 468000ef  jal          x1, 0x000009dc  # target 0x000009dc; x1 = 0x00000578
    578: 000a8413  addi         x8, x21, 0
    57c: 000b0493  addi         x9, x22, 0
    580: 00640533  add          x10, x8, x6
    584: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    588: d00f8f93  addi         x31, x31, -768  # x31 = 0x00021d00
    58c: 00050f13  addi         x30, x10, 0
    590: 00048e93  addi         x29, x9, 0
    594: 494000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000598
    598: 00640533  add          x10, x8, x6
    59c: 20050513  addi         x10, x10, 512
    5a0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    5a4: d20f8f93  addi         x31, x31, -736  # x31 = 0x00021d20
    5a8: 00050f13  addi         x30, x10, 0
    5ac: 00048e93  addi         x29, x9, 0
    5b0: 478000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x000005b4
    5b4: 00038f93  addi         x31, x7, 0
    5b8: 528000ef  jal          x1, 0x00000ae0  # target 0x00000ae0; x1 = 0x000005bc
    5bc: 000a8513  addi         x10, x21, 0
    5c0: 000b0593  addi         x11, x22, 0
    5c4: 00650633  add          x12, x10, x6
    5c8: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    5cc: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00036900 · arc_apb_reset_unit + 0x6900
    5d0: 00060f13  addi         x30, x12, 0
    5d4: 00058e93  addi         x29, x11, 0
    5d8: 450000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x000005dc
    5dc: 00650633  add          x12, x10, x6
    5e0: 20060613  addi         x12, x12, 512
    5e4: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    5e8: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00036920 · arc_apb_reset_unit + 0x6920
    5ec: 00060f13  addi         x30, x12, 0
    5f0: 00058e93  addi         x29, x11, 0
    5f4: 434000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x000005f8
    5f8: 00328393  addi         x7, x5, 3
    5fc: 00038f93  addi         x31, x7, 0
    600: 3dc000ef  jal          x1, 0x000009dc  # target 0x000009dc; x1 = 0x00000604
    604: 000a8413  addi         x8, x21, 0
    608: 000b0493  addi         x9, x22, 0
    60c: 00640533  add          x10, x8, x6
    610: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    614: d40f8f93  addi         x31, x31, -704  # x31 = 0x00021d40
    618: 00050f13  addi         x30, x10, 0
    61c: 00048e93  addi         x29, x9, 0
    620: 408000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000624
    624: 00640533  add          x10, x8, x6
    628: 20050513  addi         x10, x10, 512
    62c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    630: d60f8f93  addi         x31, x31, -672  # x31 = 0x00021d60
    634: 00050f13  addi         x30, x10, 0
    638: 00048e93  addi         x29, x9, 0
    63c: 3ec000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000640
    640: 00038f93  addi         x31, x7, 0
    644: 49c000ef  jal          x1, 0x00000ae0  # target 0x00000ae0; x1 = 0x00000648
    648: 000a8513  addi         x10, x21, 0
    64c: 000b0593  addi         x11, x22, 0
    650: 00650633  add          x12, x10, x6
    654: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    658: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00036940 · arc_apb_reset_unit + 0x6940
    65c: 00060f13  addi         x30, x12, 0
    660: 00058e93  addi         x29, x11, 0
    664: 3c4000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000668
    668: 00650633  add          x12, x10, x6
    66c: 20060613  addi         x12, x12, 512
    670: 00037fb7  lui          x31, 0x00037  # x31 = 0x00037000 · arc_apb_reset_unit + 0x7000
    674: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00036960 · arc_apb_reset_unit + 0x6960
    678: 00060f13  addi         x30, x12, 0
    67c: 00058e93  addi         x29, x11, 0
    680: 3a8000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000684
    684: 320000ef  jal          x1, 0x000009a4  # target 0x000009a4; x1 = 0x00000688
    688: 338000ef  jal          x1, 0x000009c0  # target 0x000009c0; x1 = 0x0000068c
    68c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    690: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    694: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    698: 00120213  addi         x4, x4, 1
    69c: 01021213  slli         x4, x4, 16
    6a0: 01025213  srli         x4, x4, 16
    6a4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6a8: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    6ac: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    6b0: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    6b4: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    6b8: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    6bc: 0ff0000f  fence        0xf, 0xf
    6c0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6c4: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    6c8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    6cc: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6d0: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    6d4: 00520233  add          x4, x4, x5
    6d8: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    6dc: 08030313  addi         x6, x6, 128  # x6 = 0x00022080
    6e0: 00626863  bltu         x4, x6, 0x000006f0  # target 0x000006f0
    6e4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    6e8: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    6ec: 40720233  sub          x4, x4, x7
loc_6f0:
    6f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6f4: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    6f8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    6fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    700: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    704: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    708: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    70c: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    710: 00520233  add          x4, x4, x5
    714: 00023337  lui          x6, 0x00023  # x6 = 0x00023000
    718: 88030313  addi         x6, x6, -1920  # x6 = 0x00022880
    71c: 00626863  bltu         x4, x6, 0x0000072c  # target 0x0000072c
    720: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    724: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    728: 40720233  sub          x4, x4, x7
loc_72c:
    72c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    730: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    734: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    738: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    73c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    740: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    744: 00120213  addi         x4, x4, 1
    748: 01021213  slli         x4, x4, 16
    74c: 01025213  srli         x4, x4, 16
    750: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    754: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    758: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    75c: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    760: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    764: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    768: 0ff0000f  fence        0xf, 0xf
    76c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    770: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    774: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    778: 00600393  addi         x7, x0, 6  # x7 = 0x00000006
loc_77c:
    77c: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    780: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    784: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    788: 40428333  sub          x6, x5, x4
    78c: 01031313  slli         x6, x6, 16
    790: 01035313  srli         x6, x6, 16
    794: 00737663  bgeu         x6, x7, 0x000007a0  # target 0x000007a0
    798: 0ff0000f  fence        0xf, 0xf
    79c: fe1ff06f  jal          x0, 0x0000077c  # target 0x0000077c
loc_7a0:
    7a0: 0ff0000f  fence        0xf, 0xf
    7a4: 200000ef  jal          x1, 0x000009a4  # target 0x000009a4; x1 = 0x000007a8
    7a8: 218000ef  jal          x1, 0x000009c0  # target 0x000009c0; x1 = 0x000007ac
    7ac: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    7b0: 37c000ef  jal          x1, 0x00000b2c  # target 0x00000b2c; x1 = 0x000007b4
    7b4: 000a8213  addi         x4, x21, 0
    7b8: 000b0293  addi         x5, x22, 0
    7bc: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    7c0: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    7c4: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    7c8: 00030f93  addi         x31, x6, 0
    7cc: 00020f13  addi         x30, x4, 0
    7d0: 00028e93  addi         x29, x5, 0
    7d4: 3a8000ef  jal          x1, 0x00000b7c  # target 0x00000b7c; x1 = 0x000007d8
    7d8: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    7dc: 350000ef  jal          x1, 0x00000b2c  # target 0x00000b2c; x1 = 0x000007e0
    7e0: 000a8213  addi         x4, x21, 0
    7e4: 000b0293  addi         x5, x22, 0
    7e8: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    7ec: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    7f0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    7f4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    7f8: 00730333  add          x6, x6, x7
    7fc: 00030f93  addi         x31, x6, 0
    800: 00020f13  addi         x30, x4, 0
    804: 00028e93  addi         x29, x5, 0
    808: 374000ef  jal          x1, 0x00000b7c  # target 0x00000b7c; x1 = 0x0000080c
    80c: 00200f93  addi         x31, x0, 2  # x31 = 0x00000002
    810: 31c000ef  jal          x1, 0x00000b2c  # target 0x00000b2c; x1 = 0x00000814
    814: 000a8213  addi         x4, x21, 0
    818: 000b0293  addi         x5, x22, 0
    81c: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    820: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    824: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    828: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    82c: 00730333  add          x6, x6, x7
    830: 00030f93  addi         x31, x6, 0
    834: 00020f13  addi         x30, x4, 0
    838: 00028e93  addi         x29, x5, 0
    83c: 340000ef  jal          x1, 0x00000b7c  # target 0x00000b7c; x1 = 0x00000840
    840: 00300f93  addi         x31, x0, 3  # x31 = 0x00000003
    844: 2e8000ef  jal          x1, 0x00000b2c  # target 0x00000b2c; x1 = 0x00000848
    848: 000a8213  addi         x4, x21, 0
    84c: 000b0293  addi         x5, x22, 0
    850: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    854: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    858: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    85c: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    860: 00730333  add          x6, x6, x7
    864: 00030f93  addi         x31, x6, 0
    868: 00020f13  addi         x30, x4, 0
    86c: 00028e93  addi         x29, x5, 0
    870: 30c000ef  jal          x1, 0x00000b7c  # target 0x00000b7c; x1 = 0x00000874
    874: 00400f93  addi         x31, x0, 4  # x31 = 0x00000004
    878: 2b4000ef  jal          x1, 0x00000b2c  # target 0x00000b2c; x1 = 0x0000087c
    87c: 000a8213  addi         x4, x21, 0
    880: 000b0293  addi         x5, x22, 0
    884: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    888: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    88c: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    890: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    894: 00730333  add          x6, x6, x7
    898: 00030f93  addi         x31, x6, 0
    89c: 00020f13  addi         x30, x4, 0
    8a0: 00028e93  addi         x29, x5, 0
    8a4: 2d8000ef  jal          x1, 0x00000b7c  # target 0x00000b7c; x1 = 0x000008a8
    8a8: 00500f93  addi         x31, x0, 5  # x31 = 0x00000005
    8ac: 280000ef  jal          x1, 0x00000b2c  # target 0x00000b2c; x1 = 0x000008b0
    8b0: 000a8213  addi         x4, x21, 0
    8b4: 000b0293  addi         x5, x22, 0
    8b8: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
    8bc: 87438393  addi         x7, x7, -1932  # x7 = 0xffb00874 · riscv_local_mem + 0x874
    8c0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x874 · 0xffb00874
    8c4: 000053b7  lui          x7, 0x00005  # x7 = 0x00005000
    8c8: 00730333  add          x6, x6, x7
    8cc: 00030f93  addi         x31, x6, 0
    8d0: 00020f13  addi         x30, x4, 0
    8d4: 00028e93  addi         x29, x5, 0
    8d8: 2a4000ef  jal          x1, 0x00000b7c  # target 0x00000b7c; x1 = 0x000008dc
    8dc: 0c8000ef  jal          x1, 0x000009a4  # target 0x000009a4; x1 = 0x000008e0
    8e0: 0e0000ef  jal          x1, 0x000009c0  # target 0x000009c0; x1 = 0x000008e4
    8e4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    8e8: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    8ec: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    8f0: 00620213  addi         x4, x4, 6
    8f4: 01021213  slli         x4, x4, 16
    8f8: 01025213  srli         x4, x4, 16
    8fc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    900: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    904: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    908: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    90c: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    910: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    914: 0ff0000f  fence        0xf, 0xf
    918: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    91c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    920: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    924: 000062b7  lui          x5, 0x00006  # x5 = 0x00006000
    928: 00520233  add          x4, x4, x5
    92c: 00020337  lui          x6, 0x00020  # x6 = 0x00020000
    930: 88030313  addi         x6, x6, -1920  # x6 = 0x0001f880
    934: 00626663  bltu         x4, x6, 0x00000940  # target 0x00000940
    938: 000063b7  lui          x7, 0x00006  # x7 = 0x00006000
    93c: 40720233  sub          x4, x4, x7
loc_940:
    940: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    944: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    948: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
loc_94c:
    94c: 2e80006f  jal          x0, 0x00000c34  # target 0x00000c34
loc_950:
    950: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    954: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    958: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    95c: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    960: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    964: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    968: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    96c: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    970: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    974: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    978: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    97c: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    980: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    984: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    988: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    98c: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    990: 020f8f93  addi         x31, x31, 32
    994: 020f0f13  addi         x30, x30, 32
    998: ff8e8e93  addi         x29, x29, -8
    99c: fa0e9ae3  bne          x29, x0, 0x00000950  # target 0x00000950
    9a0: 00008067  jalr         x0, 0(x1)
loc_9a4:
    9a4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9a8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    9ac: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    9b0: 000a0463  beq          x20, x0, 0x000009b8  # target 0x000009b8
    9b4: ff1ff06f  jal          x0, 0x000009a4  # target 0x000009a4
loc_9b8:
    9b8: 0ff0000f  fence        0xf, 0xf
    9bc: 00008067  jalr         x0, 0(x1)
loc_9c0:
    9c0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9c4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    9c8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    9cc: 000a0463  beq          x20, x0, 0x000009d4  # target 0x000009d4
    9d0: ff1ff06f  jal          x0, 0x000009c0  # target 0x000009c0
loc_9d4:
    9d4: 0ff0000f  fence        0xf, 0xf
    9d8: 00008067  jalr         x0, 0(x1)
loc_9dc:
    9dc: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    9e0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    9e4: 007a7d13  andi         x26, x20, 7
    9e8: ff8a7a13  andi         x20, x20, -8
    9ec: 01af8ab3  add          x21, x31, x26
    9f0: 007afb93  andi         x23, x21, 7
    9f4: 003ada93  srli         x21, x21, 3
    9f8: 00ba9a93  slli         x21, x21, 11
    9fc: 014a8ab3  add          x21, x21, x20
    a00: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000a00
    a04: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000a18
    a08: 001b9b93  slli         x23, x23, 1
    a0c: 017b0b33  add          x22, x22, x23
    a10: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    a14: 00008067  jalr         x0, 0(x1)
    a18: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    a1c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    a20: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    a24: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_a28:
    a28: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    a2c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    a30: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    a34: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    a38: 015a6463  bltu         x20, x21, 0x00000a40  # target 0x00000a40
    a3c: fedff06f  jal          x0, 0x00000a28  # target 0x00000a28
loc_a40:
    a40: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    a44: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    a48: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    a4c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    a50: 015a6463  bltu         x20, x21, 0x00000a58  # target 0x00000a58
    a54: fedff06f  jal          x0, 0x00000a40  # target 0x00000a40
loc_a58:
    a58: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    a5c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    a60: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    a64: 014a1a13  slli         x20, x20, 20
    a68: 014a5a13  srli         x20, x20, 20
    a6c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_a70:
    a70: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    a74: 000b0463  beq          x22, x0, 0x00000a7c  # target 0x00000a7c
    a78: ff9ff06f  jal          x0, 0x00000a70  # target 0x00000a70
loc_a7c:
    a7c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    a80: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    a84: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    a88: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    a8c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    a90: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    a94: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    a98: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    a9c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    aa0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    aa4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    aa8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    aac: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    ab0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    ab4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    ab8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    abc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    ac0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    ac4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    ac8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    acc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_ad0:
    ad0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    ad4: 000b0463  beq          x22, x0, 0x00000adc  # target 0x00000adc
    ad8: ff9ff06f  jal          x0, 0x00000ad0  # target 0x00000ad0
loc_adc:
    adc: 00008067  jalr         x0, 0(x1)
loc_ae0:
    ae0: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    ae4: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    ae8: 007a7d13  andi         x26, x20, 7
    aec: ff8a7a13  andi         x20, x20, -8
    af0: 01af8ab3  add          x21, x31, x26
    af4: 007afb93  andi         x23, x21, 7
    af8: 003ada93  srli         x21, x21, 3
    afc: 00ba9a93  slli         x21, x21, 11
    b00: 014a8ab3  add          x21, x21, x20
    b04: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000b04
    b08: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b1c
    b0c: 001b9b93  slli         x23, x23, 1
    b10: 017b0b33  add          x22, x22, x23
    b14: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b18: 00008067  jalr         x0, 0(x1)
    b1c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b20: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b24: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    b28: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_b2c:
    b2c: 0000fab7  lui          x21, 0x0000f  # x21 = 0x0000f000
    b30: 900a8a93  addi         x21, x21, -1792  # x21 = 0x0000e900
    b34: 000aaa03  lw           x20, 0(x21)  # param e2e_attention_partials; 0x0000e900
    b38: 007a7d13  andi         x26, x20, 7
    b3c: ff8a7a13  andi         x20, x20, -8
    b40: 01af8ab3  add          x21, x31, x26
    b44: 007afb93  andi         x23, x21, 7
    b48: 003ada93  srli         x21, x21, 3
    b4c: 00ca9a93  slli         x21, x21, 12
    b50: 014a8ab3  add          x21, x21, x20
    b54: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000b54
    b58: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b6c
    b5c: 001b9b93  slli         x23, x23, 1
    b60: 017b0b33  add          x22, x22, x23
    b64: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b68: 00008067  jalr         x0, 0(x1)
    b6c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b70: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b74: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    b78: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_b7c:
    b7c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    b80: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    b84: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    b88: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    b8c: 015a6463  bltu         x20, x21, 0x00000b94  # target 0x00000b94
    b90: fedff06f  jal          x0, 0x00000b7c  # target 0x00000b7c
loc_b94:
    b94: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    b98: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    b9c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    ba0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    ba4: 015a6463  bltu         x20, x21, 0x00000bac  # target 0x00000bac
    ba8: fedff06f  jal          x0, 0x00000b94  # target 0x00000b94
loc_bac:
    bac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    bb0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    bb4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    bb8: 014a1a13  slli         x20, x20, 20
    bbc: 014a5a13  srli         x20, x20, 20
    bc0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_bc4:
    bc4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    bc8: 000b0463  beq          x22, x0, 0x00000bd0  # target 0x00000bd0
    bcc: ff9ff06f  jal          x0, 0x00000bc4  # target 0x00000bc4
loc_bd0:
    bd0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    bd4: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    bd8: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    bdc: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    be0: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    be4: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    be8: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    bec: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    bf0: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    bf4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    bf8: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    bfc: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    c00: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    c04: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00001000
    c08: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    c0c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    c10: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    c14: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    c18: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    c1c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    c20: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_c24:
    c24: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    c28: 000b0463  beq          x22, x0, 0x00000c30  # target 0x00000c30
    c2c: ff9ff06f  jal          x0, 0x00000c24  # target 0x00000c24
loc_c30:
    c30: 00008067  jalr         x0, 0(x1)
    c34:           j FW_NCRISC+4   # return to firmware, linked at install
