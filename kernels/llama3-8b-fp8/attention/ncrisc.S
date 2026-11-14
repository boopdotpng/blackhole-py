# llama3 8b-fp8 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000252b7  lui          x5, 0x00025  # x5 = 0x00025000
      c: 88028293  addi         x5, x5, -1920  # x5 = 0x00024880
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00024880
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 08028293  addi         x5, x5, 128  # x5 = 0x00012080
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00012080
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 000252b7  lui          x5, 0x00025  # x5 = 0x00025000
     4c: 08028293  addi         x5, x5, 128  # x5 = 0x00025080
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00025080
     54: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     58: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     5c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     60: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     64: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     68: 0001d2b7  lui          x5, 0x0001d  # x5 = 0x0001d000
     6c: 88028293  addi         x5, x5, -1920  # x5 = 0x0001c880
     70: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x0001c880
     74: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     78: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     7c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     80: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     84: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     88: 000562b7  lui          x5, 0x00056  # x5 = 0x00056000
     8c: 98028293  addi         x5, x5, -1664  # x5 = 0x00055980
     90: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00055980
     94: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     98: 88820213  addi         x4, x4, -1912  # x4 = 0xffb00888 · riscv_local_mem + 0x888
     9c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00000000
     a0: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     a4: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     a8: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     ac: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     b0: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     b4: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     b8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     bc: 0063fa63  bgeu         x7, x6, 0x000000d0  # target 0x000000d0
     c0: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     c4: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     c8: 0063f463  bgeu         x7, x6, 0x000000d0  # target 0x000000d0
     cc: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_d0:
     d0: 00526463  bltu         x4, x5, 0x000000d8  # target 0x000000d8
     d4: 0680106f  jal          x0, 0x0000113c  # target 0x0000113c
loc_d8:
     d8: 00012237  lui          x4, 0x00012  # x4 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     dc: 08020213  addi         x4, x4, 128  # x4 = 0x00012080
     e0: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     e4: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
loc_e8:
     e8: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     ec: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     f0: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     f4: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     f8: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     fc: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
    100: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
    104: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
    108: 02020213  addi         x4, x4, 32
    10c: ff828293  addi         x5, x5, -8
    110: fc029ce3  bne          x5, x0, 0x000000e8  # target 0x000000e8
    114: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    118: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    11c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    120: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_124:
    124: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    128: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    12c: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    130: 40428333  sub          x6, x5, x4
    134: 01031313  slli         x6, x6, 16
    138: 01035313  srli         x6, x6, 16
    13c: 00737663  bgeu         x6, x7, 0x00000148  # target 0x00000148
    140: 0ff0000f  fence        0xf, 0xf
    144: fe1ff06f  jal          x0, 0x00000124  # target 0x00000124
loc_148:
    148: 0ff0000f  fence        0xf, 0xf
    14c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    150: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00024880
    154: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    158: 080f0f13  addi         x30, x30, 128  # x30 = 0x00012080
    15c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    160: 7e1000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000164
    164: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    168: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000248a0
    16c: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    170: 280f0f13  addi         x30, x30, 640  # x30 = 0x00012280
    174: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    178: 7c9000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000017c
    17c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    180: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000248c0
    184: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    188: 880f0f13  addi         x30, x30, -1920  # x30 = 0x00012880
    18c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    190: 7b1000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000194
    194: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    198: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000248e0
    19c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1a0: a80f0f13  addi         x30, x30, -1408  # x30 = 0x00012a80
    1a4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1a8: 799000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000001ac
    1ac: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1b0: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00024900
    1b4: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1b8: 080f0f13  addi         x30, x30, 128  # x30 = 0x00013080
    1bc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1c0: 781000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000001c4
    1c4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1c8: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00024920
    1cc: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1d0: 280f0f13  addi         x30, x30, 640  # x30 = 0x00013280
    1d4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1d8: 769000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000001dc
    1dc: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1e0: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00024940
    1e4: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    1e8: 880f0f13  addi         x30, x30, -1920  # x30 = 0x00013880
    1ec: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1f0: 751000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000001f4
    1f4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1f8: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00024960
    1fc: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    200: a80f0f13  addi         x30, x30, -1408  # x30 = 0x00013a80
    204: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    208: 739000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000020c
    20c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    210: 980f8f93  addi         x31, x31, -1664  # x31 = 0x00024980
    214: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    218: 0a0f0f13  addi         x30, x30, 160  # x30 = 0x000120a0
    21c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    220: 721000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000224
    224: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    228: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x000249a0
    22c: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    230: 2a0f0f13  addi         x30, x30, 672  # x30 = 0x000122a0
    234: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    238: 709000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000023c
    23c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    240: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000249c0
    244: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    248: 8a0f0f13  addi         x30, x30, -1888  # x30 = 0x000128a0
    24c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    250: 6f1000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000254
    254: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    258: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000249e0
    25c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    260: aa0f0f13  addi         x30, x30, -1376  # x30 = 0x00012aa0
    264: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    268: 6d9000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000026c
    26c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    270: a00f8f93  addi         x31, x31, -1536  # x31 = 0x00024a00
    274: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    278: 0a0f0f13  addi         x30, x30, 160  # x30 = 0x000130a0
    27c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    280: 6c1000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000284
    284: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    288: a20f8f93  addi         x31, x31, -1504  # x31 = 0x00024a20
    28c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    290: 2a0f0f13  addi         x30, x30, 672  # x30 = 0x000132a0
    294: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    298: 6a9000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000029c
    29c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2a0: a40f8f93  addi         x31, x31, -1472  # x31 = 0x00024a40
    2a4: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    2a8: 8a0f0f13  addi         x30, x30, -1888  # x30 = 0x000138a0
    2ac: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2b0: 691000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000002b4
    2b4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2b8: a60f8f93  addi         x31, x31, -1440  # x31 = 0x00024a60
    2bc: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    2c0: aa0f0f13  addi         x30, x30, -1376  # x30 = 0x00013aa0
    2c4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2c8: 679000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000002cc
    2cc: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2d0: a80f8f93  addi         x31, x31, -1408  # x31 = 0x00024a80
    2d4: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2d8: 0c0f0f13  addi         x30, x30, 192  # x30 = 0x000120c0
    2dc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2e0: 661000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000002e4
    2e4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2e8: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x00024aa0
    2ec: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2f0: 2c0f0f13  addi         x30, x30, 704  # x30 = 0x000122c0
    2f4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2f8: 649000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000002fc
    2fc: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    300: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x00024ac0
    304: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    308: 8c0f0f13  addi         x30, x30, -1856  # x30 = 0x000128c0
    30c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    310: 631000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000314
    314: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    318: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x00024ae0
    31c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    320: ac0f0f13  addi         x30, x30, -1344  # x30 = 0x00012ac0
    324: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    328: 619000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000032c
    32c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    330: b00f8f93  addi         x31, x31, -1280  # x31 = 0x00024b00
    334: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    338: 0c0f0f13  addi         x30, x30, 192  # x30 = 0x000130c0
    33c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    340: 601000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000344
    344: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    348: b20f8f93  addi         x31, x31, -1248  # x31 = 0x00024b20
    34c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    350: 2c0f0f13  addi         x30, x30, 704  # x30 = 0x000132c0
    354: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    358: 5e9000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000035c
    35c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    360: b40f8f93  addi         x31, x31, -1216  # x31 = 0x00024b40
    364: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    368: 8c0f0f13  addi         x30, x30, -1856  # x30 = 0x000138c0
    36c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    370: 5d1000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000374
    374: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    378: b60f8f93  addi         x31, x31, -1184  # x31 = 0x00024b60
    37c: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    380: ac0f0f13  addi         x30, x30, -1344  # x30 = 0x00013ac0
    384: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    388: 5b9000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000038c
    38c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    390: b80f8f93  addi         x31, x31, -1152  # x31 = 0x00024b80
    394: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    398: 0e0f0f13  addi         x30, x30, 224  # x30 = 0x000120e0
    39c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3a0: 5a1000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000003a4
    3a4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3a8: ba0f8f93  addi         x31, x31, -1120  # x31 = 0x00024ba0
    3ac: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3b0: 2e0f0f13  addi         x30, x30, 736  # x30 = 0x000122e0
    3b4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3b8: 589000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000003bc
    3bc: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3c0: bc0f8f93  addi         x31, x31, -1088  # x31 = 0x00024bc0
    3c4: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3c8: 8e0f0f13  addi         x30, x30, -1824  # x30 = 0x000128e0
    3cc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3d0: 571000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000003d4
    3d4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3d8: be0f8f93  addi         x31, x31, -1056  # x31 = 0x00024be0
    3dc: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3e0: ae0f0f13  addi         x30, x30, -1312  # x30 = 0x00012ae0
    3e4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3e8: 559000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x000003ec
    3ec: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3f0: c00f8f93  addi         x31, x31, -1024  # x31 = 0x00024c00
    3f4: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3f8: 0e0f0f13  addi         x30, x30, 224  # x30 = 0x000130e0
    3fc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    400: 541000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000404
    404: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    408: c20f8f93  addi         x31, x31, -992  # x31 = 0x00024c20
    40c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    410: 2e0f0f13  addi         x30, x30, 736  # x30 = 0x000132e0
    414: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    418: 529000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000041c
    41c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    420: c40f8f93  addi         x31, x31, -960  # x31 = 0x00024c40
    424: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    428: 8e0f0f13  addi         x30, x30, -1824  # x30 = 0x000138e0
    42c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    430: 511000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x00000434
    434: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    438: c60f8f93  addi         x31, x31, -928  # x31 = 0x00024c60
    43c: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    440: ae0f0f13  addi         x30, x30, -1312  # x30 = 0x00013ae0
    444: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    448: 4f9000ef  jal          x1, 0x00001140  # target 0x00001140; x1 = 0x0000044c
    44c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    450: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    454: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    458: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    45c: 00520233  add          x4, x4, x5
    460: 00014337  lui          x6, 0x00014  # x6 = 0x00014000
    464: 08030313  addi         x6, x6, 128  # x6 = 0x00014080
    468: 00626663  bltu         x4, x6, 0x00000474  # target 0x00000474
    46c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    470: 40720233  sub          x4, x4, x7
loc_474:
    474: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    478: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    47c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    480: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    484: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    488: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    48c: 00420213  addi         x4, x4, 4
    490: 01021213  slli         x4, x4, 16
    494: 01025213  srli         x4, x4, 16
    498: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    49c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4a0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    4a4: ffb482b7  lui          x5, 0xffb48  # x5 = 0xffb48000
    4a8: 02828293  addi         x5, x5, 40  # x5 = 0xffb48028
    4ac: 0042a023  sw           x4, 0(x5)  # 0xffb48028; write runtime value
    4b0: 0ff0000f  fence        0xf, 0xf
    4b4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4b8: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    4bc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    4c0: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4c4: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    4c8: 00520233  add          x4, x4, x5
    4cc: 00026337  lui          x6, 0x00026  # x6 = 0x00026000
    4d0: 88030313  addi         x6, x6, -1920  # x6 = 0x00025880
    4d4: 00626863  bltu         x4, x6, 0x000004e4  # target 0x000004e4
    4d8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4dc: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    4e0: 40720233  sub          x4, x4, x7
loc_4e4:
    4e4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4e8: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    4ec: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    4f0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4f4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    4f8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    4fc: 00120213  addi         x4, x4, 1
    500: 01021213  slli         x4, x4, 16
    504: 01025213  srli         x4, x4, 16
    508: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    50c: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    510: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    514: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    518: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    51c: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    520: 0ff0000f  fence        0xf, 0xf
    524: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    528: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
    52c: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
    530: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    534: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
    538: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    53c: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    540: 0063fa63  bgeu         x7, x6, 0x00000554  # target 0x00000554
    544: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    548: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
    54c: 0063f463  bgeu         x7, x6, 0x00000554  # target 0x00000554
    550: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_554:
    554: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    558: 0003a303  lw           x6, 0(x7)  # param kv_blocks; 0x00000790
    55c: fff30313  addi         x6, x6, -1
    560: 025372b3  remu         x5, x6, x5
    564: 28429463  bne          x5, x4, 0x000007ec  # target 0x000007ec
    568: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    56c: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    570: 00525293  srli         x5, x4, 5
    574: 00229293  slli         x5, x5, 2
    578: 00012437  lui          x8, 0x00012  # x8 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    57c: 90040413  addi         x8, x8, -1792  # x8 = 0x00011900
    580: 00042383  lw           x7, 0(x8)  # param attention_core; 0x00011900
    584: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
    588: 0283d3b3  divu         x7, x7, x8
    58c: 0003d393  srli         x7, x7, 0
    590: 00a39393  slli         x7, x7, 10
    594: 007282b3  add          x5, x5, x7
    598: 00f27313  andi         x6, x4, 15
    59c: 00531313  slli         x6, x6, 5
    5a0: 01027393  andi         x7, x4, 16
    5a4: 00639393  slli         x7, x7, 6
    5a8: 00730333  add          x6, x6, x7
    5ac: 3e9000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x000005b0
    5b0: 401000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x000005b4
    5b4: 00028393  addi         x7, x5, 0
    5b8: 00038f93  addi         x31, x7, 0
    5bc: 411000ef  jal          x1, 0x000011cc  # target 0x000011cc; x1 = 0x000005c0
    5c0: 000a8413  addi         x8, x21, 0
    5c4: 000b0493  addi         x9, x22, 0
    5c8: 00640533  add          x10, x8, x6
    5cc: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    5d0: c80f8f93  addi         x31, x31, -896  # x31 = 0x00024c80
    5d4: 00050f13  addi         x30, x10, 0
    5d8: 00048e93  addi         x29, x9, 0
    5dc: 43d000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000005e0
    5e0: 00640533  add          x10, x8, x6
    5e4: 20050513  addi         x10, x10, 512
    5e8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    5ec: ca0f8f93  addi         x31, x31, -864  # x31 = 0x00024ca0
    5f0: 00050f13  addi         x30, x10, 0
    5f4: 00048e93  addi         x29, x9, 0
    5f8: 421000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000005fc
    5fc: 00038f93  addi         x31, x7, 0
    600: 4d1000ef  jal          x1, 0x000012d0  # target 0x000012d0; x1 = 0x00000604
    604: 000a8513  addi         x10, x21, 0
    608: 000b0593  addi         x11, x22, 0
    60c: 00650633  add          x12, x10, x6
    610: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    614: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00025880
    618: 00060f13  addi         x30, x12, 0
    61c: 00058e93  addi         x29, x11, 0
    620: 3f9000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000624
    624: 00650633  add          x12, x10, x6
    628: 20060613  addi         x12, x12, 512
    62c: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    630: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000258a0
    634: 00060f13  addi         x30, x12, 0
    638: 00058e93  addi         x29, x11, 0
    63c: 3dd000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000640
    640: 00128393  addi         x7, x5, 1
    644: 00038f93  addi         x31, x7, 0
    648: 385000ef  jal          x1, 0x000011cc  # target 0x000011cc; x1 = 0x0000064c
    64c: 000a8413  addi         x8, x21, 0
    650: 000b0493  addi         x9, x22, 0
    654: 00640533  add          x10, x8, x6
    658: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    65c: cc0f8f93  addi         x31, x31, -832  # x31 = 0x00024cc0
    660: 00050f13  addi         x30, x10, 0
    664: 00048e93  addi         x29, x9, 0
    668: 3b1000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x0000066c
    66c: 00640533  add          x10, x8, x6
    670: 20050513  addi         x10, x10, 512
    674: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    678: ce0f8f93  addi         x31, x31, -800  # x31 = 0x00024ce0
    67c: 00050f13  addi         x30, x10, 0
    680: 00048e93  addi         x29, x9, 0
    684: 395000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000688
    688: 00038f93  addi         x31, x7, 0
    68c: 445000ef  jal          x1, 0x000012d0  # target 0x000012d0; x1 = 0x00000690
    690: 000a8513  addi         x10, x21, 0
    694: 000b0593  addi         x11, x22, 0
    698: 00650633  add          x12, x10, x6
    69c: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    6a0: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000258c0
    6a4: 00060f13  addi         x30, x12, 0
    6a8: 00058e93  addi         x29, x11, 0
    6ac: 36d000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000006b0
    6b0: 00650633  add          x12, x10, x6
    6b4: 20060613  addi         x12, x12, 512
    6b8: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    6bc: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000258e0
    6c0: 00060f13  addi         x30, x12, 0
    6c4: 00058e93  addi         x29, x11, 0
    6c8: 351000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000006cc
    6cc: 00228393  addi         x7, x5, 2
    6d0: 00038f93  addi         x31, x7, 0
    6d4: 2f9000ef  jal          x1, 0x000011cc  # target 0x000011cc; x1 = 0x000006d8
    6d8: 000a8413  addi         x8, x21, 0
    6dc: 000b0493  addi         x9, x22, 0
    6e0: 00640533  add          x10, x8, x6
    6e4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    6e8: d00f8f93  addi         x31, x31, -768  # x31 = 0x00024d00
    6ec: 00050f13  addi         x30, x10, 0
    6f0: 00048e93  addi         x29, x9, 0
    6f4: 325000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000006f8
    6f8: 00640533  add          x10, x8, x6
    6fc: 20050513  addi         x10, x10, 512
    700: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    704: d20f8f93  addi         x31, x31, -736  # x31 = 0x00024d20
    708: 00050f13  addi         x30, x10, 0
    70c: 00048e93  addi         x29, x9, 0
    710: 309000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000714
    714: 00038f93  addi         x31, x7, 0
    718: 3b9000ef  jal          x1, 0x000012d0  # target 0x000012d0; x1 = 0x0000071c
    71c: 000a8513  addi         x10, x21, 0
    720: 000b0593  addi         x11, x22, 0
    724: 00650633  add          x12, x10, x6
    728: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    72c: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00025900
    730: 00060f13  addi         x30, x12, 0
    734: 00058e93  addi         x29, x11, 0
    738: 2e1000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x0000073c
    73c: 00650633  add          x12, x10, x6
    740: 20060613  addi         x12, x12, 512
    744: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    748: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00025920
    74c: 00060f13  addi         x30, x12, 0
    750: 00058e93  addi         x29, x11, 0
    754: 2c5000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000758
    758: 00328393  addi         x7, x5, 3
    75c: 00038f93  addi         x31, x7, 0
    760: 26d000ef  jal          x1, 0x000011cc  # target 0x000011cc; x1 = 0x00000764
    764: 000a8413  addi         x8, x21, 0
    768: 000b0493  addi         x9, x22, 0
    76c: 00640533  add          x10, x8, x6
    770: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    774: d40f8f93  addi         x31, x31, -704  # x31 = 0x00024d40
    778: 00050f13  addi         x30, x10, 0
    77c: 00048e93  addi         x29, x9, 0
    780: 299000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000784
    784: 00640533  add          x10, x8, x6
    788: 20050513  addi         x10, x10, 512
    78c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    790: d60f8f93  addi         x31, x31, -672  # x31 = 0x00024d60
    794: 00050f13  addi         x30, x10, 0
    798: 00048e93  addi         x29, x9, 0
    79c: 27d000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000007a0
    7a0: 00038f93  addi         x31, x7, 0
    7a4: 32d000ef  jal          x1, 0x000012d0  # target 0x000012d0; x1 = 0x000007a8
    7a8: 000a8513  addi         x10, x21, 0
    7ac: 000b0593  addi         x11, x22, 0
    7b0: 00650633  add          x12, x10, x6
    7b4: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    7b8: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00025940
    7bc: 00060f13  addi         x30, x12, 0
    7c0: 00058e93  addi         x29, x11, 0
    7c4: 255000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000007c8
    7c8: 00650633  add          x12, x10, x6
    7cc: 20060613  addi         x12, x12, 512
    7d0: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    7d4: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00025960
    7d8: 00060f13  addi         x30, x12, 0
    7dc: 00058e93  addi         x29, x11, 0
    7e0: 239000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000007e4
    7e4: 1b1000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x000007e8
    7e8: 1c9000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x000007ec
loc_7ec:
    7ec: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7f0: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    7f4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    7f8: 00600393  addi         x7, x0, 6  # x7 = 0x00000006
loc_7fc:
    7fc: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    800: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    804: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    808: 40428333  sub          x6, x5, x4
    80c: 01031313  slli         x6, x6, 16
    810: 01035313  srli         x6, x6, 16
    814: 00737663  bgeu         x6, x7, 0x00000820  # target 0x00000820
    818: 0ff0000f  fence        0xf, 0xf
    81c: fe1ff06f  jal          x0, 0x000007fc  # target 0x000007fc
loc_820:
    820: 0ff0000f  fence        0xf, 0xf
    824: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    828: 90438393  addi         x7, x7, -1788  # x7 = 0x00011904
    82c: 0003a203  lw           x4, 0(x7)  # param attention_phase; 0x00011904
    830: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    834: 90838393  addi         x7, x7, -1784  # x7 = 0x00011908
    838: 0003a283  lw           x5, 0(x7)  # param attention_merger; 0x00011908
    83c: 00006337  lui          x6, 0x00006  # x6 = 0x00006000
    840: 02430333  mul          x6, x6, x4
    844: 000263b7  lui          x7, 0x00026  # x7 = 0x00026000
    848: 98038393  addi         x7, x7, -1664  # x7 = 0x00025980
    84c: 00730333  add          x6, x6, x7
    850: 145000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x00000854
    854: 15d000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x00000858
    858: 0a021863  bne          x4, x0, 0x00000908  # target 0x00000908
    85c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    860: 006383b3  add          x7, x7, x6
    864: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    868: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001c880
    86c: 00038f13  addi         x30, x7, 0
    870: 00028e93  addi         x29, x5, 0
    874: 2a9000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000878
    878: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    87c: 006383b3  add          x7, x7, x6
    880: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    884: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001d880
    888: 00038f13  addi         x30, x7, 0
    88c: 00028e93  addi         x29, x5, 0
    890: 28d000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000894
    894: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    898: 006383b3  add          x7, x7, x6
    89c: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    8a0: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001e880
    8a4: 00038f13  addi         x30, x7, 0
    8a8: 00028e93  addi         x29, x5, 0
    8ac: 271000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x000008b0
    8b0: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    8b4: 006383b3  add          x7, x7, x6
    8b8: 00020fb7  lui          x31, 0x00020  # x31 = 0x00020000
    8bc: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001f880
    8c0: 00038f13  addi         x30, x7, 0
    8c4: 00028e93  addi         x29, x5, 0
    8c8: 255000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x000008cc
    8cc: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    8d0: 006383b3  add          x7, x7, x6
    8d4: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    8d8: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00020880
    8dc: 00038f13  addi         x30, x7, 0
    8e0: 00028e93  addi         x29, x5, 0
    8e4: 239000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x000008e8
    8e8: 000053b7  lui          x7, 0x00005  # x7 = 0x00005000
    8ec: 006383b3  add          x7, x7, x6
    8f0: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    8f4: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00021880
    8f8: 00038f13  addi         x30, x7, 0
    8fc: 00028e93  addi         x29, x5, 0
    900: 21d000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000904
    904: 0ac0006f  jal          x0, 0x000009b0  # target 0x000009b0
loc_908:
    908: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    90c: 006383b3  add          x7, x7, x6
    910: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    914: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001c880
    918: 00038f13  addi         x30, x7, 0
    91c: 00028e93  addi         x29, x5, 0
    920: 1fd000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000924
    924: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    928: 006383b3  add          x7, x7, x6
    92c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    930: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001d880
    934: 00038f13  addi         x30, x7, 0
    938: 00028e93  addi         x29, x5, 0
    93c: 1e1000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000940
    940: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    944: 006383b3  add          x7, x7, x6
    948: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    94c: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001e880
    950: 00038f13  addi         x30, x7, 0
    954: 00028e93  addi         x29, x5, 0
    958: 1c5000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x0000095c
    95c: 000053b7  lui          x7, 0x00005  # x7 = 0x00005000
    960: 006383b3  add          x7, x7, x6
    964: 00020fb7  lui          x31, 0x00020  # x31 = 0x00020000
    968: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001f880
    96c: 00038f13  addi         x30, x7, 0
    970: 00028e93  addi         x29, x5, 0
    974: 1a9000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000978
    978: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    97c: 006383b3  add          x7, x7, x6
    980: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    984: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00020880
    988: 00038f13  addi         x30, x7, 0
    98c: 00028e93  addi         x29, x5, 0
    990: 18d000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x00000994
    994: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    998: 006383b3  add          x7, x7, x6
    99c: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    9a0: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00021880
    9a4: 00038f13  addi         x30, x7, 0
    9a8: 00028e93  addi         x29, x5, 0
    9ac: 171000ef  jal          x1, 0x0000131c  # target 0x0000131c; x1 = 0x000009b0
loc_9b0:
    9b0: 7e4000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x000009b4
    9b4: 7fc000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x000009b8
    9b8: 7dc000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x000009bc
    9bc: 7f4000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x000009c0
    9c0: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    9c4: 040f8f93  addi         x31, x31, 64  # x31 = 0x00012040
    9c8: 00028f13  addi         x30, x5, 0
loc_9cc:
    9cc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9d0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    9d4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    9d8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    9dc: 015a6463  bltu         x20, x21, 0x000009e4  # target 0x000009e4
    9e0: fedff06f  jal          x0, 0x000009cc  # target 0x000009cc
loc_9e4:
    9e4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9e8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    9ec: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    9f0: 014a1a13  slli         x20, x20, 20
    9f4: 014a5a13  srli         x20, x20, 20
    9f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_9fc:
    9fc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    a00: 000b0463  beq          x22, x0, 0x00000a08  # target 0x00000a08
    a04: ff9ff06f  jal          x0, 0x000009fc  # target 0x000009fc
loc_a08:
    a08: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    a0c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write 0x00012040
    a10: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    a14: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    a18: 00058c37  lui          x24, 0x00058  # x24 = 0x00058000 · arc_apb_niu1 + 0x0
    a1c: 980c0c13  addi         x24, x24, -1664  # x24 = 0x00057980
    a20: 018ba623  sw           x24, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write 0x00057980
    a24: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    a28: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    a2c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    a30: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    a34: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    a38: 091c0c13  addi         x24, x24, 145  # x24 = 0x00002091
    a3c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002091
    a40: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a44: 07cc0c13  addi         x24, x24, 124  # x24 = 0x0000107c
    a48: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x0000107c
    a4c: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    a50: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    a54: 038ba423  sw           x24, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000001
    a58: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    a5c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    a60: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    a64: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    a68: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_a6c:
    a6c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    a70: 000b0463  beq          x22, x0, 0x00000a78  # target 0x00000a78
    a74: ff9ff06f  jal          x0, 0x00000a6c  # target 0x00000a6c
loc_a78:
    a78: 738000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x00000a7c
    a7c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    a80: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    a84: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    a88: 00620213  addi         x4, x4, 6
    a8c: 01021213  slli         x4, x4, 16
    a90: 01025213  srli         x4, x4, 16
    a94: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    a98: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    a9c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    aa0: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    aa4: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    aa8: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    aac: 0ff0000f  fence        0xf, 0xf
    ab0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    ab4: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    ab8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    abc: 000062b7  lui          x5, 0x00006  # x5 = 0x00006000
    ac0: 00520233  add          x4, x4, x5
    ac4: 00023337  lui          x6, 0x00023  # x6 = 0x00023000
    ac8: 88030313  addi         x6, x6, -1920  # x6 = 0x00022880
    acc: 00626663  bltu         x4, x6, 0x00000ad8  # target 0x00000ad8
    ad0: 000063b7  lui          x7, 0x00006  # x7 = 0x00006000
    ad4: 40720233  sub          x4, x4, x7
loc_ad8:
    ad8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    adc: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    ae0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    ae4: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    ae8: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    aec: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    af0: 64021663  bne          x4, x0, 0x0000113c  # target 0x0000113c
    af4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    af8: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    afc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    b00: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_b04:
    b04: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    b08: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    b0c: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    b10: 40428333  sub          x6, x5, x4
    b14: 01031313  slli         x6, x6, 16
    b18: 01035313  srli         x6, x6, 16
    b1c: 00737663  bgeu         x6, x7, 0x00000b28  # target 0x00000b28
    b20: 0ff0000f  fence        0xf, 0xf
    b24: fe1ff06f  jal          x0, 0x00000b04  # target 0x00000b04
loc_b28:
    b28: 0ff0000f  fence        0xf, 0xf
    b2c: 668000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x00000b30
    b30: 680000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x00000b34
    b34: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b38: 90028293  addi         x5, x5, -1792  # x5 = 0x00011900
    b3c: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x00011900
    b40: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    b44: 02525233  divu         x4, x4, x5
    b48: 00921213  slli         x4, x4, 9
    b4c: 00020293  addi         x5, x4, 0
    b50: 00a2d313  srli         x6, x5, 10
    b54: 00030f93  addi         x31, x6, 0
    b58: 07d000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000b5c
    b5c: 000a8393  addi         x7, x21, 0
    b60: 000b0413  addi         x8, x22, 0
    b64: 3ff2f293  andi         x5, x5, 1023
    b68: 00129493  slli         x9, x5, 1
    b6c: 007484b3  add          x9, x9, x7
    b70: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    b74: 980f8f93  addi         x31, x31, -1664  # x31 = 0x00055980
    b78: 00048f13  addi         x30, x9, 0
    b7c: 00040e93  addi         x29, x8, 0
    b80: 698000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000b84
    b84: 01028293  addi         x5, x5, 16
    b88: 00129493  slli         x9, x5, 1
    b8c: 007484b3  add          x9, x9, x7
    b90: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    b94: b80f8f93  addi         x31, x31, -1152  # x31 = 0x00055b80
    b98: 00048f13  addi         x30, x9, 0
    b9c: 00040e93  addi         x29, x8, 0
    ba0: 678000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000ba4
    ba4: 02020293  addi         x5, x4, 32
    ba8: 00a2d313  srli         x6, x5, 10
    bac: 00030f93  addi         x31, x6, 0
    bb0: 025000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000bb4
    bb4: 000a8393  addi         x7, x21, 0
    bb8: 000b0413  addi         x8, x22, 0
    bbc: 3ff2f293  andi         x5, x5, 1023
    bc0: 00129493  slli         x9, x5, 1
    bc4: 007484b3  add          x9, x9, x7
    bc8: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    bcc: 180f8f93  addi         x31, x31, 384  # x31 = 0x00056180
    bd0: 00048f13  addi         x30, x9, 0
    bd4: 00040e93  addi         x29, x8, 0
    bd8: 640000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000bdc
    bdc: 01028293  addi         x5, x5, 16
    be0: 00129493  slli         x9, x5, 1
    be4: 007484b3  add          x9, x9, x7
    be8: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    bec: 380f8f93  addi         x31, x31, 896  # x31 = 0x00056380
    bf0: 00048f13  addi         x30, x9, 0
    bf4: 00040e93  addi         x29, x8, 0
    bf8: 620000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000bfc
    bfc: 04020293  addi         x5, x4, 64
    c00: 00a2d313  srli         x6, x5, 10
    c04: 00030f93  addi         x31, x6, 0
    c08: 7cc000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000c0c
    c0c: 000a8393  addi         x7, x21, 0
    c10: 000b0413  addi         x8, x22, 0
    c14: 3ff2f293  andi         x5, x5, 1023
    c18: 00129493  slli         x9, x5, 1
    c1c: 007484b3  add          x9, x9, x7
    c20: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c24: 980f8f93  addi         x31, x31, -1664  # x31 = 0x00056980
    c28: 00048f13  addi         x30, x9, 0
    c2c: 00040e93  addi         x29, x8, 0
    c30: 5e8000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000c34
    c34: 01028293  addi         x5, x5, 16
    c38: 00129493  slli         x9, x5, 1
    c3c: 007484b3  add          x9, x9, x7
    c40: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c44: b80f8f93  addi         x31, x31, -1152  # x31 = 0x00056b80
    c48: 00048f13  addi         x30, x9, 0
    c4c: 00040e93  addi         x29, x8, 0
    c50: 5c8000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000c54
    c54: 06020293  addi         x5, x4, 96
    c58: 00a2d313  srli         x6, x5, 10
    c5c: 00030f93  addi         x31, x6, 0
    c60: 774000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000c64
    c64: 000a8393  addi         x7, x21, 0
    c68: 000b0413  addi         x8, x22, 0
    c6c: 3ff2f293  andi         x5, x5, 1023
    c70: 00129493  slli         x9, x5, 1
    c74: 007484b3  add          x9, x9, x7
    c78: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c7c: 180f8f93  addi         x31, x31, 384  # x31 = 0x00057180
    c80: 00048f13  addi         x30, x9, 0
    c84: 00040e93  addi         x29, x8, 0
    c88: 590000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000c8c
    c8c: 01028293  addi         x5, x5, 16
    c90: 00129493  slli         x9, x5, 1
    c94: 007484b3  add          x9, x9, x7
    c98: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c9c: 380f8f93  addi         x31, x31, 896  # x31 = 0x00057380
    ca0: 00048f13  addi         x30, x9, 0
    ca4: 00040e93  addi         x29, x8, 0
    ca8: 570000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000cac
    cac: 08020293  addi         x5, x4, 128
    cb0: 00a2d313  srli         x6, x5, 10
    cb4: 00030f93  addi         x31, x6, 0
    cb8: 71c000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000cbc
    cbc: 000a8393  addi         x7, x21, 0
    cc0: 000b0413  addi         x8, x22, 0
    cc4: 3ff2f293  andi         x5, x5, 1023
    cc8: 00129493  slli         x9, x5, 1
    ccc: 007484b3  add          x9, x9, x7
    cd0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    cd4: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x000559a0
    cd8: 00048f13  addi         x30, x9, 0
    cdc: 00040e93  addi         x29, x8, 0
    ce0: 538000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000ce4
    ce4: 01028293  addi         x5, x5, 16
    ce8: 00129493  slli         x9, x5, 1
    cec: 007484b3  add          x9, x9, x7
    cf0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    cf4: ba0f8f93  addi         x31, x31, -1120  # x31 = 0x00055ba0
    cf8: 00048f13  addi         x30, x9, 0
    cfc: 00040e93  addi         x29, x8, 0
    d00: 518000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000d04
    d04: 0a020293  addi         x5, x4, 160
    d08: 00a2d313  srli         x6, x5, 10
    d0c: 00030f93  addi         x31, x6, 0
    d10: 6c4000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000d14
    d14: 000a8393  addi         x7, x21, 0
    d18: 000b0413  addi         x8, x22, 0
    d1c: 3ff2f293  andi         x5, x5, 1023
    d20: 00129493  slli         x9, x5, 1
    d24: 007484b3  add          x9, x9, x7
    d28: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    d2c: 1a0f8f93  addi         x31, x31, 416  # x31 = 0x000561a0
    d30: 00048f13  addi         x30, x9, 0
    d34: 00040e93  addi         x29, x8, 0
    d38: 4e0000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000d3c
    d3c: 01028293  addi         x5, x5, 16
    d40: 00129493  slli         x9, x5, 1
    d44: 007484b3  add          x9, x9, x7
    d48: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    d4c: 3a0f8f93  addi         x31, x31, 928  # x31 = 0x000563a0
    d50: 00048f13  addi         x30, x9, 0
    d54: 00040e93  addi         x29, x8, 0
    d58: 4c0000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000d5c
    d5c: 0c020293  addi         x5, x4, 192
    d60: 00a2d313  srli         x6, x5, 10
    d64: 00030f93  addi         x31, x6, 0
    d68: 66c000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000d6c
    d6c: 000a8393  addi         x7, x21, 0
    d70: 000b0413  addi         x8, x22, 0
    d74: 3ff2f293  andi         x5, x5, 1023
    d78: 00129493  slli         x9, x5, 1
    d7c: 007484b3  add          x9, x9, x7
    d80: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    d84: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x000569a0
    d88: 00048f13  addi         x30, x9, 0
    d8c: 00040e93  addi         x29, x8, 0
    d90: 488000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000d94
    d94: 01028293  addi         x5, x5, 16
    d98: 00129493  slli         x9, x5, 1
    d9c: 007484b3  add          x9, x9, x7
    da0: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    da4: ba0f8f93  addi         x31, x31, -1120  # x31 = 0x00056ba0
    da8: 00048f13  addi         x30, x9, 0
    dac: 00040e93  addi         x29, x8, 0
    db0: 468000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000db4
    db4: 0e020293  addi         x5, x4, 224
    db8: 00a2d313  srli         x6, x5, 10
    dbc: 00030f93  addi         x31, x6, 0
    dc0: 614000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000dc4
    dc4: 000a8393  addi         x7, x21, 0
    dc8: 000b0413  addi         x8, x22, 0
    dcc: 3ff2f293  andi         x5, x5, 1023
    dd0: 00129493  slli         x9, x5, 1
    dd4: 007484b3  add          x9, x9, x7
    dd8: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    ddc: 1a0f8f93  addi         x31, x31, 416  # x31 = 0x000571a0
    de0: 00048f13  addi         x30, x9, 0
    de4: 00040e93  addi         x29, x8, 0
    de8: 430000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000dec
    dec: 01028293  addi         x5, x5, 16
    df0: 00129493  slli         x9, x5, 1
    df4: 007484b3  add          x9, x9, x7
    df8: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    dfc: 3a0f8f93  addi         x31, x31, 928  # x31 = 0x000573a0
    e00: 00048f13  addi         x30, x9, 0
    e04: 00040e93  addi         x29, x8, 0
    e08: 410000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000e0c
    e0c: 10020293  addi         x5, x4, 256
    e10: 00a2d313  srli         x6, x5, 10
    e14: 00030f93  addi         x31, x6, 0
    e18: 5bc000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000e1c
    e1c: 000a8393  addi         x7, x21, 0
    e20: 000b0413  addi         x8, x22, 0
    e24: 3ff2f293  andi         x5, x5, 1023
    e28: 00129493  slli         x9, x5, 1
    e2c: 007484b3  add          x9, x9, x7
    e30: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e34: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000559c0
    e38: 00048f13  addi         x30, x9, 0
    e3c: 00040e93  addi         x29, x8, 0
    e40: 3d8000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000e44
    e44: 01028293  addi         x5, x5, 16
    e48: 00129493  slli         x9, x5, 1
    e4c: 007484b3  add          x9, x9, x7
    e50: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e54: bc0f8f93  addi         x31, x31, -1088  # x31 = 0x00055bc0
    e58: 00048f13  addi         x30, x9, 0
    e5c: 00040e93  addi         x29, x8, 0
    e60: 3b8000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000e64
    e64: 12020293  addi         x5, x4, 288
    e68: 00a2d313  srli         x6, x5, 10
    e6c: 00030f93  addi         x31, x6, 0
    e70: 564000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000e74
    e74: 000a8393  addi         x7, x21, 0
    e78: 000b0413  addi         x8, x22, 0
    e7c: 3ff2f293  andi         x5, x5, 1023
    e80: 00129493  slli         x9, x5, 1
    e84: 007484b3  add          x9, x9, x7
    e88: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e8c: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x000561c0
    e90: 00048f13  addi         x30, x9, 0
    e94: 00040e93  addi         x29, x8, 0
    e98: 380000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000e9c
    e9c: 01028293  addi         x5, x5, 16
    ea0: 00129493  slli         x9, x5, 1
    ea4: 007484b3  add          x9, x9, x7
    ea8: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    eac: 3c0f8f93  addi         x31, x31, 960  # x31 = 0x000563c0
    eb0: 00048f13  addi         x30, x9, 0
    eb4: 00040e93  addi         x29, x8, 0
    eb8: 360000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000ebc
    ebc: 14020293  addi         x5, x4, 320
    ec0: 00a2d313  srli         x6, x5, 10
    ec4: 00030f93  addi         x31, x6, 0
    ec8: 50c000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000ecc
    ecc: 000a8393  addi         x7, x21, 0
    ed0: 000b0413  addi         x8, x22, 0
    ed4: 3ff2f293  andi         x5, x5, 1023
    ed8: 00129493  slli         x9, x5, 1
    edc: 007484b3  add          x9, x9, x7
    ee0: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    ee4: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000569c0
    ee8: 00048f13  addi         x30, x9, 0
    eec: 00040e93  addi         x29, x8, 0
    ef0: 328000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000ef4
    ef4: 01028293  addi         x5, x5, 16
    ef8: 00129493  slli         x9, x5, 1
    efc: 007484b3  add          x9, x9, x7
    f00: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    f04: bc0f8f93  addi         x31, x31, -1088  # x31 = 0x00056bc0
    f08: 00048f13  addi         x30, x9, 0
    f0c: 00040e93  addi         x29, x8, 0
    f10: 308000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000f14
    f14: 16020293  addi         x5, x4, 352
    f18: 00a2d313  srli         x6, x5, 10
    f1c: 00030f93  addi         x31, x6, 0
    f20: 4b4000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000f24
    f24: 000a8393  addi         x7, x21, 0
    f28: 000b0413  addi         x8, x22, 0
    f2c: 3ff2f293  andi         x5, x5, 1023
    f30: 00129493  slli         x9, x5, 1
    f34: 007484b3  add          x9, x9, x7
    f38: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    f3c: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x000571c0
    f40: 00048f13  addi         x30, x9, 0
    f44: 00040e93  addi         x29, x8, 0
    f48: 2d0000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000f4c
    f4c: 01028293  addi         x5, x5, 16
    f50: 00129493  slli         x9, x5, 1
    f54: 007484b3  add          x9, x9, x7
    f58: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    f5c: 3c0f8f93  addi         x31, x31, 960  # x31 = 0x000573c0
    f60: 00048f13  addi         x30, x9, 0
    f64: 00040e93  addi         x29, x8, 0
    f68: 2b0000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000f6c
    f6c: 18020293  addi         x5, x4, 384
    f70: 00a2d313  srli         x6, x5, 10
    f74: 00030f93  addi         x31, x6, 0
    f78: 45c000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000f7c
    f7c: 000a8393  addi         x7, x21, 0
    f80: 000b0413  addi         x8, x22, 0
    f84: 3ff2f293  andi         x5, x5, 1023
    f88: 00129493  slli         x9, x5, 1
    f8c: 007484b3  add          x9, x9, x7
    f90: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    f94: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000559e0
    f98: 00048f13  addi         x30, x9, 0
    f9c: 00040e93  addi         x29, x8, 0
    fa0: 278000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000fa4
    fa4: 01028293  addi         x5, x5, 16
    fa8: 00129493  slli         x9, x5, 1
    fac: 007484b3  add          x9, x9, x7
    fb0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    fb4: be0f8f93  addi         x31, x31, -1056  # x31 = 0x00055be0
    fb8: 00048f13  addi         x30, x9, 0
    fbc: 00040e93  addi         x29, x8, 0
    fc0: 258000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000fc4
    fc4: 1a020293  addi         x5, x4, 416
    fc8: 00a2d313  srli         x6, x5, 10
    fcc: 00030f93  addi         x31, x6, 0
    fd0: 404000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00000fd4
    fd4: 000a8393  addi         x7, x21, 0
    fd8: 000b0413  addi         x8, x22, 0
    fdc: 3ff2f293  andi         x5, x5, 1023
    fe0: 00129493  slli         x9, x5, 1
    fe4: 007484b3  add          x9, x9, x7
    fe8: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    fec: 1e0f8f93  addi         x31, x31, 480  # x31 = 0x000561e0
    ff0: 00048f13  addi         x30, x9, 0
    ff4: 00040e93  addi         x29, x8, 0
    ff8: 220000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00000ffc
    ffc: 01028293  addi         x5, x5, 16
   1000: 00129493  slli         x9, x5, 1
   1004: 007484b3  add          x9, x9, x7
   1008: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
   100c: 3e0f8f93  addi         x31, x31, 992  # x31 = 0x000563e0
   1010: 00048f13  addi         x30, x9, 0
   1014: 00040e93  addi         x29, x8, 0
   1018: 200000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x0000101c
   101c: 1c020293  addi         x5, x4, 448
   1020: 00a2d313  srli         x6, x5, 10
   1024: 00030f93  addi         x31, x6, 0
   1028: 3ac000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x0000102c
   102c: 000a8393  addi         x7, x21, 0
   1030: 000b0413  addi         x8, x22, 0
   1034: 3ff2f293  andi         x5, x5, 1023
   1038: 00129493  slli         x9, x5, 1
   103c: 007484b3  add          x9, x9, x7
   1040: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   1044: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000569e0
   1048: 00048f13  addi         x30, x9, 0
   104c: 00040e93  addi         x29, x8, 0
   1050: 1c8000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00001054
   1054: 01028293  addi         x5, x5, 16
   1058: 00129493  slli         x9, x5, 1
   105c: 007484b3  add          x9, x9, x7
   1060: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   1064: be0f8f93  addi         x31, x31, -1056  # x31 = 0x00056be0
   1068: 00048f13  addi         x30, x9, 0
   106c: 00040e93  addi         x29, x8, 0
   1070: 1a8000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x00001074
   1074: 1e020293  addi         x5, x4, 480
   1078: 00a2d313  srli         x6, x5, 10
   107c: 00030f93  addi         x31, x6, 0
   1080: 354000ef  jal          x1, 0x000013d4  # target 0x000013d4; x1 = 0x00001084
   1084: 000a8393  addi         x7, x21, 0
   1088: 000b0413  addi         x8, x22, 0
   108c: 3ff2f293  andi         x5, x5, 1023
   1090: 00129493  slli         x9, x5, 1
   1094: 007484b3  add          x9, x9, x7
   1098: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   109c: 1e0f8f93  addi         x31, x31, 480  # x31 = 0x000571e0
   10a0: 00048f13  addi         x30, x9, 0
   10a4: 00040e93  addi         x29, x8, 0
   10a8: 170000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000010ac
   10ac: 01028293  addi         x5, x5, 16
   10b0: 00129493  slli         x9, x5, 1
   10b4: 007484b3  add          x9, x9, x7
   10b8: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   10bc: 3e0f8f93  addi         x31, x31, 992  # x31 = 0x000573e0
   10c0: 00048f13  addi         x30, x9, 0
   10c4: 00040e93  addi         x29, x8, 0
   10c8: 150000ef  jal          x1, 0x00001218  # target 0x00001218; x1 = 0x000010cc
   10cc: 0c8000ef  jal          x1, 0x00001194  # target 0x00001194; x1 = 0x000010d0
   10d0: 0e0000ef  jal          x1, 0x000011b0  # target 0x000011b0; x1 = 0x000010d4
   10d4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
   10d8: 88828293  addi         x5, x5, -1912  # x5 = 0xffb00888 · riscv_local_mem + 0x888
   10dc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x888 · 0xffb00888
   10e0: 00420213  addi         x4, x4, 4
   10e4: 01021213  slli         x4, x4, 16
   10e8: 01025213  srli         x4, x4, 16
   10ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
   10f0: 88828293  addi         x5, x5, -1912  # x5 = 0xffb00888 · riscv_local_mem + 0x888
   10f4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
   10f8: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
   10fc: 02028293  addi         x5, x5, 32  # x5 = 0xffb51020
   1100: 0042a023  sw           x4, 0(x5)  # 0xffb51020; write runtime value
   1104: 0ff0000f  fence        0xf, 0xf
   1108: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
   110c: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
   1110: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
   1114: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
   1118: 00520233  add          x4, x4, x5
   111c: 00058337  lui          x6, 0x00058  # x6 = 0x00058000 · arc_apb_niu1 + 0x0
   1120: 98030313  addi         x6, x6, -1664  # x6 = 0x00057980
   1124: 00626663  bltu         x4, x6, 0x00001130  # target 0x00001130
   1128: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
   112c: 40720233  sub          x4, x4, x7
loc_1130:
   1130: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
   1134: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
   1138: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
loc_113c:
   113c: 2e40006f  jal          x0, 0x00001420  # target 0x00001420
loc_1140:
   1140: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
   1144: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
   1148: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
   114c: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
   1150: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
   1154: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
   1158: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
   115c: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
   1160: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
   1164: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
   1168: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
   116c: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
   1170: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
   1174: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
   1178: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
   117c: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
   1180: 020f8f93  addi         x31, x31, 32
   1184: 020f0f13  addi         x30, x30, 32
   1188: ff8e8e93  addi         x29, x29, -8
   118c: fa0e9ae3  bne          x29, x0, 0x00001140  # target 0x00001140
   1190: 00008067  jalr         x0, 0(x1)
loc_1194:
   1194: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1198: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
   119c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
   11a0: 000a0463  beq          x20, x0, 0x000011a8  # target 0x000011a8
   11a4: ff1ff06f  jal          x0, 0x00001194  # target 0x00001194
loc_11a8:
   11a8: 0ff0000f  fence        0xf, 0xf
   11ac: 00008067  jalr         x0, 0(x1)
loc_11b0:
   11b0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   11b4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
   11b8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
   11bc: 000a0463  beq          x20, x0, 0x000011c4  # target 0x000011c4
   11c0: ff1ff06f  jal          x0, 0x000011b0  # target 0x000011b0
loc_11c4:
   11c4: 0ff0000f  fence        0xf, 0xf
   11c8: 00008067  jalr         x0, 0(x1)
loc_11cc:
   11cc: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
   11d0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
   11d4: 007a7d13  andi         x26, x20, 7
   11d8: ff8a7a13  andi         x20, x20, -8
   11dc: 01af8ab3  add          x21, x31, x26
   11e0: 007afb93  andi         x23, x21, 7
   11e4: 003ada93  srli         x21, x21, 3
   11e8: 00ba9a93  slli         x21, x21, 11
   11ec: 014a8ab3  add          x21, x21, x20
   11f0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000011f0
   11f4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001208
   11f8: 001b9b93  slli         x23, x23, 1
   11fc: 017b0b33  add          x22, x22, x23
   1200: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1204: 00008067  jalr         x0, 0(x1)
   1208: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   120c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1210: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   1214: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_1218:
   1218: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   121c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
   1220: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
   1224: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   1228: 015a6463  bltu         x20, x21, 0x00001230  # target 0x00001230
   122c: fedff06f  jal          x0, 0x00001218  # target 0x00001218
loc_1230:
   1230: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1234: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
   1238: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
   123c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   1240: 015a6463  bltu         x20, x21, 0x00001248  # target 0x00001248
   1244: fedff06f  jal          x0, 0x00001230  # target 0x00001230
loc_1248:
   1248: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   124c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
   1250: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
   1254: 014a1a13  slli         x20, x20, 20
   1258: 014a5a13  srli         x20, x20, 20
   125c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_1260:
   1260: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   1264: 000b0463  beq          x22, x0, 0x0000126c  # target 0x0000126c
   1268: ff9ff06f  jal          x0, 0x00001260  # target 0x00001260
loc_126c:
   126c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   1270: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
   1274: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
   1278: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
   127c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
   1280: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
   1284: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
   1288: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
   128c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
   1290: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
   1294: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
   1298: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
   129c: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
   12a0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
   12a4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
   12a8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
   12ac: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
   12b0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   12b4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
   12b8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
   12bc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_12c0:
   12c0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   12c4: 000b0463  beq          x22, x0, 0x000012cc  # target 0x000012cc
   12c8: ff9ff06f  jal          x0, 0x000012c0  # target 0x000012c0
loc_12cc:
   12cc: 00008067  jalr         x0, 0(x1)
loc_12d0:
   12d0: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   12d4: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   12d8: 007a7d13  andi         x26, x20, 7
   12dc: ff8a7a13  andi         x20, x20, -8
   12e0: 01af8ab3  add          x21, x31, x26
   12e4: 007afb93  andi         x23, x21, 7
   12e8: 003ada93  srli         x21, x21, 3
   12ec: 00ba9a93  slli         x21, x21, 11
   12f0: 014a8ab3  add          x21, x21, x20
   12f4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000012f4
   12f8: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000130c
   12fc: 001b9b93  slli         x23, x23, 1
   1300: 017b0b33  add          x22, x22, x23
   1304: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1308: 00008067  jalr         x0, 0(x1)
   130c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1310: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1314: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   1318: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_131c:
   131c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1320: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
   1324: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
   1328: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   132c: 015a6463  bltu         x20, x21, 0x00001334  # target 0x00001334
   1330: fedff06f  jal          x0, 0x0000131c  # target 0x0000131c
loc_1334:
   1334: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1338: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
   133c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
   1340: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   1344: 015a6463  bltu         x20, x21, 0x0000134c  # target 0x0000134c
   1348: fedff06f  jal          x0, 0x00001334  # target 0x00001334
loc_134c:
   134c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1350: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
   1354: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
   1358: 014a1a13  slli         x20, x20, 20
   135c: 014a5a13  srli         x20, x20, 20
   1360: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_1364:
   1364: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   1368: 000b0463  beq          x22, x0, 0x00001370  # target 0x00001370
   136c: ff9ff06f  jal          x0, 0x00001364  # target 0x00001364
loc_1370:
   1370: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   1374: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
   1378: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
   137c: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
   1380: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
   1384: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
   1388: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
   138c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
   1390: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
   1394: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
   1398: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
   139c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
   13a0: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
   13a4: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00001000
   13a8: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
   13ac: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
   13b0: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
   13b4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   13b8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
   13bc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
   13c0: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_13c4:
   13c4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   13c8: 000b0463  beq          x22, x0, 0x000013d0  # target 0x000013d0
   13cc: ff9ff06f  jal          x0, 0x000013c4  # target 0x000013c4
loc_13d0:
   13d0: 00008067  jalr         x0, 0(x1)
loc_13d4:
   13d4: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
   13d8: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x0000078c
   13dc: 007a7d13  andi         x26, x20, 7
   13e0: ff8a7a13  andi         x20, x20, -8
   13e4: 01af8ab3  add          x21, x31, x26
   13e8: 007afb93  andi         x23, x21, 7
   13ec: 003ada93  srli         x21, x21, 3
   13f0: 00ba9a93  slli         x21, x21, 11
   13f4: 014a8ab3  add          x21, x21, x20
   13f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000013f8
   13fc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001410
   1400: 001b9b93  slli         x23, x23, 1
   1404: 017b0b33  add          x22, x22, x23
   1408: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   140c: 00008067  jalr         x0, 0(x1)
   1410: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1414: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1418: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   141c: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
   1420:           j FW_NCRISC+4   # return to firmware, linked at install
