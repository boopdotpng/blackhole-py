# llama3 8b-fp8 decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000232b7  lui          x5, 0x00023  # x5 = 0x00023000
      c: 88028293  addi         x5, x5, -1920  # x5 = 0x00022880
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00022880
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     24: 88058593  addi         x11, x11, -1920  # x11 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00014637  lui          x12, 0x00014  # x12 = 0x00014000
     2c: 08060613  addi         x12, x12, 128  # x12 = 0x00014080
     30: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00014080
     34: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     38: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
     3c: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     40: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     44: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
     48: 00018637  lui          x12, 0x00018  # x12 = 0x00018000
     4c: 08060613  addi         x12, x12, 128  # x12 = 0x00018080
     50: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00018080
     54: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     58: 88c58593  addi         x11, x11, -1908  # x11 = 0xffb0088c · riscv_local_mem + 0x88c
     5c: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     60: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     64: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
     68: 00025637  lui          x12, 0x00025  # x12 = 0x00025000
     6c: 08060613  addi         x12, x12, 128  # x12 = 0x00025080
     70: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00025080
     74: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     78: 89458593  addi         x11, x11, -1900  # x11 = 0xffb00894 · riscv_local_mem + 0x894
     7c: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     80: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     84: 89848493  addi         x9, x9, -1896  # x9 = 0xffb00898 · riscv_local_mem + 0x898
     88: 00026537  lui          x10, 0x00026  # x10 = 0x00026000
     8c: 98050513  addi         x10, x10, -1664  # x10 = 0x00025980
     90: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00025980
     94: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     98: 89c48493  addi         x9, x9, -1892  # x9 = 0xffb0089c · riscv_local_mem + 0x89c
     9c: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
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
     d0: 32527ce3  bgeu         x4, x5, 0x00000c08  # target 0x00000c08
     d4: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     d8: 90028293  addi         x5, x5, -1792  # x5 = 0x00011900
     dc: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x00011900
     e0: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
     e4: 02525233  divu         x4, x4, x5
     e8: 325000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x000000ec
     ec: 33d000ef  jal          x1, 0x00000c28  # target 0x00000c28; x1 = 0x000000f0
     f0: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     f4: 0003a283  lw           x5, 0(x7)  # param start_pos; 0x000007ac
     f8: 0072f313  andi         x6, x5, 7
     fc: 00831313  slli         x6, x6, 8
    100: 0032d293  srli         x5, x5, 3
    104: 00028f93  addi         x31, x5, 0
    108: 33d000ef  jal          x1, 0x00000c44  # target 0x00000c44; x1 = 0x0000010c
    10c: 000a8393  addi         x7, x21, 0
    110: 000b0413  addi         x8, x22, 0
    114: 006383b3  add          x7, x7, x6
    118: 00038f93  addi         x31, x7, 0
    11c: 00040f13  addi         x30, x8, 0
    120: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    124: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00023880
    128: 369000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x0000012c
    12c: 00038f93  addi         x31, x7, 0
    130: 00040f13  addi         x30, x8, 0
    134: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    138: 980e8e93  addi         x29, x29, -1664  # x29 = 0x00023980
    13c: 355000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x00000140
    140: 00038f93  addi         x31, x7, 0
    144: 00040f13  addi         x30, x8, 0
    148: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    14c: a80e8e93  addi         x29, x29, -1408  # x29 = 0x00023a80
    150: 341000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x00000154
    154: 00038f93  addi         x31, x7, 0
    158: 00040f13  addi         x30, x8, 0
    15c: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    160: b80e8e93  addi         x29, x29, -1152  # x29 = 0x00023b80
    164: 32d000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x00000168
    168: 00038f93  addi         x31, x7, 0
    16c: 00040f13  addi         x30, x8, 0
    170: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    174: c80e8e93  addi         x29, x29, -896  # x29 = 0x00023c80
    178: 319000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x0000017c
    17c: 00028f93  addi         x31, x5, 0
    180: 3b1000ef  jal          x1, 0x00000d30  # target 0x00000d30; x1 = 0x00000184
    184: 000a8393  addi         x7, x21, 0
    188: 000b0413  addi         x8, x22, 0
    18c: 006383b3  add          x7, x7, x6
    190: 00038f93  addi         x31, x7, 0
    194: 00040f13  addi         x30, x8, 0
    198: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    19c: 080e8e93  addi         x29, x29, 128  # x29 = 0x00024080
    1a0: 2f1000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x000001a4
    1a4: 00038f93  addi         x31, x7, 0
    1a8: 00040f13  addi         x30, x8, 0
    1ac: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1b0: 180e8e93  addi         x29, x29, 384  # x29 = 0x00024180
    1b4: 2dd000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x000001b8
    1b8: 00038f93  addi         x31, x7, 0
    1bc: 00040f13  addi         x30, x8, 0
    1c0: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1c4: 280e8e93  addi         x29, x29, 640  # x29 = 0x00024280
    1c8: 2c9000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x000001cc
    1cc: 00038f93  addi         x31, x7, 0
    1d0: 00040f13  addi         x30, x8, 0
    1d4: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1d8: 380e8e93  addi         x29, x29, 896  # x29 = 0x00024380
    1dc: 2b5000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x000001e0
    1e0: 00038f93  addi         x31, x7, 0
    1e4: 00040f13  addi         x30, x8, 0
    1e8: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1ec: 480e8e93  addi         x29, x29, 1152  # x29 = 0x00024480
    1f0: 2a1000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x000001f4
    1f4: 00921293  slli         x5, x4, 9
    1f8: 3ff2f313  andi         x6, x5, 1023
    1fc: 00131313  slli         x6, x6, 1
    200: 00a2d293  srli         x5, x5, 10
    204: 00028f93  addi         x31, x5, 0
    208: 375000ef  jal          x1, 0x00000d7c  # target 0x00000d7c; x1 = 0x0000020c
    20c: 000a8393  addi         x7, x21, 0
    210: 000b0413  addi         x8, x22, 0
    214: 006383b3  add          x7, x7, x6
    218: 00038f93  addi         x31, x7, 0
    21c: 00040f13  addi         x30, x8, 0
    220: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    224: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00022880
loc_228:
    228: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    22c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    230: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    234: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    238: 015a6463  bltu         x20, x21, 0x00000240  # target 0x00000240
    23c: fedff06f  jal          x0, 0x00000228  # target 0x00000228
loc_240:
    240: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    244: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    248: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    24c: 014a1a13  slli         x20, x20, 20
    250: 014a5a13  srli         x20, x20, 20
    254: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_258:
    258: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    25c: 000b0463  beq          x22, x0, 0x00000264  # target 0x00000264
    260: ff9ff06f  jal          x0, 0x00000258  # target 0x00000258
loc_264:
    264: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    268: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    26c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    270: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    274: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00022880
    278: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    27c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    280: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    284: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    288: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    28c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    290: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    294: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    298: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000400
    29c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    2a0: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    2a4: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    2a8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    2ac: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    2b0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    2b4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_2b8:
    2b8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    2bc: 000b0463  beq          x22, x0, 0x000002c4  # target 0x000002c4
    2c0: ff9ff06f  jal          x0, 0x000002b8  # target 0x000002b8
loc_2c4:
    2c4: 08038493  addi         x9, x7, 128
    2c8: 00048f93  addi         x31, x9, 0
    2cc: 00040f13  addi         x30, x8, 0
    2d0: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    2d4: 080e8e93  addi         x29, x29, 128  # x29 = 0x00023080
    2d8: 2f1000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x000002dc
    2dc: 00038f93  addi         x31, x7, 0
    2e0: 00040f13  addi         x30, x8, 0
    2e4: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    2e8: 100e8e93  addi         x29, x29, 256  # x29 = 0x00023100
    2ec: 2dd000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x000002f0
    2f0: 18038493  addi         x9, x7, 384
    2f4: 00048f93  addi         x31, x9, 0
    2f8: 00040f13  addi         x30, x8, 0
    2fc: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    300: 180e8e93  addi         x29, x29, 384  # x29 = 0x00023180
    304: 2c5000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x00000308
    308: 10038493  addi         x9, x7, 256
    30c: 00048f93  addi         x31, x9, 0
    310: 00040f13  addi         x30, x8, 0
    314: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    318: 200e8e93  addi         x29, x29, 512  # x29 = 0x00023200
    31c: 2ad000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x00000320
    320: 28038493  addi         x9, x7, 640
    324: 00048f93  addi         x31, x9, 0
    328: 00040f13  addi         x30, x8, 0
    32c: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    330: 280e8e93  addi         x29, x29, 640  # x29 = 0x00023280
    334: 295000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x00000338
    338: 20038493  addi         x9, x7, 512
    33c: 00048f93  addi         x31, x9, 0
    340: 00040f13  addi         x30, x8, 0
    344: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    348: 300e8e93  addi         x29, x29, 768  # x29 = 0x00023300
    34c: 27d000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x00000350
    350: 38038493  addi         x9, x7, 896
    354: 00048f93  addi         x31, x9, 0
    358: 00040f13  addi         x30, x8, 0
    35c: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    360: 380e8e93  addi         x29, x29, 896  # x29 = 0x00023380
    364: 265000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x00000368
    368: 30038493  addi         x9, x7, 768
    36c: 00048f93  addi         x31, x9, 0
    370: 00040f13  addi         x30, x8, 0
    374: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    378: 400e8e93  addi         x29, x29, 1024  # x29 = 0x00023400
    37c: 24d000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x00000380
    380: 00221293  slli         x5, x4, 2
    384: 0022d293  srli         x5, x5, 2
    388: 00729293  slli         x5, x5, 7
    38c: 3ff2f313  andi         x6, x5, 1023
    390: 00131313  slli         x6, x6, 1
    394: 00a2d293  srli         x5, x5, 10
    398: 00028f93  addi         x31, x5, 0
    39c: 2cd000ef  jal          x1, 0x00000e68  # target 0x00000e68; x1 = 0x000003a0
    3a0: 000a8393  addi         x7, x21, 0
    3a4: 000b0413  addi         x8, x22, 0
    3a8: 006383b3  add          x7, x7, x6
    3ac: 00038f93  addi         x31, x7, 0
    3b0: 00040f13  addi         x30, x8, 0
    3b4: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    3b8: c80e8e93  addi         x29, x29, -896  # x29 = 0x00022c80
    3bc: 0d5000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x000003c0
    3c0: 08038493  addi         x9, x7, 128
    3c4: 00048f93  addi         x31, x9, 0
    3c8: 00040f13  addi         x30, x8, 0
    3cc: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    3d0: 480e8e93  addi         x29, x29, 1152  # x29 = 0x00023480
    3d4: 1f5000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x000003d8
    3d8: 00038f93  addi         x31, x7, 0
    3dc: 00040f13  addi         x30, x8, 0
    3e0: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    3e4: 500e8e93  addi         x29, x29, 1280  # x29 = 0x00023500
    3e8: 1e1000ef  jal          x1, 0x00000dc8  # target 0x00000dc8; x1 = 0x000003ec
    3ec: 00221293  slli         x5, x4, 2
    3f0: 0022d293  srli         x5, x5, 2
    3f4: 00729293  slli         x5, x5, 7
    3f8: 3ff2f313  andi         x6, x5, 1023
    3fc: 00131313  slli         x6, x6, 1
    400: 00a2d293  srli         x5, x5, 10
    404: 00028f93  addi         x31, x5, 0
    408: 2ad000ef  jal          x1, 0x00000eb4  # target 0x00000eb4; x1 = 0x0000040c
    40c: 000a8393  addi         x7, x21, 0
    410: 000b0413  addi         x8, x22, 0
    414: 006383b3  add          x7, x7, x6
    418: 00038f93  addi         x31, x7, 0
    41c: 00040f13  addi         x30, x8, 0
    420: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    424: 880e8e93  addi         x29, x29, -1920  # x29 = 0x00025880
    428: 069000ef  jal          x1, 0x00000c90  # target 0x00000c90; x1 = 0x0000042c
    42c: 7fc000ef  jal          x1, 0x00000c28  # target 0x00000c28; x1 = 0x00000430
    430: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    434: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    438: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    43c: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    440: 00520233  add          x4, x4, x5
    444: 00025337  lui          x6, 0x00025  # x6 = 0x00025000
    448: 88030313  addi         x6, x6, -1920  # x6 = 0x00024880
    44c: 00626663  bltu         x4, x6, 0x00000458  # target 0x00000458
    450: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    454: 40720233  sub          x4, x4, x7
loc_458:
    458: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    45c: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    460: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    464: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    468: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    46c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    470: 00420213  addi         x4, x4, 4
    474: 01021213  slli         x4, x4, 16
    478: 01025213  srli         x4, x4, 16
    47c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    480: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    484: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    488: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    48c: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    490: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    494: 0ff0000f  fence        0xf, 0xf
    498: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    49c: 90038393  addi         x7, x7, -1792  # x7 = 0x00011900
    4a0: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x00011900
    4a4: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
    4a8: 02725233  divu         x4, x4, x7
    4ac: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    4b0: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    4b4: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    4b8: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    4bc: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    4c0: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    4c4: 00747a63  bgeu         x8, x7, 0x000004d8  # target 0x000004d8
    4c8: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    4cc: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    4d0: 00747463  bgeu         x8, x7, 0x000004d8  # target 0x000004d8
    4d4: 00800313  addi         x6, x0, 8  # x6 = 0x00000008
loc_4d8:
    4d8: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4dc: 90448493  addi         x9, x9, -1788  # x9 = 0x00011904
    4e0: 0004a383  lw           x7, 0(x9)  # param attention_phase; 0x00011904
    4e4: 79000593  addi         x11, x0, 1936  # x11 = 0x00000790
    4e8: 0005a483  lw           x9, 0(x11)  # param kv_blocks; 0x00000790
    4ec: 00100413  addi         x8, x0, 1  # x8 = 0x00000001
    4f0: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
    4f4: 00957a63  bgeu         x10, x9, 0x00000508  # target 0x00000508
    4f8: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    4fc: 05000513  addi         x10, x0, 80  # x10 = 0x00000050
    500: 00957463  bgeu         x10, x9, 0x00000508  # target 0x00000508
    504: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
loc_508:
    508: 008282b3  add          x5, x5, x8
    50c: fff28293  addi         x5, x5, -1
    510: 407282b3  sub          x5, x5, x7
    514: 0282d2b3  divu         x5, x5, x8
    518: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    51c: 00028413  addi         x8, x5, 0
loc_520:
    520: 6083fe63  bgeu         x7, x8, 0x00000b3c  # target 0x00000b3c
    524: 00025493  srli         x9, x4, 0
    528: 00a49493  slli         x9, x9, 10
    52c: 02638533  mul          x10, x7, x6
    530: 00012637  lui          x12, 0x00012  # x12 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    534: 90460613  addi         x12, x12, -1788  # x12 = 0x00011904
    538: 00062583  lw           x11, 0(x12)  # param attention_phase; 0x00011904
    53c: 00b50533  add          x10, x10, x11
    540: 79000613  addi         x12, x0, 1936  # x12 = 0x00000790
    544: 00062583  lw           x11, 0(x12)  # param kv_blocks; 0x00000790
    548: fff58593  addi         x11, x11, -1
    54c: 40b505b3  sub          x11, x10, x11
    550: 00251513  slli         x10, x10, 2
    554: 00a484b3  add          x9, x9, x10
    558: 00058513  addi         x10, x11, 0
    55c: 6b0000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x00000560
    560: 6c8000ef  jal          x1, 0x00000c28  # target 0x00000c28; x1 = 0x00000564
    564: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    568: 88480813  addi         x16, x16, -1916  # x16 = 0xffb00884 · riscv_local_mem + 0x884
    56c: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x884 · 0xffb00884
loc_570:
    570: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    574: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    578: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    57c: 40c586b3  sub          x13, x11, x12
    580: 01069693  slli         x13, x13, 16
    584: 0106d693  srli         x13, x13, 16
    588: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    58c: 40d70733  sub          x14, x14, x13
    590: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    594: 00f77663  bgeu         x14, x15, 0x000005a0  # target 0x000005a0
    598: 0ff0000f  fence        0xf, 0xf
    59c: fd5ff06f  jal          x0, 0x00000570  # target 0x00000570
loc_5a0:
    5a0: 0ff0000f  fence        0xf, 0xf
    5a4: 00048593  addi         x11, x9, 0
    5a8: 00058f93  addi         x31, x11, 0
    5ac: 155000ef  jal          x1, 0x00000f00  # target 0x00000f00; x1 = 0x000005b0
    5b0: 000a8613  addi         x12, x21, 0
    5b4: 000b0693  addi         x13, x22, 0
    5b8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    5bc: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    5c0: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    5c4: 00060f93  addi         x31, x12, 0
    5c8: 00068f13  addi         x30, x13, 0
    5cc: 00070e93  addi         x29, x14, 0
    5d0: 17d000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x000005d4
    5d4: 00148593  addi         x11, x9, 1
    5d8: 00058f93  addi         x31, x11, 0
    5dc: 215000ef  jal          x1, 0x00000ff0  # target 0x00000ff0; x1 = 0x000005e0
    5e0: 000a8613  addi         x12, x21, 0
    5e4: 000b0693  addi         x13, x22, 0
    5e8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    5ec: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    5f0: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    5f4: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5f8: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    5fc: 00f70733  add          x14, x14, x15
    600: 00060f93  addi         x31, x12, 0
    604: 00068f13  addi         x30, x13, 0
    608: 00070e93  addi         x29, x14, 0
    60c: 141000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x00000610
    610: 00248593  addi         x11, x9, 2
    614: 00058f93  addi         x31, x11, 0
    618: 225000ef  jal          x1, 0x0000103c  # target 0x0000103c; x1 = 0x0000061c
    61c: 000a8613  addi         x12, x21, 0
    620: 000b0693  addi         x13, x22, 0
    624: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    628: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    62c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    630: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    634: 00f70733  add          x14, x14, x15
    638: 00060f93  addi         x31, x12, 0
    63c: 00068f13  addi         x30, x13, 0
    640: 00070e93  addi         x29, x14, 0
    644: 109000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x00000648
    648: 00348593  addi         x11, x9, 3
    64c: 00058f93  addi         x31, x11, 0
    650: 0b1000ef  jal          x1, 0x00000f00  # target 0x00000f00; x1 = 0x00000654
    654: 000a8613  addi         x12, x21, 0
    658: 000b0693  addi         x13, x22, 0
    65c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    660: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    664: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    668: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    66c: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    670: 00f70733  add          x14, x14, x15
    674: 00060f93  addi         x31, x12, 0
    678: 00068f13  addi         x30, x13, 0
    67c: 00070e93  addi         x29, x14, 0
    680: 0cd000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x00000684
    684: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    688: 88c80813  addi         x16, x16, -1908  # x16 = 0xffb0088c · riscv_local_mem + 0x88c
    68c: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_690:
    690: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    694: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    698: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    69c: 40c586b3  sub          x13, x11, x12
    6a0: 01069693  slli         x13, x13, 16
    6a4: 0106d693  srli         x13, x13, 16
    6a8: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    6ac: 40d70733  sub          x14, x14, x13
    6b0: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    6b4: 00f77663  bgeu         x14, x15, 0x000006c0  # target 0x000006c0
    6b8: 0ff0000f  fence        0xf, 0xf
    6bc: fd5ff06f  jal          x0, 0x00000690  # target 0x00000690
loc_6c0:
    6c0: 0ff0000f  fence        0xf, 0xf
    6c4: 00048593  addi         x11, x9, 0
    6c8: 00058f93  addi         x31, x11, 0
    6cc: 1bd000ef  jal          x1, 0x00001088  # target 0x00001088; x1 = 0x000006d0
    6d0: 000a8613  addi         x12, x21, 0
    6d4: 000b0693  addi         x13, x22, 0
    6d8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    6dc: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    6e0: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    6e4: 00060f93  addi         x31, x12, 0
    6e8: 00068f13  addi         x30, x13, 0
    6ec: 00070e93  addi         x29, x14, 0
    6f0: 05d000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x000006f4
    6f4: 00148593  addi         x11, x9, 1
    6f8: 00058f93  addi         x31, x11, 0
    6fc: 1d9000ef  jal          x1, 0x000010d4  # target 0x000010d4; x1 = 0x00000700
    700: 000a8613  addi         x12, x21, 0
    704: 000b0693  addi         x13, x22, 0
    708: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    70c: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    710: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    714: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    718: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    71c: 00f70733  add          x14, x14, x15
    720: 00060f93  addi         x31, x12, 0
    724: 00068f13  addi         x30, x13, 0
    728: 00070e93  addi         x29, x14, 0
    72c: 021000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x00000730
    730: 00248593  addi         x11, x9, 2
    734: 00058f93  addi         x31, x11, 0
    738: 1e9000ef  jal          x1, 0x00001120  # target 0x00001120; x1 = 0x0000073c
    73c: 000a8613  addi         x12, x21, 0
    740: 000b0693  addi         x13, x22, 0
    744: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    748: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    74c: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    750: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    754: 00f70733  add          x14, x14, x15
    758: 00060f93  addi         x31, x12, 0
    75c: 00068f13  addi         x30, x13, 0
    760: 00070e93  addi         x29, x14, 0
    764: 7e8000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x00000768
    768: 00348593  addi         x11, x9, 3
    76c: 00058f93  addi         x31, x11, 0
    770: 119000ef  jal          x1, 0x00001088  # target 0x00001088; x1 = 0x00000774
    774: 000a8613  addi         x12, x21, 0
    778: 000b0693  addi         x13, x22, 0
    77c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    780: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    784: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    788: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    78c: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    790: 00f70733  add          x14, x14, x15
    794: 00060f93  addi         x31, x12, 0
    798: 00068f13  addi         x30, x13, 0
    79c: 00070e93  addi         x29, x14, 0
    7a0: 7ac000ef  jal          x1, 0x00000f4c  # target 0x00000f4c; x1 = 0x000007a4
    7a4: 484000ef  jal          x1, 0x00000c28  # target 0x00000c28; x1 = 0x000007a8
    7a8: 2a051e63  bne          x10, x0, 0x00000a64  # target 0x00000a64
    7ac: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    7b0: 89478793  addi         x15, x15, -1900  # x15 = 0xffb00894 · riscv_local_mem + 0x894
    7b4: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x894 · 0xffb00894
    7b8: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
loc_7bc:
    7bc: ffb4f7b7  lui          x15, 0xffb4f  # x15 = 0xffb4f000
    7c0: 02878793  addi         x15, x15, 40  # x15 = 0xffb4f028
    7c4: 0007d603  lhu          x12, 0(x15)  # 0xffb4f028
    7c8: 40b606b3  sub          x13, x12, x11
    7cc: 01069693  slli         x13, x13, 16
    7d0: 0106d693  srli         x13, x13, 16
    7d4: 00e6f663  bgeu         x13, x14, 0x000007e0  # target 0x000007e0
    7d8: 0ff0000f  fence        0xf, 0xf
    7dc: fe1ff06f  jal          x0, 0x000007bc  # target 0x000007bc
loc_7e0:
    7e0: 0ff0000f  fence        0xf, 0xf
    7e4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    7e8: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    7ec: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    7f0: 7ac00793  addi         x15, x0, 1964  # x15 = 0x000007ac
    7f4: 0007a603  lw           x12, 0(x15)  # param start_pos; 0x000007ac
    7f8: 01067793  andi         x15, x12, 16
    7fc: 00679793  slli         x15, x15, 6
    800: 00f67613  andi         x12, x12, 15
    804: 00561613  slli         x12, x12, 5
    808: 00f60633  add          x12, x12, x15
    80c: 00b60633  add          x12, x12, x11
    810: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    814: c8070713  addi         x14, x14, -896  # x14 = 0x00024c80
    818: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    81c: 00c686b3  add          x13, x13, x12
    820: 00070f93  addi         x31, x14, 0  # x31 = 0x00024c80
    824: 00068f13  addi         x30, x13, 0
    828: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    82c: 141000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000830
    830: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    834: ca070713  addi         x14, x14, -864  # x14 = 0x00024ca0
    838: 20000693  addi         x13, x0, 512  # x13 = 0x00000200
    83c: 00c686b3  add          x13, x13, x12
    840: 00070f93  addi         x31, x14, 0  # x31 = 0x00024ca0
    844: 00068f13  addi         x30, x13, 0
    848: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    84c: 121000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000850
    850: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    854: cc070713  addi         x14, x14, -832  # x14 = 0x00024cc0
    858: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    85c: 80068693  addi         x13, x13, -2048  # x13 = 0x00000800
    860: 00c686b3  add          x13, x13, x12
    864: 00070f93  addi         x31, x14, 0  # x31 = 0x00024cc0
    868: 00068f13  addi         x30, x13, 0
    86c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    870: 0fd000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000874
    874: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    878: ce070713  addi         x14, x14, -800  # x14 = 0x00024ce0
    87c: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    880: a0068693  addi         x13, x13, -1536  # x13 = 0x00000a00
    884: 00c686b3  add          x13, x13, x12
    888: 00070f93  addi         x31, x14, 0  # x31 = 0x00024ce0
    88c: 00068f13  addi         x30, x13, 0
    890: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    894: 0d9000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000898
    898: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    89c: d0070713  addi         x14, x14, -768  # x14 = 0x00024d00
    8a0: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8a4: 00c686b3  add          x13, x13, x12
    8a8: 00070f93  addi         x31, x14, 0  # x31 = 0x00024d00
    8ac: 00068f13  addi         x30, x13, 0
    8b0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    8b4: 0b9000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x000008b8
    8b8: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    8bc: d2070713  addi         x14, x14, -736  # x14 = 0x00024d20
    8c0: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8c4: 20068693  addi         x13, x13, 512  # x13 = 0x00001200
    8c8: 00c686b3  add          x13, x13, x12
    8cc: 00070f93  addi         x31, x14, 0  # x31 = 0x00024d20
    8d0: 00068f13  addi         x30, x13, 0
    8d4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    8d8: 095000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x000008dc
    8dc: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    8e0: d4070713  addi         x14, x14, -704  # x14 = 0x00024d40
    8e4: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    8e8: 80068693  addi         x13, x13, -2048  # x13 = 0x00001800
    8ec: 00c686b3  add          x13, x13, x12
    8f0: 00070f93  addi         x31, x14, 0  # x31 = 0x00024d40
    8f4: 00068f13  addi         x30, x13, 0
    8f8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    8fc: 071000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000900
    900: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    904: d6070713  addi         x14, x14, -672  # x14 = 0x00024d60
    908: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    90c: a0068693  addi         x13, x13, -1536  # x13 = 0x00001a00
    910: 00c686b3  add          x13, x13, x12
    914: 00070f93  addi         x31, x14, 0  # x31 = 0x00024d60
    918: 00068f13  addi         x30, x13, 0
    91c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    920: 04d000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000924
    924: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    928: 88860613  addi         x12, x12, -1912  # x12 = 0xffb00888 · riscv_local_mem + 0x888
    92c: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x888 · 0xffb00888
    930: 7ac00793  addi         x15, x0, 1964  # x15 = 0x000007ac
    934: 0007a603  lw           x12, 0(x15)  # param start_pos; 0x000007ac
    938: 01067793  andi         x15, x12, 16
    93c: 00679793  slli         x15, x15, 6
    940: 00f67613  andi         x12, x12, 15
    944: 00561613  slli         x12, x12, 5
    948: 00f60633  add          x12, x12, x15
    94c: 00b60633  add          x12, x12, x11
    950: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    954: 88070713  addi         x14, x14, -1920  # x14 = 0x00025880
    958: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    95c: 00c686b3  add          x13, x13, x12
    960: 00070f93  addi         x31, x14, 0  # x31 = 0x00025880
    964: 00068f13  addi         x30, x13, 0
    968: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    96c: 001000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000970
    970: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    974: 8a070713  addi         x14, x14, -1888  # x14 = 0x000258a0
    978: 20000693  addi         x13, x0, 512  # x13 = 0x00000200
    97c: 00c686b3  add          x13, x13, x12
    980: 00070f93  addi         x31, x14, 0  # x31 = 0x000258a0
    984: 00068f13  addi         x30, x13, 0
    988: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    98c: 7e0000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000990
    990: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    994: 8c070713  addi         x14, x14, -1856  # x14 = 0x000258c0
    998: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    99c: 80068693  addi         x13, x13, -2048  # x13 = 0x00000800
    9a0: 00c686b3  add          x13, x13, x12
    9a4: 00070f93  addi         x31, x14, 0  # x31 = 0x000258c0
    9a8: 00068f13  addi         x30, x13, 0
    9ac: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    9b0: 7bc000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x000009b4
    9b4: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    9b8: 8e070713  addi         x14, x14, -1824  # x14 = 0x000258e0
    9bc: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9c0: a0068693  addi         x13, x13, -1536  # x13 = 0x00000a00
    9c4: 00c686b3  add          x13, x13, x12
    9c8: 00070f93  addi         x31, x14, 0  # x31 = 0x000258e0
    9cc: 00068f13  addi         x30, x13, 0
    9d0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    9d4: 798000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x000009d8
    9d8: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    9dc: 90070713  addi         x14, x14, -1792  # x14 = 0x00025900
    9e0: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9e4: 00c686b3  add          x13, x13, x12
    9e8: 00070f93  addi         x31, x14, 0  # x31 = 0x00025900
    9ec: 00068f13  addi         x30, x13, 0
    9f0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    9f4: 778000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x000009f8
    9f8: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    9fc: 92070713  addi         x14, x14, -1760  # x14 = 0x00025920
    a00: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    a04: 20068693  addi         x13, x13, 512  # x13 = 0x00001200
    a08: 00c686b3  add          x13, x13, x12
    a0c: 00070f93  addi         x31, x14, 0  # x31 = 0x00025920
    a10: 00068f13  addi         x30, x13, 0
    a14: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    a18: 754000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000a1c
    a1c: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    a20: 94070713  addi         x14, x14, -1728  # x14 = 0x00025940
    a24: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    a28: 80068693  addi         x13, x13, -2048  # x13 = 0x00001800
    a2c: 00c686b3  add          x13, x13, x12
    a30: 00070f93  addi         x31, x14, 0  # x31 = 0x00025940
    a34: 00068f13  addi         x30, x13, 0
    a38: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    a3c: 730000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000a40
    a40: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    a44: 96070713  addi         x14, x14, -1696  # x14 = 0x00025960
    a48: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    a4c: a0068693  addi         x13, x13, -1536  # x13 = 0x00001a00
    a50: 00c686b3  add          x13, x13, x12
    a54: 00070f93  addi         x31, x14, 0  # x31 = 0x00025960
    a58: 00068f13  addi         x30, x13, 0
    a5c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    a60: 70c000ef  jal          x1, 0x0000116c  # target 0x0000116c; x1 = 0x00000a64
loc_a64:
    a64: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a68: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    a6c: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    a70: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    a74: 00c585b3  add          x11, x11, x12
    a78: 000186b7  lui          x13, 0x00018  # x13 = 0x00018000
    a7c: 08068693  addi         x13, x13, 128  # x13 = 0x00018080
    a80: 00d5e663  bltu         x11, x13, 0x00000a8c  # target 0x00000a8c
    a84: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    a88: 40e585b3  sub          x11, x11, x14
loc_a8c:
    a8c: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a90: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    a94: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    a98: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    a9c: 88460613  addi         x12, x12, -1916  # x12 = 0xffb00884 · riscv_local_mem + 0x884
    aa0: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x884 · 0xffb00884
    aa4: 00458593  addi         x11, x11, 4
    aa8: 01059593  slli         x11, x11, 16
    aac: 0105d593  srli         x11, x11, 16
    ab0: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    ab4: 88460613  addi         x12, x12, -1916  # x12 = 0xffb00884 · riscv_local_mem + 0x884
    ab8: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    abc: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    ac0: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    ac4: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    ac8: 0ff0000f  fence        0xf, 0xf
    acc: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ad0: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    ad4: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    ad8: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    adc: 00c585b3  add          x11, x11, x12
    ae0: 0001c6b7  lui          x13, 0x0001c  # x13 = 0x0001c000
    ae4: 08068693  addi         x13, x13, 128  # x13 = 0x0001c080
    ae8: 00d5e663  bltu         x11, x13, 0x00000af4  # target 0x00000af4
    aec: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    af0: 40e585b3  sub          x11, x11, x14
loc_af4:
    af4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    af8: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    afc: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    b00: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b04: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    b08: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
    b0c: 00458593  addi         x11, x11, 4
    b10: 01059593  slli         x11, x11, 16
    b14: 0105d593  srli         x11, x11, 16
    b18: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b1c: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    b20: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    b24: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    b28: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    b2c: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    b30: 0ff0000f  fence        0xf, 0xf
    b34: 00138393  addi         x7, x7, 1
    b38: 9e9ff06f  jal          x0, 0x00000520  # target 0x00000520
loc_b3c:
    b3c: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b40: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    b44: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    b48: 0c021063  bne          x4, x0, 0x00000c08  # target 0x00000c08
    b4c: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    b50: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    b54: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    b58: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    b5c: 00747a63  bgeu         x8, x7, 0x00000b70  # target 0x00000b70
    b60: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    b64: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    b68: 00747463  bgeu         x8, x7, 0x00000b70  # target 0x00000b70
    b6c: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_b70:
    b70: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b74: 04030313  addi         x6, x6, 64  # x6 = 0x00012040
loc_b78:
    b78: 00032283  lw           x5, 0(x6)  # 0x00012040
    b7c: 00428663  beq          x5, x4, 0x00000b88  # target 0x00000b88
    b80: 0ff0000f  fence        0xf, 0xf
    b84: ff5ff06f  jal          x0, 0x00000b78  # target 0x00000b78
loc_b88:
    b88: 00032023  sw           x0, 0(x6)  # 0x00012040; write 0x00000000
    b8c: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    b90: 00020413  addi         x8, x4, 0
loc_b94:
    b94: 0683fa63  bgeu         x7, x8, 0x00000c08  # target 0x00000c08
    b98: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    b9c: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    ba0: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    ba4: 00006537  lui          x10, 0x00006  # x10 = 0x00006000
    ba8: 00a484b3  add          x9, x9, x10
    bac: 000565b7  lui          x11, 0x00056  # x11 = 0x00056000
    bb0: 98058593  addi         x11, x11, -1664  # x11 = 0x00055980
    bb4: 00b4e663  bltu         x9, x11, 0x00000bc0  # target 0x00000bc0
    bb8: 00030637  lui          x12, 0x00030  # x12 = 0x00030000 · arc_apb_reset_unit + 0x0
    bbc: 40c484b3  sub          x9, x9, x12
loc_bc0:
    bc0: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    bc4: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    bc8: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    bcc: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    bd0: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    bd4: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    bd8: 00648493  addi         x9, x9, 6
    bdc: 01049493  slli         x9, x9, 16
    be0: 0104d493  srli         x9, x9, 16
    be4: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    be8: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    bec: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    bf0: ffb50537  lui          x10, 0xffb50  # x10 = 0xffb50000
    bf4: 02850513  addi         x10, x10, 40  # x10 = 0xffb50028
    bf8: 00952023  sw           x9, 0(x10)  # 0xffb50028; write runtime value
    bfc: 0ff0000f  fence        0xf, 0xf
    c00: 00138393  addi         x7, x7, 1
    c04: f91ff06f  jal          x0, 0x00000b94  # target 0x00000b94
loc_c08:
    c08: 5b80006f  jal          x0, 0x000011c0  # target 0x000011c0
loc_c0c:
    c0c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c10: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    c14: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    c18: 000a0463  beq          x20, x0, 0x00000c20  # target 0x00000c20
    c1c: ff1ff06f  jal          x0, 0x00000c0c  # target 0x00000c0c
loc_c20:
    c20: 0ff0000f  fence        0xf, 0xf
    c24: 00008067  jalr         x0, 0(x1)
loc_c28:
    c28: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c2c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c30: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c34: 000a0463  beq          x20, x0, 0x00000c3c  # target 0x00000c3c
    c38: ff1ff06f  jal          x0, 0x00000c28  # target 0x00000c28
loc_c3c:
    c3c: 0ff0000f  fence        0xf, 0xf
    c40: 00008067  jalr         x0, 0(x1)
loc_c44:
    c44: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    c48: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    c4c: 007a7d13  andi         x26, x20, 7
    c50: ff8a7a13  andi         x20, x20, -8
    c54: 01af8ab3  add          x21, x31, x26
    c58: 007afb93  andi         x23, x21, 7
    c5c: 003ada93  srli         x21, x21, 3
    c60: 00ba9a93  slli         x21, x21, 11
    c64: 014a8ab3  add          x21, x21, x20
    c68: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c68
    c6c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c80
    c70: 001b9b93  slli         x23, x23, 1
    c74: 017b0b33  add          x22, x22, x23
    c78: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c7c: 00008067  jalr         x0, 0(x1)
    c80: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c84: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c88: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c8c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c90:
    c90: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c94: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c98: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c9c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    ca0: 015a6463  bltu         x20, x21, 0x00000ca8  # target 0x00000ca8
    ca4: fedff06f  jal          x0, 0x00000c90  # target 0x00000c90
loc_ca8:
    ca8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    cac: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    cb0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    cb4: 014a1a13  slli         x20, x20, 20
    cb8: 014a5a13  srli         x20, x20, 20
    cbc: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_cc0:
    cc0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    cc4: 000b0463  beq          x22, x0, 0x00000ccc  # target 0x00000ccc
    cc8: ff9ff06f  jal          x0, 0x00000cc0  # target 0x00000cc0
loc_ccc:
    ccc: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    cd0: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    cd4: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    cd8: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    cdc: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    ce0: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    ce4: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    ce8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    cec: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    cf0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    cf4: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    cf8: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    cfc: 10000c13  addi         x24, x0, 256  # x24 = 0x00000100
    d00: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000100
    d04: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    d08: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    d0c: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    d10: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    d14: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    d18: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    d1c: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_d20:
    d20: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d24: 000b0463  beq          x22, x0, 0x00000d2c  # target 0x00000d2c
    d28: ff9ff06f  jal          x0, 0x00000d20  # target 0x00000d20
loc_d2c:
    d2c: 00008067  jalr         x0, 0(x1)
loc_d30:
    d30: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    d34: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    d38: 007a7d13  andi         x26, x20, 7
    d3c: ff8a7a13  andi         x20, x20, -8
    d40: 01af8ab3  add          x21, x31, x26
    d44: 007afb93  andi         x23, x21, 7
    d48: 003ada93  srli         x21, x21, 3
    d4c: 00ba9a93  slli         x21, x21, 11
    d50: 014a8ab3  add          x21, x21, x20
    d54: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d54
    d58: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d6c
    d5c: 001b9b93  slli         x23, x23, 1
    d60: 017b0b33  add          x22, x22, x23
    d64: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d68: 00008067  jalr         x0, 0(x1)
    d6c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    d70: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d74: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    d78: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d7c:
    d7c: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    d80: 000aaa03  lw           x20, 0(x21)  # param e2e_q; 0x00000798
    d84: 007a7d13  andi         x26, x20, 7
    d88: ff8a7a13  andi         x20, x20, -8
    d8c: 01af8ab3  add          x21, x31, x26
    d90: 007afb93  andi         x23, x21, 7
    d94: 003ada93  srli         x21, x21, 3
    d98: 00ba9a93  slli         x21, x21, 11
    d9c: 014a8ab3  add          x21, x21, x20
    da0: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000da0
    da4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000db8
    da8: 001b9b93  slli         x23, x23, 1
    dac: 017b0b33  add          x22, x22, x23
    db0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    db4: 00008067  jalr         x0, 0(x1)
    db8: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    dbc: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    dc0: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    dc4: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_dc8:
    dc8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    dcc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    dd0: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    dd4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    dd8: 015a6463  bltu         x20, x21, 0x00000de0  # target 0x00000de0
    ddc: fedff06f  jal          x0, 0x00000dc8  # target 0x00000dc8
loc_de0:
    de0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    de4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    de8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    dec: 014a1a13  slli         x20, x20, 20
    df0: 014a5a13  srli         x20, x20, 20
    df4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_df8:
    df8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    dfc: 000b0463  beq          x22, x0, 0x00000e04  # target 0x00000e04
    e00: ff9ff06f  jal          x0, 0x00000df8  # target 0x00000df8
loc_e04:
    e04: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    e08: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    e0c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    e10: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    e14: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    e18: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    e1c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    e20: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    e24: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    e28: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    e2c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    e30: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    e34: 08000c13  addi         x24, x0, 128  # x24 = 0x00000080
    e38: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000080
    e3c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    e40: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    e44: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    e48: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    e4c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    e50: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    e54: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_e58:
    e58: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    e5c: 000b0463  beq          x22, x0, 0x00000e64  # target 0x00000e64
    e60: ff9ff06f  jal          x0, 0x00000e58  # target 0x00000e58
loc_e64:
    e64: 00008067  jalr         x0, 0(x1)
loc_e68:
    e68: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    e6c: 000aaa03  lw           x20, 0(x21)  # param e2e_k; 0x0000079c
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
loc_eb4:
    eb4: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    eb8: 000aaa03  lw           x20, 0(x21)  # param e2e_v; 0x000007a0
    ebc: 007a7d13  andi         x26, x20, 7
    ec0: ff8a7a13  andi         x20, x20, -8
    ec4: 01af8ab3  add          x21, x31, x26
    ec8: 007afb93  andi         x23, x21, 7
    ecc: 003ada93  srli         x21, x21, 3
    ed0: 00ba9a93  slli         x21, x21, 11
    ed4: 014a8ab3  add          x21, x21, x20
    ed8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ed8
    edc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000ef0
    ee0: 001b9b93  slli         x23, x23, 1
    ee4: 017b0b33  add          x22, x22, x23
    ee8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    eec: 00008067  jalr         x0, 0(x1)
    ef0: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ef4: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ef8: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    efc: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_f00:
    f00: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    f04: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    f08: 007a7d13  andi         x26, x20, 7
    f0c: ff8a7a13  andi         x20, x20, -8
    f10: 01af8ab3  add          x21, x31, x26
    f14: 007afb93  andi         x23, x21, 7
    f18: 003ada93  srli         x21, x21, 3
    f1c: 00ba9a93  slli         x21, x21, 11
    f20: 014a8ab3  add          x21, x21, x20
    f24: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000f24
    f28: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f3c
    f2c: 001b9b93  slli         x23, x23, 1
    f30: 017b0b33  add          x22, x22, x23
    f34: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    f38: 00008067  jalr         x0, 0(x1)
    f3c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f40: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f44: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    f48: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_f4c:
    f4c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    f50: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    f54: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    f58: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    f5c: 015a6463  bltu         x20, x21, 0x00000f64  # target 0x00000f64
    f60: fedff06f  jal          x0, 0x00000f4c  # target 0x00000f4c
loc_f64:
    f64: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    f68: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    f6c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    f70: 014a1a13  slli         x20, x20, 20
    f74: 014a5a13  srli         x20, x20, 20
    f78: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_f7c:
    f7c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    f80: 000b0463  beq          x22, x0, 0x00000f88  # target 0x00000f88
    f84: ff9ff06f  jal          x0, 0x00000f7c  # target 0x00000f7c
loc_f88:
    f88: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    f8c: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    f90: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    f94: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    f98: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    f9c: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    fa0: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    fa4: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    fa8: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    fac: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    fb0: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    fb4: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    fb8: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    fbc: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    fc0: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    fc4: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    fc8: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    fcc: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    fd0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    fd4: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    fd8: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    fdc: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_fe0:
    fe0: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    fe4: 000b0463  beq          x22, x0, 0x00000fec  # target 0x00000fec
    fe8: ff9ff06f  jal          x0, 0x00000fe0  # target 0x00000fe0
loc_fec:
    fec: 00008067  jalr         x0, 0(x1)
loc_ff0:
    ff0: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    ff4: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    ff8: 007a7d13  andi         x26, x20, 7
    ffc: ff8a7a13  andi         x20, x20, -8
   1000: 01af8ab3  add          x21, x31, x26
   1004: 007afb93  andi         x23, x21, 7
   1008: 003ada93  srli         x21, x21, 3
   100c: 00ba9a93  slli         x21, x21, 11
   1010: 014a8ab3  add          x21, x21, x20
   1014: 00000b17  auipc        x22, 0x00000  # x22 = 0x00001014
   1018: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000102c
   101c: 001b9b93  slli         x23, x23, 1
   1020: 017b0b33  add          x22, x22, x23
   1024: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1028: 00008067  jalr         x0, 0(x1)
   102c: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1030: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1034: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
   1038: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_103c:
   103c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
   1040: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
   1044: 007a7d13  andi         x26, x20, 7
   1048: ff8a7a13  andi         x20, x20, -8
   104c: 01af8ab3  add          x21, x31, x26
   1050: 007afb93  andi         x23, x21, 7
   1054: 003ada93  srli         x21, x21, 3
   1058: 00ba9a93  slli         x21, x21, 11
   105c: 014a8ab3  add          x21, x21, x20
   1060: 00000b17  auipc        x22, 0x00000  # x22 = 0x00001060
   1064: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001078
   1068: 001b9b93  slli         x23, x23, 1
   106c: 017b0b33  add          x22, x22, x23
   1070: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1074: 00008067  jalr         x0, 0(x1)
   1078: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
   107c: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1080: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
   1084: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_1088:
   1088: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   108c: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   1090: 007a7d13  andi         x26, x20, 7
   1094: ff8a7a13  andi         x20, x20, -8
   1098: 01af8ab3  add          x21, x31, x26
   109c: 007afb93  andi         x23, x21, 7
   10a0: 003ada93  srli         x21, x21, 3
   10a4: 00ba9a93  slli         x21, x21, 11
   10a8: 014a8ab3  add          x21, x21, x20
   10ac: 00000b17  auipc        x22, 0x00000  # x22 = 0x000010ac
   10b0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000010c4
   10b4: 001b9b93  slli         x23, x23, 1
   10b8: 017b0b33  add          x22, x22, x23
   10bc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   10c0: 00008067  jalr         x0, 0(x1)
   10c4: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   10c8: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   10cc: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
   10d0: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_10d4:
   10d4: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   10d8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   10dc: 007a7d13  andi         x26, x20, 7
   10e0: ff8a7a13  andi         x20, x20, -8
   10e4: 01af8ab3  add          x21, x31, x26
   10e8: 007afb93  andi         x23, x21, 7
   10ec: 003ada93  srli         x21, x21, 3
   10f0: 00ba9a93  slli         x21, x21, 11
   10f4: 014a8ab3  add          x21, x21, x20
   10f8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000010f8
   10fc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001110
   1100: 001b9b93  slli         x23, x23, 1
   1104: 017b0b33  add          x22, x22, x23
   1108: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   110c: 00008067  jalr         x0, 0(x1)
   1110: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
   1114: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1118: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
   111c: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_1120:
   1120: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   1124: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   1128: 007a7d13  andi         x26, x20, 7
   112c: ff8a7a13  andi         x20, x20, -8
   1130: 01af8ab3  add          x21, x31, x26
   1134: 007afb93  andi         x23, x21, 7
   1138: 003ada93  srli         x21, x21, 3
   113c: 00ba9a93  slli         x21, x21, 11
   1140: 014a8ab3  add          x21, x21, x20
   1144: 00000b17  auipc        x22, 0x00000  # x22 = 0x00001144
   1148: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000115c
   114c: 001b9b93  slli         x23, x23, 1
   1150: 017b0b33  add          x22, x22, x23
   1154: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1158: 00008067  jalr         x0, 0(x1)
   115c: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1160: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1164: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   1168: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_116c:
   116c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
   1170: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
   1174: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
   1178: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
   117c: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
   1180: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
   1184: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
   1188: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
   118c: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
   1190: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
   1194: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
   1198: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
   119c: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
   11a0: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
   11a4: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
   11a8: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
   11ac: 020f8f93  addi         x31, x31, 32
   11b0: 020f0f13  addi         x30, x30, 32
   11b4: ff8e8e93  addi         x29, x29, -8
   11b8: fa0e9ae3  bne          x29, x0, 0x0000116c  # target 0x0000116c
   11bc: 00008067  jalr         x0, 0(x1)
   11c0:           j FW_BRISC+4   # return to firmware, linked at install
