# llama3 1b decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 0001e2b7  lui          x5, 0x0001e  # x5 = 0x0001e000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x0001d800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x0001d800
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
     44: 0001e2b7  lui          x5, 0x0001e  # x5 = 0x0001e000
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x0001e000
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     5c: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     60: 000182b7  lui          x5, 0x00018  # x5 = 0x00018000
     64: 80028293  addi         x5, x5, -2048  # x5 = 0x00017800
     68: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00017800
     6c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     70: 88020213  addi         x4, x4, -1920  # x4 = 0xffb00880 · riscv_local_mem + 0x880
     74: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00000000
     78: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     7c: 88420213  addi         x4, x4, -1916  # x4 = 0xffb00884 · riscv_local_mem + 0x884
     80: 0003f2b7  lui          x5, 0x0003f  # x5 = 0x0003f000 · arc_apb_reset_unit + 0xf000
     84: 88028293  addi         x5, x5, -1920  # x5 = 0x0003e880 · arc_apb_reset_unit + 0xe880
     88: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x0003e880
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
     c8: 285278e3  bgeu         x4, x5, 0x00000b58  # target 0x00000b58
     cc: 00012237  lui          x4, 0x00012  # x4 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     d0: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
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
    100: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    104: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
    108: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
    10c: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_110:
    110: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    114: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    118: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    11c: 40428333  sub          x6, x5, x4
    120: 01031313  slli         x6, x6, 16
    124: 01035313  srli         x6, x6, 16
    128: 00737663  bgeu         x6, x7, 0x00000134  # target 0x00000134
    12c: 0ff0000f  fence        0xf, 0xf
    130: fe1ff06f  jal          x0, 0x00000110  # target 0x00000110
loc_134:
    134: 0ff0000f  fence        0xf, 0xf
    138: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    13c: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001d800
    140: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    144: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    148: 215000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x0000014c
    14c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    150: 820f8f93  addi         x31, x31, -2016  # x31 = 0x0001d820
    154: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    158: 200f0f13  addi         x30, x30, 512  # x30 = 0x00012200
    15c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    160: 1fd000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x00000164
    164: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    168: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001d840
    16c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    170: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00012800
    174: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    178: 1e5000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x0000017c
    17c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    180: 860f8f93  addi         x31, x31, -1952  # x31 = 0x0001d860
    184: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    188: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00012a00
    18c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    190: 1cd000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x00000194
    194: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    198: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0001d880
    19c: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1a0: 020f0f13  addi         x30, x30, 32  # x30 = 0x00012020
    1a4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1a8: 1b5000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x000001ac
    1ac: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    1b0: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x0001d8a0
    1b4: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    1b8: 220f0f13  addi         x30, x30, 544  # x30 = 0x00012220
    1bc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1c0: 19d000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x000001c4
    1c4: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    1c8: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x0001d8c0
    1cc: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1d0: 820f0f13  addi         x30, x30, -2016  # x30 = 0x00012820
    1d4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1d8: 185000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x000001dc
    1dc: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    1e0: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x0001d8e0
    1e4: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    1e8: a20f0f13  addi         x30, x30, -1504  # x30 = 0x00012a20
    1ec: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    1f0: 16d000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x000001f4
    1f4: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    1f8: 900f8f93  addi         x31, x31, -1792  # x31 = 0x0001d900
    1fc: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    200: 040f0f13  addi         x30, x30, 64  # x30 = 0x00012040
    204: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    208: 155000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x0000020c
    20c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    210: 920f8f93  addi         x31, x31, -1760  # x31 = 0x0001d920
    214: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    218: 240f0f13  addi         x30, x30, 576  # x30 = 0x00012240
    21c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    220: 13d000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x00000224
    224: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    228: 940f8f93  addi         x31, x31, -1728  # x31 = 0x0001d940
    22c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    230: 840f0f13  addi         x30, x30, -1984  # x30 = 0x00012840
    234: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    238: 125000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x0000023c
    23c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    240: 960f8f93  addi         x31, x31, -1696  # x31 = 0x0001d960
    244: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    248: a40f0f13  addi         x30, x30, -1472  # x30 = 0x00012a40
    24c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    250: 10d000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x00000254
    254: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    258: 980f8f93  addi         x31, x31, -1664  # x31 = 0x0001d980
    25c: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    260: 060f0f13  addi         x30, x30, 96  # x30 = 0x00012060
    264: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    268: 0f5000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x0000026c
    26c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    270: 9a0f8f93  addi         x31, x31, -1632  # x31 = 0x0001d9a0
    274: 00012f37  lui          x30, 0x00012  # x30 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    278: 260f0f13  addi         x30, x30, 608  # x30 = 0x00012260
    27c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    280: 0dd000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x00000284
    284: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    288: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x0001d9c0
    28c: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    290: 860f0f13  addi         x30, x30, -1952  # x30 = 0x00012860
    294: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    298: 0c5000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x0000029c
    29c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    2a0: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x0001d9e0
    2a4: 00013f37  lui          x30, 0x00013  # x30 = 0x00013000
    2a8: a60f0f13  addi         x30, x30, -1440  # x30 = 0x00012a60
    2ac: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    2b0: 0ad000ef  jal          x1, 0x00000b5c  # target 0x00000b5c; x1 = 0x000002b4
    2b4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2b8: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    2bc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    2c0: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c4: 00520233  add          x4, x4, x5
    2c8: 00013337  lui          x6, 0x00013  # x6 = 0x00013000
    2cc: 00626663  bltu         x4, x6, 0x000002d8  # target 0x000002d8
    2d0: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2d4: 40720233  sub          x4, x4, x7
loc_2d8:
    2d8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    2dc: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    2e0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    2e4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2e8: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    2ec: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    2f0: 00220213  addi         x4, x4, 2
    2f4: 01021213  slli         x4, x4, 16
    2f8: 01025213  srli         x4, x4, 16
    2fc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    300: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    304: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    308: ffb482b7  lui          x5, 0xffb48  # x5 = 0xffb48000
    30c: 02828293  addi         x5, x5, 40  # x5 = 0xffb48028
    310: 0042a023  sw           x4, 0(x5)  # 0xffb48028; write runtime value
    314: 0ff0000f  fence        0xf, 0xf
    318: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    31c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    320: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    324: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    328: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    32c: 00520233  add          x4, x4, x5
    330: 0001f337  lui          x6, 0x0001f  # x6 = 0x0001f000
    334: 80030313  addi         x6, x6, -2048  # x6 = 0x0001e800
    338: 00626863  bltu         x4, x6, 0x00000348  # target 0x00000348
    33c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    340: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    344: 40720233  sub          x4, x4, x7
loc_348:
    348: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    34c: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    350: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    354: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    358: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    35c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    360: 00120213  addi         x4, x4, 1
    364: 01021213  slli         x4, x4, 16
    368: 01025213  srli         x4, x4, 16
    36c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    370: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    374: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    378: ffb4f2b7  lui          x5, 0xffb4f  # x5 = 0xffb4f000
    37c: 02828293  addi         x5, x5, 40  # x5 = 0xffb4f028
    380: 0042a023  sw           x4, 0(x5)  # 0xffb4f028; write runtime value
    384: 0ff0000f  fence        0xf, 0xf
    388: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    38c: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
    390: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
    394: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
    398: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
    39c: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
    3a0: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
    3a4: 0063fa63  bgeu         x7, x6, 0x000003b8  # target 0x000003b8
    3a8: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
    3ac: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
    3b0: 0063f463  bgeu         x7, x6, 0x000003b8  # target 0x000003b8
    3b4: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_3b8:
    3b8: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    3bc: 0003a303  lw           x6, 0(x7)  # param kv_blocks; 0x00000790
    3c0: fff30313  addi         x6, x6, -1
    3c4: 025372b3  remu         x5, x6, x5
    3c8: 16429863  bne          x5, x4, 0x00000538  # target 0x00000538
    3cc: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    3d0: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    3d4: 00525293  srli         x5, x4, 5
    3d8: 00129293  slli         x5, x5, 1
    3dc: 00012437  lui          x8, 0x00012  # x8 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    3e0: 90040413  addi         x8, x8, -1792  # x8 = 0x00011900
    3e4: 00042383  lw           x7, 0(x8)  # param attention_core; 0x00011900
    3e8: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
    3ec: 0283d3b3  divu         x7, x7, x8
    3f0: 0003d393  srli         x7, x7, 0
    3f4: 00939393  slli         x7, x7, 9
    3f8: 007282b3  add          x5, x5, x7
    3fc: 00f27313  andi         x6, x4, 15
    400: 00531313  slli         x6, x6, 5
    404: 01027393  andi         x7, x4, 16
    408: 00639393  slli         x7, x7, 6
    40c: 00730333  add          x6, x6, x7
    410: 7a0000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x00000414
    414: 7b8000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000418
    418: 00028393  addi         x7, x5, 0
    41c: 00038f93  addi         x31, x7, 0
    420: 7c8000ef  jal          x1, 0x00000be8  # target 0x00000be8; x1 = 0x00000424
    424: 000a8413  addi         x8, x21, 0
    428: 000b0493  addi         x9, x22, 0
    42c: 00640533  add          x10, x8, x6
    430: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    434: a00f8f93  addi         x31, x31, -1536  # x31 = 0x0001da00
    438: 00050f13  addi         x30, x10, 0
    43c: 00048e93  addi         x29, x9, 0
    440: 7f4000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000444
    444: 00640533  add          x10, x8, x6
    448: 20050513  addi         x10, x10, 512
    44c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    450: a20f8f93  addi         x31, x31, -1504  # x31 = 0x0001da20
    454: 00050f13  addi         x30, x10, 0
    458: 00048e93  addi         x29, x9, 0
    45c: 7d8000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000460
    460: 00038f93  addi         x31, x7, 0
    464: 089000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x00000468
    468: 000a8513  addi         x10, x21, 0
    46c: 000b0593  addi         x11, x22, 0
    470: 00650633  add          x12, x10, x6
    474: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    478: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001e800
    47c: 00060f13  addi         x30, x12, 0
    480: 00058e93  addi         x29, x11, 0
    484: 7b0000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000488
    488: 00650633  add          x12, x10, x6
    48c: 20060613  addi         x12, x12, 512
    490: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    494: 820f8f93  addi         x31, x31, -2016  # x31 = 0x0001e820
    498: 00060f13  addi         x30, x12, 0
    49c: 00058e93  addi         x29, x11, 0
    4a0: 794000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000004a4
    4a4: 00128393  addi         x7, x5, 1
    4a8: 00038f93  addi         x31, x7, 0
    4ac: 73c000ef  jal          x1, 0x00000be8  # target 0x00000be8; x1 = 0x000004b0
    4b0: 000a8413  addi         x8, x21, 0
    4b4: 000b0493  addi         x9, x22, 0
    4b8: 00640533  add          x10, x8, x6
    4bc: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    4c0: a40f8f93  addi         x31, x31, -1472  # x31 = 0x0001da40
    4c4: 00050f13  addi         x30, x10, 0
    4c8: 00048e93  addi         x29, x9, 0
    4cc: 768000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000004d0
    4d0: 00640533  add          x10, x8, x6
    4d4: 20050513  addi         x10, x10, 512
    4d8: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    4dc: a60f8f93  addi         x31, x31, -1440  # x31 = 0x0001da60
    4e0: 00050f13  addi         x30, x10, 0
    4e4: 00048e93  addi         x29, x9, 0
    4e8: 74c000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000004ec
    4ec: 00038f93  addi         x31, x7, 0
    4f0: 7fc000ef  jal          x1, 0x00000cec  # target 0x00000cec; x1 = 0x000004f4
    4f4: 000a8513  addi         x10, x21, 0
    4f8: 000b0593  addi         x11, x22, 0
    4fc: 00650633  add          x12, x10, x6
    500: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    504: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001e840
    508: 00060f13  addi         x30, x12, 0
    50c: 00058e93  addi         x29, x11, 0
    510: 724000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000514
    514: 00650633  add          x12, x10, x6
    518: 20060613  addi         x12, x12, 512
    51c: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    520: 860f8f93  addi         x31, x31, -1952  # x31 = 0x0001e860
    524: 00060f13  addi         x30, x12, 0
    528: 00058e93  addi         x29, x11, 0
    52c: 708000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000530
    530: 680000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x00000534
    534: 698000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000538
loc_538:
    538: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    53c: 88040413  addi         x8, x8, -1920  # x8 = 0xffb00880 · riscv_local_mem + 0x880
    540: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x880 · 0xffb00880
    544: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_548:
    548: ffb4c437  lui          x8, 0xffb4c  # x8 = 0xffb4c000
    54c: 02840413  addi         x8, x8, 40  # x8 = 0xffb4c028
    550: 00045283  lhu          x5, 0(x8)  # 0xffb4c028
    554: 40428333  sub          x6, x5, x4
    558: 01031313  slli         x6, x6, 16
    55c: 01035313  srli         x6, x6, 16
    560: 00737663  bgeu         x6, x7, 0x0000056c  # target 0x0000056c
    564: 0ff0000f  fence        0xf, 0xf
    568: fe1ff06f  jal          x0, 0x00000548  # target 0x00000548
loc_56c:
    56c: 0ff0000f  fence        0xf, 0xf
    570: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    574: 90438393  addi         x7, x7, -1788  # x7 = 0x00011904
    578: 0003a203  lw           x4, 0(x7)  # param attention_phase; 0x00011904
    57c: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    580: 90838393  addi         x7, x7, -1784  # x7 = 0x00011908
    584: 0003a283  lw           x5, 0(x7)  # param attention_merger; 0x00011908
    588: 00004337  lui          x6, 0x00004  # x6 = 0x00004000
    58c: 02430333  mul          x6, x6, x4
    590: 0001f3b7  lui          x7, 0x0001f  # x7 = 0x0001f000
    594: 88038393  addi         x7, x7, -1920  # x7 = 0x0001e880
    598: 00730333  add          x6, x6, x7
    59c: 614000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x000005a0
    5a0: 62c000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x000005a4
    5a4: 06021c63  bne          x4, x0, 0x0000061c  # target 0x0000061c
    5a8: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    5ac: 006383b3  add          x7, x7, x6
    5b0: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    5b4: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00017800
    5b8: 00038f13  addi         x30, x7, 0
    5bc: 00028e93  addi         x29, x5, 0
    5c0: 778000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x000005c4
    5c4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c8: 006383b3  add          x7, x7, x6
    5cc: 00019fb7  lui          x31, 0x00019  # x31 = 0x00019000
    5d0: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00018800
    5d4: 00038f13  addi         x30, x7, 0
    5d8: 00028e93  addi         x29, x5, 0
    5dc: 75c000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x000005e0
    5e0: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    5e4: 006383b3  add          x7, x7, x6
    5e8: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    5ec: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00019800
    5f0: 00038f13  addi         x30, x7, 0
    5f4: 00028e93  addi         x29, x5, 0
    5f8: 740000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x000005fc
    5fc: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    600: 006383b3  add          x7, x7, x6
    604: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    608: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001a800
    60c: 00038f13  addi         x30, x7, 0
    610: 00028e93  addi         x29, x5, 0
    614: 724000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x00000618
    618: 0740006f  jal          x0, 0x0000068c  # target 0x0000068c
loc_61c:
    61c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    620: 006383b3  add          x7, x7, x6
    624: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    628: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00017800
    62c: 00038f13  addi         x30, x7, 0
    630: 00028e93  addi         x29, x5, 0
    634: 704000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x00000638
    638: 000033b7  lui          x7, 0x00003  # x7 = 0x00003000
    63c: 006383b3  add          x7, x7, x6
    640: 00019fb7  lui          x31, 0x00019  # x31 = 0x00019000
    644: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00018800
    648: 00038f13  addi         x30, x7, 0
    64c: 00028e93  addi         x29, x5, 0
    650: 6e8000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x00000654
    654: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    658: 006383b3  add          x7, x7, x6
    65c: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    660: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00019800
    664: 00038f13  addi         x30, x7, 0
    668: 00028e93  addi         x29, x5, 0
    66c: 6cc000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x00000670
    670: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    674: 006383b3  add          x7, x7, x6
    678: 0001bfb7  lui          x31, 0x0001b  # x31 = 0x0001b000
    67c: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0001a800
    680: 00038f13  addi         x30, x7, 0
    684: 00028e93  addi         x29, x5, 0
    688: 6b0000ef  jal          x1, 0x00000d38  # target 0x00000d38; x1 = 0x0000068c
loc_68c:
    68c: 524000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x00000690
    690: 53c000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000694
    694: 51c000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x00000698
    698: 534000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x0000069c
    69c: 00012fb7  lui          x31, 0x00012  # x31 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    6a0: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00011fc0
    6a4: 00028f13  addi         x30, x5, 0
loc_6a8:
    6a8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6ac: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    6b0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    6b4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6b8: 015a6463  bltu         x20, x21, 0x000006c0  # target 0x000006c0
    6bc: fedff06f  jal          x0, 0x000006a8  # target 0x000006a8
loc_6c0:
    6c0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6c4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    6c8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    6cc: 014a1a13  slli         x20, x20, 20
    6d0: 014a5a13  srli         x20, x20, 20
    6d4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_6d8:
    6d8: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    6dc: 000b0463  beq          x22, x0, 0x000006e4  # target 0x000006e4
    6e0: ff9ff06f  jal          x0, 0x000006d8  # target 0x000006d8
loc_6e4:
    6e4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    6e8: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write 0x00011fc0
    6ec: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    6f0: 01eba423  sw           x30, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    6f4: 00040c37  lui          x24, 0x00040  # x24 = 0x00040000
    6f8: 880c0c13  addi         x24, x24, -1920  # x24 = 0x0003f880 · arc_apb_reset_unit + 0xf880
    6fc: 018ba623  sw           x24, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write 0x0003f880
    700: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    704: 014baa23  sw           x20, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    708: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    70c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    710: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    714: 091c0c13  addi         x24, x24, 145  # x24 = 0x00002091
    718: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002091
    71c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    720: 07cc0c13  addi         x24, x24, 124  # x24 = 0x0000107c
    724: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x0000107c
    728: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    72c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    730: 038ba423  sw           x24, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000001
    734: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    738: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    73c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    740: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    744: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_748:
    748: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    74c: 000b0463  beq          x22, x0, 0x00000754  # target 0x00000754
    750: ff9ff06f  jal          x0, 0x00000748  # target 0x00000748
loc_754:
    754: 478000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000758
    758: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    75c: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    760: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880
    764: 00420213  addi         x4, x4, 4
    768: 01021213  slli         x4, x4, 16
    76c: 01025213  srli         x4, x4, 16
    770: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    774: 88028293  addi         x5, x5, -1920  # x5 = 0xffb00880 · riscv_local_mem + 0x880
    778: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    77c: ffb4c2b7  lui          x5, 0xffb4c  # x5 = 0xffb4c000
    780: 02028293  addi         x5, x5, 32  # x5 = 0xffb4c020
    784: 0042a023  sw           x4, 0(x5)  # 0xffb4c020; write runtime value
    788: 0ff0000f  fence        0xf, 0xf
    78c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    790: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    794: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c
    798: 000042b7  lui          x5, 0x00004  # x5 = 0x00004000
    79c: 00520233  add          x4, x4, x5
    7a0: 0001c337  lui          x6, 0x0001c  # x6 = 0x0001c000
    7a4: 80030313  addi         x6, x6, -2048  # x6 = 0x0001b800
    7a8: 00626663  bltu         x4, x6, 0x000007b4  # target 0x000007b4
    7ac: 000043b7  lui          x7, 0x00004  # x7 = 0x00004000
    7b0: 40720233  sub          x4, x4, x7
loc_7b4:
    7b4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7b8: 87c40413  addi         x8, x8, -1924  # x8 = 0xffb0087c · riscv_local_mem + 0x87c
    7bc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    7c0: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    7c4: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    7c8: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    7cc: 38021663  bne          x4, x0, 0x00000b58  # target 0x00000b58
    7d0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    7d4: 88840413  addi         x8, x8, -1912  # x8 = 0xffb00888 · riscv_local_mem + 0x888
    7d8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x888 · 0xffb00888
    7dc: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
loc_7e0:
    7e0: ffb51437  lui          x8, 0xffb51  # x8 = 0xffb51000
    7e4: 02840413  addi         x8, x8, 40  # x8 = 0xffb51028
    7e8: 00045283  lhu          x5, 0(x8)  # 0xffb51028
    7ec: 40428333  sub          x6, x5, x4
    7f0: 01031313  slli         x6, x6, 16
    7f4: 01035313  srli         x6, x6, 16
    7f8: 00737663  bgeu         x6, x7, 0x00000804  # target 0x00000804
    7fc: 0ff0000f  fence        0xf, 0xf
    800: fe1ff06f  jal          x0, 0x000007e0  # target 0x000007e0
loc_804:
    804: 0ff0000f  fence        0xf, 0xf
    808: 3a8000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x0000080c
    80c: 3c0000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000810
    810: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    814: 90028293  addi         x5, x5, -1792  # x5 = 0x00011900
    818: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x00011900
    81c: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
    820: 02525233  divu         x4, x4, x5
    824: 00821213  slli         x4, x4, 8
    828: 00020293  addi         x5, x4, 0
    82c: 00a2d313  srli         x6, x5, 10
    830: 00030f93  addi         x31, x6, 0
    834: 5bc000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x00000838
    838: 000a8393  addi         x7, x21, 0
    83c: 000b0413  addi         x8, x22, 0
    840: 3ff2f293  andi         x5, x5, 1023
    844: 00129493  slli         x9, x5, 1
    848: 007484b3  add          x9, x9, x7
    84c: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    850: 880f8f93  addi         x31, x31, -1920  # x31 = 0x0003e880 · arc_apb_reset_unit + 0xe880
    854: 00048f13  addi         x30, x9, 0
    858: 00040e93  addi         x29, x8, 0
    85c: 3d8000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000860
    860: 01028293  addi         x5, x5, 16
    864: 00129493  slli         x9, x5, 1
    868: 007484b3  add          x9, x9, x7
    86c: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    870: a80f8f93  addi         x31, x31, -1408  # x31 = 0x0003ea80 · arc_apb_reset_unit + 0xea80
    874: 00048f13  addi         x30, x9, 0
    878: 00040e93  addi         x29, x8, 0
    87c: 3b8000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000880
    880: 02020293  addi         x5, x4, 32
    884: 00a2d313  srli         x6, x5, 10
    888: 00030f93  addi         x31, x6, 0
    88c: 564000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x00000890
    890: 000a8393  addi         x7, x21, 0
    894: 000b0413  addi         x8, x22, 0
    898: 3ff2f293  andi         x5, x5, 1023
    89c: 00129493  slli         x9, x5, 1
    8a0: 007484b3  add          x9, x9, x7
    8a4: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    8a8: 080f8f93  addi         x31, x31, 128  # x31 = 0x0003f080 · arc_apb_reset_unit + 0xf080
    8ac: 00048f13  addi         x30, x9, 0
    8b0: 00040e93  addi         x29, x8, 0
    8b4: 380000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000008b8
    8b8: 01028293  addi         x5, x5, 16
    8bc: 00129493  slli         x9, x5, 1
    8c0: 007484b3  add          x9, x9, x7
    8c4: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    8c8: 280f8f93  addi         x31, x31, 640  # x31 = 0x0003f280 · arc_apb_reset_unit + 0xf280
    8cc: 00048f13  addi         x30, x9, 0
    8d0: 00040e93  addi         x29, x8, 0
    8d4: 360000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000008d8
    8d8: 04020293  addi         x5, x4, 64
    8dc: 00a2d313  srli         x6, x5, 10
    8e0: 00030f93  addi         x31, x6, 0
    8e4: 50c000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x000008e8
    8e8: 000a8393  addi         x7, x21, 0
    8ec: 000b0413  addi         x8, x22, 0
    8f0: 3ff2f293  andi         x5, x5, 1023
    8f4: 00129493  slli         x9, x5, 1
    8f8: 007484b3  add          x9, x9, x7
    8fc: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    900: 8a0f8f93  addi         x31, x31, -1888  # x31 = 0x0003e8a0 · arc_apb_reset_unit + 0xe8a0
    904: 00048f13  addi         x30, x9, 0
    908: 00040e93  addi         x29, x8, 0
    90c: 328000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000910
    910: 01028293  addi         x5, x5, 16
    914: 00129493  slli         x9, x5, 1
    918: 007484b3  add          x9, x9, x7
    91c: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    920: aa0f8f93  addi         x31, x31, -1376  # x31 = 0x0003eaa0 · arc_apb_reset_unit + 0xeaa0
    924: 00048f13  addi         x30, x9, 0
    928: 00040e93  addi         x29, x8, 0
    92c: 308000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000930
    930: 06020293  addi         x5, x4, 96
    934: 00a2d313  srli         x6, x5, 10
    938: 00030f93  addi         x31, x6, 0
    93c: 4b4000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x00000940
    940: 000a8393  addi         x7, x21, 0
    944: 000b0413  addi         x8, x22, 0
    948: 3ff2f293  andi         x5, x5, 1023
    94c: 00129493  slli         x9, x5, 1
    950: 007484b3  add          x9, x9, x7
    954: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    958: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x0003f0a0 · arc_apb_reset_unit + 0xf0a0
    95c: 00048f13  addi         x30, x9, 0
    960: 00040e93  addi         x29, x8, 0
    964: 2d0000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000968
    968: 01028293  addi         x5, x5, 16
    96c: 00129493  slli         x9, x5, 1
    970: 007484b3  add          x9, x9, x7
    974: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    978: 2a0f8f93  addi         x31, x31, 672  # x31 = 0x0003f2a0 · arc_apb_reset_unit + 0xf2a0
    97c: 00048f13  addi         x30, x9, 0
    980: 00040e93  addi         x29, x8, 0
    984: 2b0000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000988
    988: 08020293  addi         x5, x4, 128
    98c: 00a2d313  srli         x6, x5, 10
    990: 00030f93  addi         x31, x6, 0
    994: 45c000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x00000998
    998: 000a8393  addi         x7, x21, 0
    99c: 000b0413  addi         x8, x22, 0
    9a0: 3ff2f293  andi         x5, x5, 1023
    9a4: 00129493  slli         x9, x5, 1
    9a8: 007484b3  add          x9, x9, x7
    9ac: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    9b0: 8c0f8f93  addi         x31, x31, -1856  # x31 = 0x0003e8c0 · arc_apb_reset_unit + 0xe8c0
    9b4: 00048f13  addi         x30, x9, 0
    9b8: 00040e93  addi         x29, x8, 0
    9bc: 278000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000009c0
    9c0: 01028293  addi         x5, x5, 16
    9c4: 00129493  slli         x9, x5, 1
    9c8: 007484b3  add          x9, x9, x7
    9cc: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    9d0: ac0f8f93  addi         x31, x31, -1344  # x31 = 0x0003eac0 · arc_apb_reset_unit + 0xeac0
    9d4: 00048f13  addi         x30, x9, 0
    9d8: 00040e93  addi         x29, x8, 0
    9dc: 258000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x000009e0
    9e0: 0a020293  addi         x5, x4, 160
    9e4: 00a2d313  srli         x6, x5, 10
    9e8: 00030f93  addi         x31, x6, 0
    9ec: 404000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x000009f0
    9f0: 000a8393  addi         x7, x21, 0
    9f4: 000b0413  addi         x8, x22, 0
    9f8: 3ff2f293  andi         x5, x5, 1023
    9fc: 00129493  slli         x9, x5, 1
    a00: 007484b3  add          x9, x9, x7
    a04: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    a08: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x0003f0c0 · arc_apb_reset_unit + 0xf0c0
    a0c: 00048f13  addi         x30, x9, 0
    a10: 00040e93  addi         x29, x8, 0
    a14: 220000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000a18
    a18: 01028293  addi         x5, x5, 16
    a1c: 00129493  slli         x9, x5, 1
    a20: 007484b3  add          x9, x9, x7
    a24: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    a28: 2c0f8f93  addi         x31, x31, 704  # x31 = 0x0003f2c0 · arc_apb_reset_unit + 0xf2c0
    a2c: 00048f13  addi         x30, x9, 0
    a30: 00040e93  addi         x29, x8, 0
    a34: 200000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000a38
    a38: 0c020293  addi         x5, x4, 192
    a3c: 00a2d313  srli         x6, x5, 10
    a40: 00030f93  addi         x31, x6, 0
    a44: 3ac000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x00000a48
    a48: 000a8393  addi         x7, x21, 0
    a4c: 000b0413  addi         x8, x22, 0
    a50: 3ff2f293  andi         x5, x5, 1023
    a54: 00129493  slli         x9, x5, 1
    a58: 007484b3  add          x9, x9, x7
    a5c: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    a60: 8e0f8f93  addi         x31, x31, -1824  # x31 = 0x0003e8e0 · arc_apb_reset_unit + 0xe8e0
    a64: 00048f13  addi         x30, x9, 0
    a68: 00040e93  addi         x29, x8, 0
    a6c: 1c8000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000a70
    a70: 01028293  addi         x5, x5, 16
    a74: 00129493  slli         x9, x5, 1
    a78: 007484b3  add          x9, x9, x7
    a7c: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    a80: ae0f8f93  addi         x31, x31, -1312  # x31 = 0x0003eae0 · arc_apb_reset_unit + 0xeae0
    a84: 00048f13  addi         x30, x9, 0
    a88: 00040e93  addi         x29, x8, 0
    a8c: 1a8000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000a90
    a90: 0e020293  addi         x5, x4, 224
    a94: 00a2d313  srli         x6, x5, 10
    a98: 00030f93  addi         x31, x6, 0
    a9c: 354000ef  jal          x1, 0x00000df0  # target 0x00000df0; x1 = 0x00000aa0
    aa0: 000a8393  addi         x7, x21, 0
    aa4: 000b0413  addi         x8, x22, 0
    aa8: 3ff2f293  andi         x5, x5, 1023
    aac: 00129493  slli         x9, x5, 1
    ab0: 007484b3  add          x9, x9, x7
    ab4: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    ab8: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x0003f0e0 · arc_apb_reset_unit + 0xf0e0
    abc: 00048f13  addi         x30, x9, 0
    ac0: 00040e93  addi         x29, x8, 0
    ac4: 170000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000ac8
    ac8: 01028293  addi         x5, x5, 16
    acc: 00129493  slli         x9, x5, 1
    ad0: 007484b3  add          x9, x9, x7
    ad4: 0003ffb7  lui          x31, 0x0003f  # x31 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    ad8: 2e0f8f93  addi         x31, x31, 736  # x31 = 0x0003f2e0 · arc_apb_reset_unit + 0xf2e0
    adc: 00048f13  addi         x30, x9, 0
    ae0: 00040e93  addi         x29, x8, 0
    ae4: 150000ef  jal          x1, 0x00000c34  # target 0x00000c34; x1 = 0x00000ae8
    ae8: 0c8000ef  jal          x1, 0x00000bb0  # target 0x00000bb0; x1 = 0x00000aec
    aec: 0e0000ef  jal          x1, 0x00000bcc  # target 0x00000bcc; x1 = 0x00000af0
    af0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    af4: 88828293  addi         x5, x5, -1912  # x5 = 0xffb00888 · riscv_local_mem + 0x888
    af8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x888 · 0xffb00888
    afc: 00220213  addi         x4, x4, 2
    b00: 01021213  slli         x4, x4, 16
    b04: 01025213  srli         x4, x4, 16
    b08: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    b0c: 88828293  addi         x5, x5, -1912  # x5 = 0xffb00888 · riscv_local_mem + 0x888
    b10: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    b14: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
    b18: 02028293  addi         x5, x5, 32  # x5 = 0xffb51020
    b1c: 0042a023  sw           x4, 0(x5)  # 0xffb51020; write runtime value
    b20: 0ff0000f  fence        0xf, 0xf
    b24: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    b28: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    b2c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884
    b30: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b34: 00520233  add          x4, x4, x5
    b38: 00040337  lui          x6, 0x00040  # x6 = 0x00040000
    b3c: 88030313  addi         x6, x6, -1920  # x6 = 0x0003f880 · arc_apb_reset_unit + 0xf880
    b40: 00626663  bltu         x4, x6, 0x00000b4c  # target 0x00000b4c
    b44: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    b48: 40720233  sub          x4, x4, x7
loc_b4c:
    b4c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    b50: 88440413  addi         x8, x8, -1916  # x8 = 0xffb00884 · riscv_local_mem + 0x884
    b54: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
loc_b58:
    b58: 2e40006f  jal          x0, 0x00000e3c  # target 0x00000e3c
loc_b5c:
    b5c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    b60: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    b64: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    b68: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    b6c: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    b70: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    b74: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    b78: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    b7c: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    b80: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    b84: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    b88: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    b8c: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    b90: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    b94: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    b98: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    b9c: 020f8f93  addi         x31, x31, 32
    ba0: 020f0f13  addi         x30, x30, 32
    ba4: ff8e8e93  addi         x29, x29, -8
    ba8: fa0e9ae3  bne          x29, x0, 0x00000b5c  # target 0x00000b5c
    bac: 00008067  jalr         x0, 0(x1)
loc_bb0:
    bb0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    bb4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    bb8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    bbc: 000a0463  beq          x20, x0, 0x00000bc4  # target 0x00000bc4
    bc0: ff1ff06f  jal          x0, 0x00000bb0  # target 0x00000bb0
loc_bc4:
    bc4: 0ff0000f  fence        0xf, 0xf
    bc8: 00008067  jalr         x0, 0(x1)
loc_bcc:
    bcc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    bd0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    bd4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    bd8: 000a0463  beq          x20, x0, 0x00000be0  # target 0x00000be0
    bdc: ff1ff06f  jal          x0, 0x00000bcc  # target 0x00000bcc
loc_be0:
    be0: 0ff0000f  fence        0xf, 0xf
    be4: 00008067  jalr         x0, 0(x1)
loc_be8:
    be8: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    bec: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
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
    c24: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c28: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c2c: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    c30: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_c34:
    c34: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    c38: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    c3c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    c40: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    c44: 015a6463  bltu         x20, x21, 0x00000c4c  # target 0x00000c4c
    c48: fedff06f  jal          x0, 0x00000c34  # target 0x00000c34
loc_c4c:
    c4c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    c50: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    c54: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    c58: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    c5c: 015a6463  bltu         x20, x21, 0x00000c64  # target 0x00000c64
    c60: fedff06f  jal          x0, 0x00000c4c  # target 0x00000c4c
loc_c64:
    c64: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    c68: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    c6c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    c70: 014a1a13  slli         x20, x20, 20
    c74: 014a5a13  srli         x20, x20, 20
    c78: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_c7c:
    c7c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    c80: 000b0463  beq          x22, x0, 0x00000c88  # target 0x00000c88
    c84: ff9ff06f  jal          x0, 0x00000c7c  # target 0x00000c7c
loc_c88:
    c88: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    c8c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    c90: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    c94: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    c98: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    c9c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    ca0: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    ca4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    ca8: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    cac: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    cb0: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    cb4: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    cb8: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    cbc: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    cc0: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    cc4: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    cc8: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    ccc: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    cd0: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    cd4: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    cd8: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_cdc:
    cdc: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    ce0: 000b0463  beq          x22, x0, 0x00000ce8  # target 0x00000ce8
    ce4: ff9ff06f  jal          x0, 0x00000cdc  # target 0x00000cdc
loc_ce8:
    ce8: 00008067  jalr         x0, 0(x1)
loc_cec:
    cec: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    cf0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    cf4: 007a7d13  andi         x26, x20, 7
    cf8: ff8a7a13  andi         x20, x20, -8
    cfc: 01af8ab3  add          x21, x31, x26
    d00: 007afb93  andi         x23, x21, 7
    d04: 003ada93  srli         x21, x21, 3
    d08: 00ba9a93  slli         x21, x21, 11
    d0c: 014a8ab3  add          x21, x21, x20
    d10: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d10
    d14: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d28
    d18: 001b9b93  slli         x23, x23, 1
    d1c: 017b0b33  add          x22, x22, x23
    d20: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d24: 00008067  jalr         x0, 0(x1)
    d28: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d2c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d30: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    d34: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_d38:
    d38: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    d3c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    d40: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    d44: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    d48: 015a6463  bltu         x20, x21, 0x00000d50  # target 0x00000d50
    d4c: fedff06f  jal          x0, 0x00000d38  # target 0x00000d38
loc_d50:
    d50: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    d54: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    d58: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    d5c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    d60: 015a6463  bltu         x20, x21, 0x00000d68  # target 0x00000d68
    d64: fedff06f  jal          x0, 0x00000d50  # target 0x00000d50
loc_d68:
    d68: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    d6c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    d70: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    d74: 014a1a13  slli         x20, x20, 20
    d78: 014a5a13  srli         x20, x20, 20
    d7c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_d80:
    d80: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    d84: 000b0463  beq          x22, x0, 0x00000d8c  # target 0x00000d8c
    d88: ff9ff06f  jal          x0, 0x00000d80  # target 0x00000d80
loc_d8c:
    d8c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    d90: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    d94: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    d98: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    d9c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    da0: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    da4: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    da8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    dac: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    db0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    db4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    db8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    dbc: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    dc0: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00001000
    dc4: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    dc8: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    dcc: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    dd0: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    dd4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    dd8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    ddc: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_de0:
    de0: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    de4: 000b0463  beq          x22, x0, 0x00000dec  # target 0x00000dec
    de8: ff9ff06f  jal          x0, 0x00000de0  # target 0x00000de0
loc_dec:
    dec: 00008067  jalr         x0, 0(x1)
loc_df0:
    df0: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    df4: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x0000078c
    df8: 007a7d13  andi         x26, x20, 7
    dfc: ff8a7a13  andi         x20, x20, -8
    e00: 01af8ab3  add          x21, x31, x26
    e04: 007afb93  andi         x23, x21, 7
    e08: 003ada93  srli         x21, x21, 3
    e0c: 00ba9a93  slli         x21, x21, 11
    e10: 014a8ab3  add          x21, x21, x20
    e14: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e14
    e18: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e2c
    e1c: 001b9b93  slli         x23, x23, 1
    e20: 017b0b33  add          x22, x22, x23
    e24: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e28: 00008067  jalr         x0, 0(x1)
    e2c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e30: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e34: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    e38: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    e3c:           j FW_NCRISC+4   # return to firmware, linked at install
