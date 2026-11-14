# llama3 8b-bf16 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000252b7  lui          x5, 0x00025  # x5 = 0x00025000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00024800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00024800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00012000
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     3c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     40: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     44: 000252b7  lui          x5, 0x00025  # x5 = 0x00025000
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00025000
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 0001d2b7  lui          x5, 0x0001d  # x5 = 0x0001d000
     64: 80028293  addi         x5, x5, -2048  # x5 = 0x0001c800
     68: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x0001c800
     6c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     70: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     74: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     78: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     7c: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     80: 000562b7  lui          x5, 0x00056  # x5 = 0x00056000
     84: 90028293  addi         x5, x5, -1792  # x5 = 0x00055900
     88: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00055900
     8c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     90: 88820213  addi         x4, x4, -1912  # x4 = 0xffb00888 · riscv_local_mem + 0x888
     94: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00000000
     98: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     9c: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     a0: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     a4: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     a8: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     ac: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     b0: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     b4: 0063fa63  bgeu         x7, x6, 0x000000c8  # target 0x000000c8
     b8: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     bc: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     c0: 0063f463  bgeu         x7, x6, 0x000000c8  # target 0x000000c8
     c4: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_c8:
     c8: 00526463  bltu         x4, x5, 0x000000d0  # target 0x000000d0
     cc: 0580106f  jal          x0, 0x00001124  # target 0x00001124
loc_d0:
     d0: 00012237  lui          x4, 0x00012  # x4 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
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
    108: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    10c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    110: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    114: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_118:
    118: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    11c: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    120: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    124: 40428333  sub          x6, x5, x4
    128: 01031313  slli         x6, x6, 16
    12c: 01035313  srli         x6, x6, 16
    130: 00737663  bgeu         x6, x7, 0x0000013c  # target 0x0000013c
    134: 0ff0000f  fence        0xf, 0xf
    138: fe1ff06f  jal          x0, 0x00000118  # target 0x00000118
loc_13c:
    13c: 0ff0000f  fence        0xf, 0xf
    140: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    144: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00024800
    148: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    14c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    150: 7d9000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000154
    154: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    158: 820f8f93  addi         x31, x31, -2016  # x31 = 0x00024820
    15c: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    160: 200f0f13  addi         x30, x30, 512  # x30 = 0x00012200
    164: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    168: 7c1000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x0000016c
    16c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    170: 840f8f93  addi         x31, x31, -1984  # x31 = 0x00024840
    174: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    178: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00012800
    17c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    180: 7a9000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000184
    184: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    188: 860f8f93  addi         x31, x31, -1952  # x31 = 0x00024860
    18c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    190: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00012a00
    194: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    198: 791000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x0000019c
    19c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1a0: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00024880
    1a4: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1a8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1ac: 77d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000001b0
    1b0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1b4: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000248a0
    1b8: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1bc: 200f0f13  addi         x30, x30, 512  # x30 = 0x00013200
    1c0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1c4: 765000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000001c8
    1c8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1cc: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000248c0
    1d0: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    1d4: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00013800
    1d8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1dc: 74d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000001e0
    1e0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1e4: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000248e0
    1e8: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    1ec: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00013a00
    1f0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1f4: 735000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000001f8
    1f8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    1fc: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00024900
    200: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    204: 020f0f13  addi         x30, x30, 32  # x30 = 0x00012020
    208: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    20c: 71d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000210
    210: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    214: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00024920
    218: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    21c: 220f0f13  addi         x30, x30, 544  # x30 = 0x00012220
    220: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    224: 705000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000228
    228: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    22c: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00024940
    230: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    234: 820f0f13  addi         x30, x30, -2016  # x30 = 0x00012820
    238: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    23c: 6ed000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000240
    240: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    244: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00024960
    248: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    24c: a20f0f13  addi         x30, x30, -1504  # x30 = 0x00012a20
    250: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    254: 6d5000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000258
    258: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    25c: 980f8f93  addi         x31, x31, -1664  # x31 = 0x00024980
    260: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    264: 020f0f13  addi         x30, x30, 32  # x30 = 0x00013020
    268: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    26c: 6bd000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000270
    270: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    274: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x000249a0
    278: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    27c: 220f0f13  addi         x30, x30, 544  # x30 = 0x00013220
    280: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    284: 6a5000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000288
    288: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    28c: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000249c0
    290: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    294: 820f0f13  addi         x30, x30, -2016  # x30 = 0x00013820
    298: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    29c: 68d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000002a0
    2a0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2a4: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000249e0
    2a8: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    2ac: a20f0f13  addi         x30, x30, -1504  # x30 = 0x00013a20
    2b0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2b4: 675000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000002b8
    2b8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2bc: a00f8f93  addi         x31, x31, -1536  # x31 = 0x00024a00
    2c0: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2c4: 040f0f13  addi         x30, x30, 64  # x30 = 0x00012040
    2c8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2cc: 65d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000002d0
    2d0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2d4: a20f8f93  addi         x31, x31, -1504  # x31 = 0x00024a20
    2d8: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    2dc: 240f0f13  addi         x30, x30, 576  # x30 = 0x00012240
    2e0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2e4: 645000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000002e8
    2e8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    2ec: a40f8f93  addi         x31, x31, -1472  # x31 = 0x00024a40
    2f0: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    2f4: 840f0f13  addi         x30, x30, -1984  # x30 = 0x00012840
    2f8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2fc: 62d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000300
    300: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    304: a60f8f93  addi         x31, x31, -1440  # x31 = 0x00024a60
    308: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    30c: a40f0f13  addi         x30, x30, -1472  # x30 = 0x00012a40
    310: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    314: 615000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000318
    318: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    31c: a80f8f93  addi         x31, x31, -1408  # x31 = 0x00024a80
    320: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    324: 040f0f13  addi         x30, x30, 64  # x30 = 0x00013040
    328: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    32c: 5fd000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000330
    330: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    334: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x00024aa0
    338: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    33c: 240f0f13  addi         x30, x30, 576  # x30 = 0x00013240
    340: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    344: 5e5000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000348
    348: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    34c: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x00024ac0
    350: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    354: 840f0f13  addi         x30, x30, -1984  # x30 = 0x00013840
    358: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    35c: 5cd000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000360
    360: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    364: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x00024ae0
    368: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    36c: a40f0f13  addi         x30, x30, -1472  # x30 = 0x00013a40
    370: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    374: 5b5000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000378
    378: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    37c: b00f8f93  addi         x31, x31, -1280  # x31 = 0x00024b00
    380: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    384: 060f0f13  addi         x30, x30, 96  # x30 = 0x00012060
    388: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    38c: 59d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000390
    390: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    394: b20f8f93  addi         x31, x31, -1248  # x31 = 0x00024b20
    398: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    39c: 260f0f13  addi         x30, x30, 608  # x30 = 0x00012260
    3a0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3a4: 585000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000003a8
    3a8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3ac: b40f8f93  addi         x31, x31, -1216  # x31 = 0x00024b40
    3b0: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3b4: 860f0f13  addi         x30, x30, -1952  # x30 = 0x00012860
    3b8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3bc: 56d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000003c0
    3c0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3c4: b60f8f93  addi         x31, x31, -1184  # x31 = 0x00024b60
    3c8: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3cc: a60f0f13  addi         x30, x30, -1440  # x30 = 0x00012a60
    3d0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3d4: 555000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000003d8
    3d8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3dc: b80f8f93  addi         x31, x31, -1152  # x31 = 0x00024b80
    3e0: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3e4: 060f0f13  addi         x30, x30, 96  # x30 = 0x00013060
    3e8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    3ec: 53d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x000003f0
    3f0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    3f4: ba0f8f93  addi         x31, x31, -1120  # x31 = 0x00024ba0
    3f8: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    3fc: 260f0f13  addi         x30, x30, 608  # x30 = 0x00013260
    400: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    404: 525000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000408
    408: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    40c: bc0f8f93  addi         x31, x31, -1088  # x31 = 0x00024bc0
    410: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    414: 860f0f13  addi         x30, x30, -1952  # x30 = 0x00013860
    418: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    41c: 50d000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000420
    420: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    424: be0f8f93  addi         x31, x31, -1056  # x31 = 0x00024be0
    428: 00014f37  lui          x30, 0x00014  # x30 = 0x00014000
    42c: a60f0f13  addi         x30, x30, -1440  # x30 = 0x00013a60
    430: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    434: 4f5000ef  jal          x1, 0x00001128  # target 0x00001128; x1 = 0x00000438
    438: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    43c: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    440: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    444: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    448: 00520233  add          x4, x4, x5
    44c: 00014337  lui          x6, 0x00014  # x6 = 0x00014000
    450: 00626663  bltu         x4, x6, 0x0000045c  # target 0x0000045c
    454: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    458: 40720233  sub          x4, x4, x7
loc_45c:
    45c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    460: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    464: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    468: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    46c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    470: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    474: 00420213  addi         x4, x4, 4
    478: 01021213  slli         x4, x4, 16
    47c: 01025213  srli         x4, x4, 16
    480: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    484: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    488: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    48c: ffb482b7  lui          x5, 0xffb48  # x5 = 0xffb48000
    490: 02828293  addi         x5, x5, 40  # x5 = 0xffb48028
    494: 0042a023  sw           x4, 0(x5)  # 0xffb48028; write runtime value
    498: 0ff0000f  fence        0xf, 0xf
    49c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4a0: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    4a4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    4a8: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4ac: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    4b0: 00520233  add          x4, x4, x5
    4b4: 00026337  lui          x6, 0x00026  # x6 = 0x00026000
    4b8: 80030313  addi         x6, x6, -2048  # x6 = 0x00025800
    4bc: 00626863  bltu         x4, x6, 0x000004cc  # target 0x000004cc
    4c0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4c4: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    4c8: 40720233  sub          x4, x4, x7
loc_4cc:
    4cc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4d0: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    4d4: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    4d8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4dc: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    4e0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    4e4: 00120213  addi         x4, x4, 1
    4e8: 01021213  slli         x4, x4, 16
    4ec: 01025213  srli         x4, x4, 16
    4f0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4f4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    4f8: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    4fc: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    500: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    504: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    508: 0ff0000f  fence        0xf, 0xf
    50c: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    510: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
    514: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
    518: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    51c: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
    520: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    524: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    528: 0063fa63  bgeu         x7, x6, 0x0000053c  # target 0x0000053c
    52c: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    530: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
    534: 0063f463  bgeu         x7, x6, 0x0000053c  # target 0x0000053c
    538: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_53c:
    53c: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    540: 0003a303  lw           x6, 0(x7)  # param kv_blocks; 0x00000790
    544: fff30313  addi         x6, x6, -1
    548: 025372b3  remu         x5, x6, x5
    54c: 28429463  bne          x5, x4, 0x000007d4  # target 0x000007d4
    550: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    554: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    558: 00525293  srli         x5, x4, 5
    55c: 00229293  slli         x5, x5, 2
    560: 00012437  lui          x8, 0x00012  # x8 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    564: 90040413  addi         x8, x8, -1792  # x8 = 0x00011900
    568: 00042383  lw           x7, 0(x8)  # param attention_core; 0x00011900
    56c: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
    570: 0283d3b3  divu         x7, x7, x8
    574: 0003d393  srli         x7, x7, 0
    578: 00a39393  slli         x7, x7, 10
    57c: 007282b3  add          x5, x5, x7
    580: 00f27313  andi         x6, x4, 15
    584: 00531313  slli         x6, x6, 5
    588: 01027393  andi         x7, x4, 16
    58c: 00639393  slli         x7, x7, 6
    590: 00730333  add          x6, x6, x7
    594: 3e9000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x00000598
    598: 401000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x0000059c
    59c: 00028393  addi         x7, x5, 0
    5a0: 00038f93  addi         x31, x7, 0
    5a4: 411000ef  jal          x1, 0x000011b4  # target 0x000011b4; x1 = 0x000005a8
    5a8: 000a8413  addi         x8, x21, 0
    5ac: 000b0493  addi         x9, x22, 0
    5b0: 00640533  add          x10, x8, x6
    5b4: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    5b8: c00f8f93  addi         x31, x31, -1024  # x31 = 0x00024c00
    5bc: 00050f13  addi         x30, x10, 0
    5c0: 00048e93  addi         x29, x9, 0
    5c4: 43d000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000005c8
    5c8: 00640533  add          x10, x8, x6
    5cc: 20050513  addi         x10, x10, 512
    5d0: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    5d4: c20f8f93  addi         x31, x31, -992  # x31 = 0x00024c20
    5d8: 00050f13  addi         x30, x10, 0
    5dc: 00048e93  addi         x29, x9, 0
    5e0: 421000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000005e4
    5e4: 00038f93  addi         x31, x7, 0
    5e8: 4d1000ef  jal          x1, 0x000012b8  # target 0x000012b8; x1 = 0x000005ec
    5ec: 000a8513  addi         x10, x21, 0
    5f0: 000b0593  addi         x11, x22, 0
    5f4: 00650633  add          x12, x10, x6
    5f8: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    5fc: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00025800
    600: 00060f13  addi         x30, x12, 0
    604: 00058e93  addi         x29, x11, 0
    608: 3f9000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x0000060c
    60c: 00650633  add          x12, x10, x6
    610: 20060613  addi         x12, x12, 512
    614: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    618: 820f8f93  addi         x31, x31, -2016  # x31 = 0x00025820
    61c: 00060f13  addi         x30, x12, 0
    620: 00058e93  addi         x29, x11, 0
    624: 3dd000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000628
    628: 00128393  addi         x7, x5, 1
    62c: 00038f93  addi         x31, x7, 0
    630: 385000ef  jal          x1, 0x000011b4  # target 0x000011b4; x1 = 0x00000634
    634: 000a8413  addi         x8, x21, 0
    638: 000b0493  addi         x9, x22, 0
    63c: 00640533  add          x10, x8, x6
    640: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    644: c40f8f93  addi         x31, x31, -960  # x31 = 0x00024c40
    648: 00050f13  addi         x30, x10, 0
    64c: 00048e93  addi         x29, x9, 0
    650: 3b1000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000654
    654: 00640533  add          x10, x8, x6
    658: 20050513  addi         x10, x10, 512
    65c: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    660: c60f8f93  addi         x31, x31, -928  # x31 = 0x00024c60
    664: 00050f13  addi         x30, x10, 0
    668: 00048e93  addi         x29, x9, 0
    66c: 395000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000670
    670: 00038f93  addi         x31, x7, 0
    674: 445000ef  jal          x1, 0x000012b8  # target 0x000012b8; x1 = 0x00000678
    678: 000a8513  addi         x10, x21, 0
    67c: 000b0593  addi         x11, x22, 0
    680: 00650633  add          x12, x10, x6
    684: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    688: 840f8f93  addi         x31, x31, -1984  # x31 = 0x00025840
    68c: 00060f13  addi         x30, x12, 0
    690: 00058e93  addi         x29, x11, 0
    694: 36d000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000698
    698: 00650633  add          x12, x10, x6
    69c: 20060613  addi         x12, x12, 512
    6a0: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    6a4: 860f8f93  addi         x31, x31, -1952  # x31 = 0x00025860
    6a8: 00060f13  addi         x30, x12, 0
    6ac: 00058e93  addi         x29, x11, 0
    6b0: 351000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000006b4
    6b4: 00228393  addi         x7, x5, 2
    6b8: 00038f93  addi         x31, x7, 0
    6bc: 2f9000ef  jal          x1, 0x000011b4  # target 0x000011b4; x1 = 0x000006c0
    6c0: 000a8413  addi         x8, x21, 0
    6c4: 000b0493  addi         x9, x22, 0
    6c8: 00640533  add          x10, x8, x6
    6cc: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    6d0: c80f8f93  addi         x31, x31, -896  # x31 = 0x00024c80
    6d4: 00050f13  addi         x30, x10, 0
    6d8: 00048e93  addi         x29, x9, 0
    6dc: 325000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000006e0
    6e0: 00640533  add          x10, x8, x6
    6e4: 20050513  addi         x10, x10, 512
    6e8: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    6ec: ca0f8f93  addi         x31, x31, -864  # x31 = 0x00024ca0
    6f0: 00050f13  addi         x30, x10, 0
    6f4: 00048e93  addi         x29, x9, 0
    6f8: 309000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000006fc
    6fc: 00038f93  addi         x31, x7, 0
    700: 3b9000ef  jal          x1, 0x000012b8  # target 0x000012b8; x1 = 0x00000704
    704: 000a8513  addi         x10, x21, 0
    708: 000b0593  addi         x11, x22, 0
    70c: 00650633  add          x12, x10, x6
    710: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    714: 880f8f93  addi         x31, x31, -1920  # x31 = 0x00025880
    718: 00060f13  addi         x30, x12, 0
    71c: 00058e93  addi         x29, x11, 0
    720: 2e1000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000724
    724: 00650633  add          x12, x10, x6
    728: 20060613  addi         x12, x12, 512
    72c: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    730: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x000258a0
    734: 00060f13  addi         x30, x12, 0
    738: 00058e93  addi         x29, x11, 0
    73c: 2c5000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000740
    740: 00328393  addi         x7, x5, 3
    744: 00038f93  addi         x31, x7, 0
    748: 26d000ef  jal          x1, 0x000011b4  # target 0x000011b4; x1 = 0x0000074c
    74c: 000a8413  addi         x8, x21, 0
    750: 000b0493  addi         x9, x22, 0
    754: 00640533  add          x10, x8, x6
    758: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    75c: cc0f8f93  addi         x31, x31, -832  # x31 = 0x00024cc0
    760: 00050f13  addi         x30, x10, 0
    764: 00048e93  addi         x29, x9, 0
    768: 299000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x0000076c
    76c: 00640533  add          x10, x8, x6
    770: 20050513  addi         x10, x10, 512
    774: 00025fb7  lui          x31, 0x00025  # x31 = 0x00025000
    778: ce0f8f93  addi         x31, x31, -800  # x31 = 0x00024ce0
    77c: 00050f13  addi         x30, x10, 0
    780: 00048e93  addi         x29, x9, 0
    784: 27d000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000788
    788: 00038f93  addi         x31, x7, 0
    78c: 32d000ef  jal          x1, 0x000012b8  # target 0x000012b8; x1 = 0x00000790
    790: 000a8513  addi         x10, x21, 0
    794: 000b0593  addi         x11, x22, 0
    798: 00650633  add          x12, x10, x6
    79c: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    7a0: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x000258c0
    7a4: 00060f13  addi         x30, x12, 0
    7a8: 00058e93  addi         x29, x11, 0
    7ac: 255000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000007b0
    7b0: 00650633  add          x12, x10, x6
    7b4: 20060613  addi         x12, x12, 512
    7b8: 00026fb7  lui          x31, 0x00026  # x31 = 0x00026000
    7bc: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x000258e0
    7c0: 00060f13  addi         x30, x12, 0
    7c4: 00058e93  addi         x29, x11, 0
    7c8: 239000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000007cc
    7cc: 1b1000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x000007d0
    7d0: 1c9000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x000007d4
loc_7d4:
    7d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7d8: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    7dc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    7e0: 00600393  addi         x7, x0, 6  # x7 = 0x00000006
loc_7e4:
    7e4: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    7e8: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    7ec: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    7f0: 40428333  sub          x6, x5, x4
    7f4: 01031313  slli         x6, x6, 16
    7f8: 01035313  srli         x6, x6, 16
    7fc: 00737663  bgeu         x6, x7, 0x00000808  # target 0x00000808
    800: 0ff0000f  fence        0xf, 0xf
    804: fe1ff06f  jal          x0, 0x000007e4  # target 0x000007e4
loc_808:
    808: 0ff0000f  fence        0xf, 0xf
    80c: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    810: 90438393  addi         x7, x7, -1788  # x7 = 0x00011904
    814: 0003a203  lw           x4, 0(x7)  # param attention_phase; 0x00011904
    818: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    81c: 90838393  addi         x7, x7, -1784  # x7 = 0x00011908
    820: 0003a283  lw           x5, 0(x7)  # param attention_merger; 0x00011908
    824: 00006337  lui          x6, 0x00006  # x6 = 0x00006000
    828: 02430333  mul          x6, x6, x4
    82c: 000263b7  lui          x7, 0x00026  # x7 = 0x00026000
    830: 90038393  addi         x7, x7, -1792  # x7 = 0x00025900
    834: 00730333  add          x6, x6, x7
    838: 145000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x0000083c
    83c: 15d000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x00000840
    840: 0a021863  bne          x4, x0, 0x000008f0  # target 0x000008f0
    844: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    848: 006383b3  add          x7, x7, x6
    84c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    850: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001c800
    854: 00038f13  addi         x30, x7, 0
    858: 00028e93  addi         x29, x5, 0
    85c: 2a9000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x00000860
    860: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    864: 006383b3  add          x7, x7, x6
    868: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    86c: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001d800
    870: 00038f13  addi         x30, x7, 0
    874: 00028e93  addi         x29, x5, 0
    878: 28d000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x0000087c
    87c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    880: 006383b3  add          x7, x7, x6
    884: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    888: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001e800
    88c: 00038f13  addi         x30, x7, 0
    890: 00028e93  addi         x29, x5, 0
    894: 271000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x00000898
    898: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    89c: 006383b3  add          x7, x7, x6
    8a0: 00020fb7  lui          x31, 0x00020  # x31 = 0x00020000
    8a4: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001f800
    8a8: 00038f13  addi         x30, x7, 0
    8ac: 00028e93  addi         x29, x5, 0
    8b0: 255000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x000008b4
    8b4: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    8b8: 006383b3  add          x7, x7, x6
    8bc: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    8c0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00020800
    8c4: 00038f13  addi         x30, x7, 0
    8c8: 00028e93  addi         x29, x5, 0
    8cc: 239000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x000008d0
    8d0: 000053b7  lui          x7, 0x00005  # x7 = 0x00005000
    8d4: 006383b3  add          x7, x7, x6
    8d8: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    8dc: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00021800
    8e0: 00038f13  addi         x30, x7, 0
    8e4: 00028e93  addi         x29, x5, 0
    8e8: 21d000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x000008ec
    8ec: 0ac0006f  jal          x0, 0x00000998  # target 0x00000998
loc_8f0:
    8f0: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    8f4: 006383b3  add          x7, x7, x6
    8f8: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    8fc: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001c800
    900: 00038f13  addi         x30, x7, 0
    904: 00028e93  addi         x29, x5, 0
    908: 1fd000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x0000090c
    90c: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    910: 006383b3  add          x7, x7, x6
    914: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    918: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001d800
    91c: 00038f13  addi         x30, x7, 0
    920: 00028e93  addi         x29, x5, 0
    924: 1e1000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x00000928
    928: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    92c: 006383b3  add          x7, x7, x6
    930: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    934: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001e800
    938: 00038f13  addi         x30, x7, 0
    93c: 00028e93  addi         x29, x5, 0
    940: 1c5000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x00000944
    944: 000053b7  lui          x7, 0x00005  # x7 = 0x00005000
    948: 006383b3  add          x7, x7, x6
    94c: 00020fb7  lui          x31, 0x00020  # x31 = 0x00020000
    950: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001f800
    954: 00038f13  addi         x30, x7, 0
    958: 00028e93  addi         x29, x5, 0
    95c: 1a9000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x00000960
    960: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    964: 006383b3  add          x7, x7, x6
    968: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    96c: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00020800
    970: 00038f13  addi         x30, x7, 0
    974: 00028e93  addi         x29, x5, 0
    978: 18d000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x0000097c
    97c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    980: 006383b3  add          x7, x7, x6
    984: 00022fb7  lui          x31, 0x00022  # x31 = 0x00022000
    988: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00021800
    98c: 00038f13  addi         x30, x7, 0
    990: 00028e93  addi         x29, x5, 0
    994: 171000ef  jal          x1, 0x00001304  # target 0x00001304; x1 = 0x00000998
loc_998:
    998: 7e4000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x0000099c
    99c: 7fc000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x000009a0
    9a0: 7dc000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x000009a4
    9a4: 7f4000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x000009a8
    9a8: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    9ac: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00011fc0
    9b0: 00028f13  addi         x30, x5, 0
loc_9b4:
    9b4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9b8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    9bc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    9c0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    9c4: 015a6463  bltu         x20, x21, 0x000009cc  # target 0x000009cc
    9c8: fedff06f  jal          x0, 0x000009b4  # target 0x000009b4
loc_9cc:
    9cc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    9d0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    9d4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    9d8: 014a1a13  slli         x20, x20, 20
    9dc: 014a5a13  srli         x20, x20, 20
    9e0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_9e4:
    9e4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    9e8: 000b0463  beq          x22, x0, 0x000009f0  # target 0x000009f0
    9ec: ff9ff06f  jal          x0, 0x000009e4  # target 0x000009e4
loc_9f0:
    9f0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    9f4: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write 0x00011fc0
    9f8: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    9fc: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    a00: 00058c37  lui          x24, 0x00058  # x24 = 0x00058000 · arc_apb_niu1 + 0x0
    a04: 900c0c13  addi         x24, x24, -1792  # x24 = 0x00057900
    a08: 018ba623  sw           x24, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write 0x00057900
    a0c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    a10: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    a14: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    a18: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    a1c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    a20: 091c0c13  addi         x24, x24, 145  # x24 = 0x00002091
    a24: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002091
    a28: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a2c: 07cc0c13  addi         x24, x24, 124  # x24 = 0x0000107c
    a30: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x0000107c
    a34: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    a38: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    a3c: 038ba423  sw           x24, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000001
    a40: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    a44: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    a48: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    a4c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    a50: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_a54:
    a54: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    a58: 000b0463  beq          x22, x0, 0x00000a60  # target 0x00000a60
    a5c: ff9ff06f  jal          x0, 0x00000a54  # target 0x00000a54
loc_a60:
    a60: 738000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x00000a64
    a64: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    a68: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    a6c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    a70: 00620213  addi         x4, x4, 6
    a74: 01021213  slli         x4, x4, 16
    a78: 01025213  srli         x4, x4, 16
    a7c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    a80: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    a84: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    a88: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    a8c: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    a90: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    a94: 0ff0000f  fence        0xf, 0xf
    a98: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    a9c: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    aa0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    aa4: 000062b7  lui          x5, 0x00006  # x5 = 0x00006000
    aa8: 00520233  add          x4, x4, x5
    aac: 00023337  lui          x6, 0x00023  # x6 = 0x00023000
    ab0: 80030313  addi         x6, x6, -2048  # x6 = 0x00022800
    ab4: 00626663  bltu         x4, x6, 0x00000ac0  # target 0x00000ac0
    ab8: 000063b7  lui          x7, 0x00006  # x7 = 0x00006000
    abc: 40720233  sub          x4, x4, x7
loc_ac0:
    ac0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    ac4: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    ac8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    acc: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    ad0: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    ad4: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    ad8: 64021663  bne          x4, x0, 0x00001124  # target 0x00001124
    adc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    ae0: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    ae4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    ae8: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_aec:
    aec: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    af0: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    af4: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    af8: 40428333  sub          x6, x5, x4
    afc: 01031313  slli         x6, x6, 16
    b00: 01035313  srli         x6, x6, 16
    b04: 00737663  bgeu         x6, x7, 0x00000b10  # target 0x00000b10
    b08: 0ff0000f  fence        0xf, 0xf
    b0c: fe1ff06f  jal          x0, 0x00000aec  # target 0x00000aec
loc_b10:
    b10: 0ff0000f  fence        0xf, 0xf
    b14: 668000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x00000b18
    b18: 680000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x00000b1c
    b1c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b20: 90028293  addi         x5, x5, -1792  # x5 = 0x00011900
    b24: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x00011900
    b28: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    b2c: 02525233  divu         x4, x4, x5
    b30: 00921213  slli         x4, x4, 9
    b34: 00020293  addi         x5, x4, 0
    b38: 00a2d313  srli         x6, x5, 10
    b3c: 00030f93  addi         x31, x6, 0
    b40: 07d000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000b44
    b44: 000a8393  addi         x7, x21, 0
    b48: 000b0413  addi         x8, x22, 0
    b4c: 3ff2f293  andi         x5, x5, 1023
    b50: 00129493  slli         x9, x5, 1
    b54: 007484b3  add          x9, x9, x7
    b58: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    b5c: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00055900
    b60: 00048f13  addi         x30, x9, 0
    b64: 00040e93  addi         x29, x8, 0
    b68: 698000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000b6c
    b6c: 01028293  addi         x5, x5, 16
    b70: 00129493  slli         x9, x5, 1
    b74: 007484b3  add          x9, x9, x7
    b78: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    b7c: b00f8f93  addi         x31, x31, -1280  # x31 = 0x00055b00
    b80: 00048f13  addi         x30, x9, 0
    b84: 00040e93  addi         x29, x8, 0
    b88: 678000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000b8c
    b8c: 02020293  addi         x5, x4, 32
    b90: 00a2d313  srli         x6, x5, 10
    b94: 00030f93  addi         x31, x6, 0
    b98: 025000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000b9c
    b9c: 000a8393  addi         x7, x21, 0
    ba0: 000b0413  addi         x8, x22, 0
    ba4: 3ff2f293  andi         x5, x5, 1023
    ba8: 00129493  slli         x9, x5, 1
    bac: 007484b3  add          x9, x9, x7
    bb0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    bb4: 100f8f93  addi         x31, x31, 256  # x31 = 0x00056100
    bb8: 00048f13  addi         x30, x9, 0
    bbc: 00040e93  addi         x29, x8, 0
    bc0: 640000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000bc4
    bc4: 01028293  addi         x5, x5, 16
    bc8: 00129493  slli         x9, x5, 1
    bcc: 007484b3  add          x9, x9, x7
    bd0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    bd4: 300f8f93  addi         x31, x31, 768  # x31 = 0x00056300
    bd8: 00048f13  addi         x30, x9, 0
    bdc: 00040e93  addi         x29, x8, 0
    be0: 620000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000be4
    be4: 04020293  addi         x5, x4, 64
    be8: 00a2d313  srli         x6, x5, 10
    bec: 00030f93  addi         x31, x6, 0
    bf0: 7cc000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000bf4
    bf4: 000a8393  addi         x7, x21, 0
    bf8: 000b0413  addi         x8, x22, 0
    bfc: 3ff2f293  andi         x5, x5, 1023
    c00: 00129493  slli         x9, x5, 1
    c04: 007484b3  add          x9, x9, x7
    c08: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c0c: 900f8f93  addi         x31, x31, -1792  # x31 = 0x00056900
    c10: 00048f13  addi         x30, x9, 0
    c14: 00040e93  addi         x29, x8, 0
    c18: 5e8000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000c1c
    c1c: 01028293  addi         x5, x5, 16
    c20: 00129493  slli         x9, x5, 1
    c24: 007484b3  add          x9, x9, x7
    c28: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c2c: b00f8f93  addi         x31, x31, -1280  # x31 = 0x00056b00
    c30: 00048f13  addi         x30, x9, 0
    c34: 00040e93  addi         x29, x8, 0
    c38: 5c8000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000c3c
    c3c: 06020293  addi         x5, x4, 96
    c40: 00a2d313  srli         x6, x5, 10
    c44: 00030f93  addi         x31, x6, 0
    c48: 774000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000c4c
    c4c: 000a8393  addi         x7, x21, 0
    c50: 000b0413  addi         x8, x22, 0
    c54: 3ff2f293  andi         x5, x5, 1023
    c58: 00129493  slli         x9, x5, 1
    c5c: 007484b3  add          x9, x9, x7
    c60: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c64: 100f8f93  addi         x31, x31, 256  # x31 = 0x00057100
    c68: 00048f13  addi         x30, x9, 0
    c6c: 00040e93  addi         x29, x8, 0
    c70: 590000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000c74
    c74: 01028293  addi         x5, x5, 16
    c78: 00129493  slli         x9, x5, 1
    c7c: 007484b3  add          x9, x9, x7
    c80: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    c84: 300f8f93  addi         x31, x31, 768  # x31 = 0x00057300
    c88: 00048f13  addi         x30, x9, 0
    c8c: 00040e93  addi         x29, x8, 0
    c90: 570000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000c94
    c94: 08020293  addi         x5, x4, 128
    c98: 00a2d313  srli         x6, x5, 10
    c9c: 00030f93  addi         x31, x6, 0
    ca0: 71c000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000ca4
    ca4: 000a8393  addi         x7, x21, 0
    ca8: 000b0413  addi         x8, x22, 0
    cac: 3ff2f293  andi         x5, x5, 1023
    cb0: 00129493  slli         x9, x5, 1
    cb4: 007484b3  add          x9, x9, x7
    cb8: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    cbc: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00055920
    cc0: 00048f13  addi         x30, x9, 0
    cc4: 00040e93  addi         x29, x8, 0
    cc8: 538000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000ccc
    ccc: 01028293  addi         x5, x5, 16
    cd0: 00129493  slli         x9, x5, 1
    cd4: 007484b3  add          x9, x9, x7
    cd8: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    cdc: b20f8f93  addi         x31, x31, -1248  # x31 = 0x00055b20
    ce0: 00048f13  addi         x30, x9, 0
    ce4: 00040e93  addi         x29, x8, 0
    ce8: 518000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000cec
    cec: 0a020293  addi         x5, x4, 160
    cf0: 00a2d313  srli         x6, x5, 10
    cf4: 00030f93  addi         x31, x6, 0
    cf8: 6c4000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000cfc
    cfc: 000a8393  addi         x7, x21, 0
    d00: 000b0413  addi         x8, x22, 0
    d04: 3ff2f293  andi         x5, x5, 1023
    d08: 00129493  slli         x9, x5, 1
    d0c: 007484b3  add          x9, x9, x7
    d10: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    d14: 120f8f93  addi         x31, x31, 288  # x31 = 0x00056120
    d18: 00048f13  addi         x30, x9, 0
    d1c: 00040e93  addi         x29, x8, 0
    d20: 4e0000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000d24
    d24: 01028293  addi         x5, x5, 16
    d28: 00129493  slli         x9, x5, 1
    d2c: 007484b3  add          x9, x9, x7
    d30: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    d34: 320f8f93  addi         x31, x31, 800  # x31 = 0x00056320
    d38: 00048f13  addi         x30, x9, 0
    d3c: 00040e93  addi         x29, x8, 0
    d40: 4c0000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000d44
    d44: 0c020293  addi         x5, x4, 192
    d48: 00a2d313  srli         x6, x5, 10
    d4c: 00030f93  addi         x31, x6, 0
    d50: 66c000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000d54
    d54: 000a8393  addi         x7, x21, 0
    d58: 000b0413  addi         x8, x22, 0
    d5c: 3ff2f293  andi         x5, x5, 1023
    d60: 00129493  slli         x9, x5, 1
    d64: 007484b3  add          x9, x9, x7
    d68: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    d6c: 920f8f93  addi         x31, x31, -1760  # x31 = 0x00056920
    d70: 00048f13  addi         x30, x9, 0
    d74: 00040e93  addi         x29, x8, 0
    d78: 488000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000d7c
    d7c: 01028293  addi         x5, x5, 16
    d80: 00129493  slli         x9, x5, 1
    d84: 007484b3  add          x9, x9, x7
    d88: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    d8c: b20f8f93  addi         x31, x31, -1248  # x31 = 0x00056b20
    d90: 00048f13  addi         x30, x9, 0
    d94: 00040e93  addi         x29, x8, 0
    d98: 468000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000d9c
    d9c: 0e020293  addi         x5, x4, 224
    da0: 00a2d313  srli         x6, x5, 10
    da4: 00030f93  addi         x31, x6, 0
    da8: 614000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000dac
    dac: 000a8393  addi         x7, x21, 0
    db0: 000b0413  addi         x8, x22, 0
    db4: 3ff2f293  andi         x5, x5, 1023
    db8: 00129493  slli         x9, x5, 1
    dbc: 007484b3  add          x9, x9, x7
    dc0: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    dc4: 120f8f93  addi         x31, x31, 288  # x31 = 0x00057120
    dc8: 00048f13  addi         x30, x9, 0
    dcc: 00040e93  addi         x29, x8, 0
    dd0: 430000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000dd4
    dd4: 01028293  addi         x5, x5, 16
    dd8: 00129493  slli         x9, x5, 1
    ddc: 007484b3  add          x9, x9, x7
    de0: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    de4: 320f8f93  addi         x31, x31, 800  # x31 = 0x00057320
    de8: 00048f13  addi         x30, x9, 0
    dec: 00040e93  addi         x29, x8, 0
    df0: 410000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000df4
    df4: 10020293  addi         x5, x4, 256
    df8: 00a2d313  srli         x6, x5, 10
    dfc: 00030f93  addi         x31, x6, 0
    e00: 5bc000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000e04
    e04: 000a8393  addi         x7, x21, 0
    e08: 000b0413  addi         x8, x22, 0
    e0c: 3ff2f293  andi         x5, x5, 1023
    e10: 00129493  slli         x9, x5, 1
    e14: 007484b3  add          x9, x9, x7
    e18: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e1c: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00055940
    e20: 00048f13  addi         x30, x9, 0
    e24: 00040e93  addi         x29, x8, 0
    e28: 3d8000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000e2c
    e2c: 01028293  addi         x5, x5, 16
    e30: 00129493  slli         x9, x5, 1
    e34: 007484b3  add          x9, x9, x7
    e38: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e3c: b40f8f93  addi         x31, x31, -1216  # x31 = 0x00055b40
    e40: 00048f13  addi         x30, x9, 0
    e44: 00040e93  addi         x29, x8, 0
    e48: 3b8000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000e4c
    e4c: 12020293  addi         x5, x4, 288
    e50: 00a2d313  srli         x6, x5, 10
    e54: 00030f93  addi         x31, x6, 0
    e58: 564000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000e5c
    e5c: 000a8393  addi         x7, x21, 0
    e60: 000b0413  addi         x8, x22, 0
    e64: 3ff2f293  andi         x5, x5, 1023
    e68: 00129493  slli         x9, x5, 1
    e6c: 007484b3  add          x9, x9, x7
    e70: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e74: 140f8f93  addi         x31, x31, 320  # x31 = 0x00056140
    e78: 00048f13  addi         x30, x9, 0
    e7c: 00040e93  addi         x29, x8, 0
    e80: 380000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000e84
    e84: 01028293  addi         x5, x5, 16
    e88: 00129493  slli         x9, x5, 1
    e8c: 007484b3  add          x9, x9, x7
    e90: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    e94: 340f8f93  addi         x31, x31, 832  # x31 = 0x00056340
    e98: 00048f13  addi         x30, x9, 0
    e9c: 00040e93  addi         x29, x8, 0
    ea0: 360000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000ea4
    ea4: 14020293  addi         x5, x4, 320
    ea8: 00a2d313  srli         x6, x5, 10
    eac: 00030f93  addi         x31, x6, 0
    eb0: 50c000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000eb4
    eb4: 000a8393  addi         x7, x21, 0
    eb8: 000b0413  addi         x8, x22, 0
    ebc: 3ff2f293  andi         x5, x5, 1023
    ec0: 00129493  slli         x9, x5, 1
    ec4: 007484b3  add          x9, x9, x7
    ec8: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    ecc: 940f8f93  addi         x31, x31, -1728  # x31 = 0x00056940
    ed0: 00048f13  addi         x30, x9, 0
    ed4: 00040e93  addi         x29, x8, 0
    ed8: 328000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000edc
    edc: 01028293  addi         x5, x5, 16
    ee0: 00129493  slli         x9, x5, 1
    ee4: 007484b3  add          x9, x9, x7
    ee8: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    eec: b40f8f93  addi         x31, x31, -1216  # x31 = 0x00056b40
    ef0: 00048f13  addi         x30, x9, 0
    ef4: 00040e93  addi         x29, x8, 0
    ef8: 308000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000efc
    efc: 16020293  addi         x5, x4, 352
    f00: 00a2d313  srli         x6, x5, 10
    f04: 00030f93  addi         x31, x6, 0
    f08: 4b4000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000f0c
    f0c: 000a8393  addi         x7, x21, 0
    f10: 000b0413  addi         x8, x22, 0
    f14: 3ff2f293  andi         x5, x5, 1023
    f18: 00129493  slli         x9, x5, 1
    f1c: 007484b3  add          x9, x9, x7
    f20: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    f24: 140f8f93  addi         x31, x31, 320  # x31 = 0x00057140
    f28: 00048f13  addi         x30, x9, 0
    f2c: 00040e93  addi         x29, x8, 0
    f30: 2d0000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000f34
    f34: 01028293  addi         x5, x5, 16
    f38: 00129493  slli         x9, x5, 1
    f3c: 007484b3  add          x9, x9, x7
    f40: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
    f44: 340f8f93  addi         x31, x31, 832  # x31 = 0x00057340
    f48: 00048f13  addi         x30, x9, 0
    f4c: 00040e93  addi         x29, x8, 0
    f50: 2b0000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000f54
    f54: 18020293  addi         x5, x4, 384
    f58: 00a2d313  srli         x6, x5, 10
    f5c: 00030f93  addi         x31, x6, 0
    f60: 45c000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000f64
    f64: 000a8393  addi         x7, x21, 0
    f68: 000b0413  addi         x8, x22, 0
    f6c: 3ff2f293  andi         x5, x5, 1023
    f70: 00129493  slli         x9, x5, 1
    f74: 007484b3  add          x9, x9, x7
    f78: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    f7c: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00055960
    f80: 00048f13  addi         x30, x9, 0
    f84: 00040e93  addi         x29, x8, 0
    f88: 278000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000f8c
    f8c: 01028293  addi         x5, x5, 16
    f90: 00129493  slli         x9, x5, 1
    f94: 007484b3  add          x9, x9, x7
    f98: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    f9c: b60f8f93  addi         x31, x31, -1184  # x31 = 0x00055b60
    fa0: 00048f13  addi         x30, x9, 0
    fa4: 00040e93  addi         x29, x8, 0
    fa8: 258000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000fac
    fac: 1a020293  addi         x5, x4, 416
    fb0: 00a2d313  srli         x6, x5, 10
    fb4: 00030f93  addi         x31, x6, 0
    fb8: 404000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00000fbc
    fbc: 000a8393  addi         x7, x21, 0
    fc0: 000b0413  addi         x8, x22, 0
    fc4: 3ff2f293  andi         x5, x5, 1023
    fc8: 00129493  slli         x9, x5, 1
    fcc: 007484b3  add          x9, x9, x7
    fd0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    fd4: 160f8f93  addi         x31, x31, 352  # x31 = 0x00056160
    fd8: 00048f13  addi         x30, x9, 0
    fdc: 00040e93  addi         x29, x8, 0
    fe0: 220000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00000fe4
    fe4: 01028293  addi         x5, x5, 16
    fe8: 00129493  slli         x9, x5, 1
    fec: 007484b3  add          x9, x9, x7
    ff0: 00056fb7  lui          x31, 0x00056  # x31 = 0x00056000
    ff4: 360f8f93  addi         x31, x31, 864  # x31 = 0x00056360
    ff8: 00048f13  addi         x30, x9, 0
    ffc: 00040e93  addi         x29, x8, 0
   1000: 200000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00001004
   1004: 1c020293  addi         x5, x4, 448
   1008: 00a2d313  srli         x6, x5, 10
   100c: 00030f93  addi         x31, x6, 0
   1010: 3ac000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x00001014
   1014: 000a8393  addi         x7, x21, 0
   1018: 000b0413  addi         x8, x22, 0
   101c: 3ff2f293  andi         x5, x5, 1023
   1020: 00129493  slli         x9, x5, 1
   1024: 007484b3  add          x9, x9, x7
   1028: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   102c: 960f8f93  addi         x31, x31, -1696  # x31 = 0x00056960
   1030: 00048f13  addi         x30, x9, 0
   1034: 00040e93  addi         x29, x8, 0
   1038: 1c8000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x0000103c
   103c: 01028293  addi         x5, x5, 16
   1040: 00129493  slli         x9, x5, 1
   1044: 007484b3  add          x9, x9, x7
   1048: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   104c: b60f8f93  addi         x31, x31, -1184  # x31 = 0x00056b60
   1050: 00048f13  addi         x30, x9, 0
   1054: 00040e93  addi         x29, x8, 0
   1058: 1a8000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x0000105c
   105c: 1e020293  addi         x5, x4, 480
   1060: 00a2d313  srli         x6, x5, 10
   1064: 00030f93  addi         x31, x6, 0
   1068: 354000ef  jal          x1, 0x000013bc  # target 0x000013bc; x1 = 0x0000106c
   106c: 000a8393  addi         x7, x21, 0
   1070: 000b0413  addi         x8, x22, 0
   1074: 3ff2f293  andi         x5, x5, 1023
   1078: 00129493  slli         x9, x5, 1
   107c: 007484b3  add          x9, x9, x7
   1080: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   1084: 160f8f93  addi         x31, x31, 352  # x31 = 0x00057160
   1088: 00048f13  addi         x30, x9, 0
   108c: 00040e93  addi         x29, x8, 0
   1090: 170000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x00001094
   1094: 01028293  addi         x5, x5, 16
   1098: 00129493  slli         x9, x5, 1
   109c: 007484b3  add          x9, x9, x7
   10a0: 00057fb7  lui          x31, 0x00057  # x31 = 0x00057000
   10a4: 360f8f93  addi         x31, x31, 864  # x31 = 0x00057360
   10a8: 00048f13  addi         x30, x9, 0
   10ac: 00040e93  addi         x29, x8, 0
   10b0: 150000ef  jal          x1, 0x00001200  # target 0x00001200; x1 = 0x000010b4
   10b4: 0c8000ef  jal          x1, 0x0000117c  # target 0x0000117c; x1 = 0x000010b8
   10b8: 0e0000ef  jal          x1, 0x00001198  # target 0x00001198; x1 = 0x000010bc
   10bc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
   10c0: 88828293  addi         x5, x5, -1912  # x5 = 0xffb00888 · riscv_local_mem + 0x888
   10c4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x888 · 0xffb00888
   10c8: 00420213  addi         x4, x4, 4
   10cc: 01021213  slli         x4, x4, 16
   10d0: 01025213  srli         x4, x4, 16
   10d4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
   10d8: 88828293  addi         x5, x5, -1912  # x5 = 0xffb00888 · riscv_local_mem + 0x888
   10dc: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
   10e0: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
   10e4: 02028293  addi         x5, x5, 32  # x5 = 0xffb51020
   10e8: 0042a023  sw           x4, 0(x5)  # 0xffb51020; write runtime value
   10ec: 0ff0000f  fence        0xf, 0xf
   10f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
   10f4: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
   10f8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
   10fc: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
   1100: 00520233  add          x4, x4, x5
   1104: 00058337  lui          x6, 0x00058  # x6 = 0x00058000 · arc_apb_niu1 + 0x0
   1108: 90030313  addi         x6, x6, -1792  # x6 = 0x00057900
   110c: 00626663  bltu         x4, x6, 0x00001118  # target 0x00001118
   1110: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
   1114: 40720233  sub          x4, x4, x7
loc_1118:
   1118: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
   111c: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
   1120: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
loc_1124:
   1124: 2e40006f  jal          x0, 0x00001408  # target 0x00001408
loc_1128:
   1128: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
   112c: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
   1130: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
   1134: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
   1138: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
   113c: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
   1140: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
   1144: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
   1148: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
   114c: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
   1150: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
   1154: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
   1158: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
   115c: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
   1160: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
   1164: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
   1168: 020f8f93  addi         x31, x31, 32
   116c: 020f0f13  addi         x30, x30, 32
   1170: ff8e8e93  addi         x29, x29, -8
   1174: fa0e9ae3  bne          x29, x0, 0x00001128  # target 0x00001128
   1178: 00008067  jalr         x0, 0(x1)
loc_117c:
   117c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1180: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
   1184: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
   1188: 000a0463  beq          x20, x0, 0x00001190  # target 0x00001190
   118c: ff1ff06f  jal          x0, 0x0000117c  # target 0x0000117c
loc_1190:
   1190: 0ff0000f  fence        0xf, 0xf
   1194: 00008067  jalr         x0, 0(x1)
loc_1198:
   1198: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   119c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
   11a0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
   11a4: 000a0463  beq          x20, x0, 0x000011ac  # target 0x000011ac
   11a8: ff1ff06f  jal          x0, 0x00001198  # target 0x00001198
loc_11ac:
   11ac: 0ff0000f  fence        0xf, 0xf
   11b0: 00008067  jalr         x0, 0(x1)
loc_11b4:
   11b4: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
   11b8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
   11bc: 007a7d13  andi         x26, x20, 7
   11c0: ff8a7a13  andi         x20, x20, -8
   11c4: 01af8ab3  add          x21, x31, x26
   11c8: 007afb93  andi         x23, x21, 7
   11cc: 003ada93  srli         x21, x21, 3
   11d0: 00ba9a93  slli         x21, x21, 11
   11d4: 014a8ab3  add          x21, x21, x20
   11d8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000011d8
   11dc: 018b0b13  addi         x22, x22, 24  # x22 = 0x000011f0
   11e0: 001b9b93  slli         x23, x23, 1
   11e4: 017b0b33  add          x22, x22, x23
   11e8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   11ec: 00008067  jalr         x0, 0(x1)
   11f0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   11f4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   11f8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   11fc: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_1200:
   1200: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1204: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
   1208: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
   120c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   1210: 015a6463  bltu         x20, x21, 0x00001218  # target 0x00001218
   1214: fedff06f  jal          x0, 0x00001200  # target 0x00001200
loc_1218:
   1218: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   121c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
   1220: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
   1224: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   1228: 015a6463  bltu         x20, x21, 0x00001230  # target 0x00001230
   122c: fedff06f  jal          x0, 0x00001218  # target 0x00001218
loc_1230:
   1230: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1234: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
   1238: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
   123c: 014a1a13  slli         x20, x20, 20
   1240: 014a5a13  srli         x20, x20, 20
   1244: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_1248:
   1248: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   124c: 000b0463  beq          x22, x0, 0x00001254  # target 0x00001254
   1250: ff9ff06f  jal          x0, 0x00001248  # target 0x00001248
loc_1254:
   1254: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   1258: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
   125c: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
   1260: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
   1264: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
   1268: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
   126c: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
   1270: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
   1274: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
   1278: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
   127c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
   1280: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
   1284: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
   1288: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
   128c: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
   1290: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
   1294: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
   1298: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   129c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
   12a0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
   12a4: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_12a8:
   12a8: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   12ac: 000b0463  beq          x22, x0, 0x000012b4  # target 0x000012b4
   12b0: ff9ff06f  jal          x0, 0x000012a8  # target 0x000012a8
loc_12b4:
   12b4: 00008067  jalr         x0, 0(x1)
loc_12b8:
   12b8: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   12bc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   12c0: 007a7d13  andi         x26, x20, 7
   12c4: ff8a7a13  andi         x20, x20, -8
   12c8: 01af8ab3  add          x21, x31, x26
   12cc: 007afb93  andi         x23, x21, 7
   12d0: 003ada93  srli         x21, x21, 3
   12d4: 00ba9a93  slli         x21, x21, 11
   12d8: 014a8ab3  add          x21, x21, x20
   12dc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000012dc
   12e0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000012f4
   12e4: 001b9b93  slli         x23, x23, 1
   12e8: 017b0b33  add          x22, x22, x23
   12ec: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   12f0: 00008067  jalr         x0, 0(x1)
   12f4: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   12f8: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   12fc: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   1300: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_1304:
   1304: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1308: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
   130c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
   1310: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   1314: 015a6463  bltu         x20, x21, 0x0000131c  # target 0x0000131c
   1318: fedff06f  jal          x0, 0x00001304  # target 0x00001304
loc_131c:
   131c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1320: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
   1324: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
   1328: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
   132c: 015a6463  bltu         x20, x21, 0x00001334  # target 0x00001334
   1330: fedff06f  jal          x0, 0x0000131c  # target 0x0000131c
loc_1334:
   1334: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
   1338: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
   133c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
   1340: 014a1a13  slli         x20, x20, 20
   1344: 014a5a13  srli         x20, x20, 20
   1348: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_134c:
   134c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   1350: 000b0463  beq          x22, x0, 0x00001358  # target 0x00001358
   1354: ff9ff06f  jal          x0, 0x0000134c  # target 0x0000134c
loc_1358:
   1358: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   135c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
   1360: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
   1364: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
   1368: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
   136c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
   1370: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
   1374: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
   1378: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
   137c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
   1380: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
   1384: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
   1388: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
   138c: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00001000
   1390: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
   1394: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
   1398: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
   139c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
   13a0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
   13a4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
   13a8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_13ac:
   13ac: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
   13b0: 000b0463  beq          x22, x0, 0x000013b8  # target 0x000013b8
   13b4: ff9ff06f  jal          x0, 0x000013ac  # target 0x000013ac
loc_13b8:
   13b8: 00008067  jalr         x0, 0(x1)
loc_13bc:
   13bc: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
   13c0: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x0000078c
   13c4: 007a7d13  andi         x26, x20, 7
   13c8: ff8a7a13  andi         x20, x20, -8
   13cc: 01af8ab3  add          x21, x31, x26
   13d0: 007afb93  andi         x23, x21, 7
   13d4: 003ada93  srli         x21, x21, 3
   13d8: 00ba9a93  slli         x21, x21, 11
   13dc: 014a8ab3  add          x21, x21, x20
   13e0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000013e0
   13e4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000013f8
   13e8: 001b9b93  slli         x23, x23, 1
   13ec: 017b0b33  add          x22, x22, x23
   13f0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   13f4: 00008067  jalr         x0, 0(x1)
   13f8: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   13fc: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1400: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   1404: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
   1408:           j FW_NCRISC+4   # return to firmware, linked at install
