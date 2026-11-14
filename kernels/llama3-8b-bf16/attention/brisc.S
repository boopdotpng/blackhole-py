# llama3 8b-bf16 decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 000232b7  lui          x5, 0x00023  # x5 = 0x00023000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x00022800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00022800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     24: 88058593  addi         x11, x11, -1920  # x11 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00014637  lui          x12, 0x00014  # x12 = 0x00014000
     2c: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00014000
     30: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     34: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
     38: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     40: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
     44: 00018637  lui          x12, 0x00018  # x12 = 0x00018000
     48: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00018000
     4c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     50: 88c58593  addi         x11, x11, -1908  # x11 = 0xffb0088c · riscv_local_mem + 0x88c
     54: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     58: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     5c: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
     60: 00025637  lui          x12, 0x00025  # x12 = 0x00025000
     64: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x00025000
     68: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     6c: 89458593  addi         x11, x11, -1900  # x11 = 0xffb00894 · riscv_local_mem + 0x894
     70: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     74: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     78: 89848493  addi         x9, x9, -1896  # x9 = 0xffb00898 · riscv_local_mem + 0x898
     7c: 00026537  lui          x10, 0x00026  # x10 = 0x00026000
     80: 90050513  addi         x10, x10, -1792  # x10 = 0x00025900
     84: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x00025900
     88: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     8c: 89c48493  addi         x9, x9, -1892  # x9 = 0xffb0089c · riscv_local_mem + 0x89c
     90: 0004a023  sw           x0, 0(x9)  # riscv_local_mem + 0x89c · 0xffb0089c; write 0x00000000
     94: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     98: 90430313  addi         x6, x6, -1788  # x6 = 0x00011904
     9c: 00032203  lw           x4, 0(x6)  # param attention_phase; 0x00011904
     a0: 79000413  addi         x8, x0, 1936  # x8 = 0x00000790
     a4: 00042303  lw           x6, 0(x8)  # param kv_blocks; 0x00000790
     a8: 00100293  addi         x5, x0, 1  # x5 = 0x00000001
     ac: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
     b0: 0063fa63  bgeu         x7, x6, 0x000000c4  # target 0x000000c4
     b4: 00400293  addi         x5, x0, 4  # x5 = 0x00000004
     b8: 05000393  addi         x7, x0, 80  # x7 = 0x00000050
     bc: 0063f463  bgeu         x7, x6, 0x000000c4  # target 0x000000c4
     c0: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
loc_c4:
     c4: 325274e3  bgeu         x4, x5, 0x00000bec  # target 0x00000bec
     c8: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     cc: 90028293  addi         x5, x5, -1792  # x5 = 0x00011900
     d0: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x00011900
     d4: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
     d8: 02525233  divu         x4, x4, x5
     dc: 315000ef  jal          x1, 0x00000bf0  # target 0x00000bf0; x1 = 0x000000e0
     e0: 32d000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x000000e4
     e4: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     e8: 0003a283  lw           x5, 0(x7)  # param start_pos; 0x000007ac
     ec: 0072f313  andi         x6, x5, 7
     f0: 00831313  slli         x6, x6, 8
     f4: 0032d293  srli         x5, x5, 3
     f8: 00028f93  addi         x31, x5, 0
     fc: 32d000ef  jal          x1, 0x00000c28  # target 0x00000c28; x1 = 0x00000100
    100: 000a8393  addi         x7, x21, 0
    104: 000b0413  addi         x8, x22, 0
    108: 006383b3  add          x7, x7, x6
    10c: 00038f93  addi         x31, x7, 0
    110: 00040f13  addi         x30, x8, 0
    114: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    118: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00023800
    11c: 359000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x00000120
    120: 00038f93  addi         x31, x7, 0
    124: 00040f13  addi         x30, x8, 0
    128: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    12c: 900e8e93  addi         x29, x29, -1792  # x29 = 0x00023900
    130: 345000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x00000134
    134: 00038f93  addi         x31, x7, 0
    138: 00040f13  addi         x30, x8, 0
    13c: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    140: a00e8e93  addi         x29, x29, -1536  # x29 = 0x00023a00
    144: 331000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x00000148
    148: 00038f93  addi         x31, x7, 0
    14c: 00040f13  addi         x30, x8, 0
    150: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    154: b00e8e93  addi         x29, x29, -1280  # x29 = 0x00023b00
    158: 31d000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x0000015c
    15c: 00038f93  addi         x31, x7, 0
    160: 00040f13  addi         x30, x8, 0
    164: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    168: c00e8e93  addi         x29, x29, -1024  # x29 = 0x00023c00
    16c: 309000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x00000170
    170: 00028f93  addi         x31, x5, 0
    174: 3a1000ef  jal          x1, 0x00000d14  # target 0x00000d14; x1 = 0x00000178
    178: 000a8393  addi         x7, x21, 0
    17c: 000b0413  addi         x8, x22, 0
    180: 006383b3  add          x7, x7, x6
    184: 00038f93  addi         x31, x7, 0
    188: 00040f13  addi         x30, x8, 0
    18c: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    190: 2e5000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x00000194
    194: 00038f93  addi         x31, x7, 0
    198: 00040f13  addi         x30, x8, 0
    19c: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1a0: 100e8e93  addi         x29, x29, 256  # x29 = 0x00024100
    1a4: 2d1000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x000001a8
    1a8: 00038f93  addi         x31, x7, 0
    1ac: 00040f13  addi         x30, x8, 0
    1b0: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1b4: 200e8e93  addi         x29, x29, 512  # x29 = 0x00024200
    1b8: 2bd000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x000001bc
    1bc: 00038f93  addi         x31, x7, 0
    1c0: 00040f13  addi         x30, x8, 0
    1c4: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1c8: 300e8e93  addi         x29, x29, 768  # x29 = 0x00024300
    1cc: 2a9000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x000001d0
    1d0: 00038f93  addi         x31, x7, 0
    1d4: 00040f13  addi         x30, x8, 0
    1d8: 00024eb7  lui          x29, 0x00024  # x29 = 0x00024000
    1dc: 400e8e93  addi         x29, x29, 1024  # x29 = 0x00024400
    1e0: 295000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x000001e4
    1e4: 00921293  slli         x5, x4, 9
    1e8: 3ff2f313  andi         x6, x5, 1023
    1ec: 00131313  slli         x6, x6, 1
    1f0: 00a2d293  srli         x5, x5, 10
    1f4: 00028f93  addi         x31, x5, 0
    1f8: 369000ef  jal          x1, 0x00000d60  # target 0x00000d60; x1 = 0x000001fc
    1fc: 000a8393  addi         x7, x21, 0
    200: 000b0413  addi         x8, x22, 0
    204: 006383b3  add          x7, x7, x6
    208: 00038f93  addi         x31, x7, 0
    20c: 00040f13  addi         x30, x8, 0
    210: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    214: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00022800
loc_218:
    218: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    21c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    220: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    224: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    228: 015a6463  bltu         x20, x21, 0x00000230  # target 0x00000230
    22c: fedff06f  jal          x0, 0x00000218  # target 0x00000218
loc_230:
    230: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    234: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    238: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    23c: 014a1a13  slli         x20, x20, 20
    240: 014a5a13  srli         x20, x20, 20
    244: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_248:
    248: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    24c: 000b0463  beq          x22, x0, 0x00000254  # target 0x00000254
    250: ff9ff06f  jal          x0, 0x00000248  # target 0x00000248
loc_254:
    254: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    258: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    25c: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    260: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    264: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x00022800
    268: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    26c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    270: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    274: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    278: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    27c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    280: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    284: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    288: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000400
    28c: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    290: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    294: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    298: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    29c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    2a0: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    2a4: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_2a8:
    2a8: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    2ac: 000b0463  beq          x22, x0, 0x000002b4  # target 0x000002b4
    2b0: ff9ff06f  jal          x0, 0x000002a8  # target 0x000002a8
loc_2b4:
    2b4: 08038493  addi         x9, x7, 128
    2b8: 00048f93  addi         x31, x9, 0
    2bc: 00040f13  addi         x30, x8, 0
    2c0: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    2c4: 2e9000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x000002c8
    2c8: 00038f93  addi         x31, x7, 0
    2cc: 00040f13  addi         x30, x8, 0
    2d0: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    2d4: 080e8e93  addi         x29, x29, 128  # x29 = 0x00023080
    2d8: 2d5000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x000002dc
    2dc: 18038493  addi         x9, x7, 384
    2e0: 00048f93  addi         x31, x9, 0
    2e4: 00040f13  addi         x30, x8, 0
    2e8: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    2ec: 100e8e93  addi         x29, x29, 256  # x29 = 0x00023100
    2f0: 2bd000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x000002f4
    2f4: 10038493  addi         x9, x7, 256
    2f8: 00048f93  addi         x31, x9, 0
    2fc: 00040f13  addi         x30, x8, 0
    300: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    304: 180e8e93  addi         x29, x29, 384  # x29 = 0x00023180
    308: 2a5000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x0000030c
    30c: 28038493  addi         x9, x7, 640
    310: 00048f93  addi         x31, x9, 0
    314: 00040f13  addi         x30, x8, 0
    318: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    31c: 200e8e93  addi         x29, x29, 512  # x29 = 0x00023200
    320: 28d000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x00000324
    324: 20038493  addi         x9, x7, 512
    328: 00048f93  addi         x31, x9, 0
    32c: 00040f13  addi         x30, x8, 0
    330: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    334: 280e8e93  addi         x29, x29, 640  # x29 = 0x00023280
    338: 275000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x0000033c
    33c: 38038493  addi         x9, x7, 896
    340: 00048f93  addi         x31, x9, 0
    344: 00040f13  addi         x30, x8, 0
    348: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    34c: 300e8e93  addi         x29, x29, 768  # x29 = 0x00023300
    350: 25d000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x00000354
    354: 30038493  addi         x9, x7, 768
    358: 00048f93  addi         x31, x9, 0
    35c: 00040f13  addi         x30, x8, 0
    360: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    364: 380e8e93  addi         x29, x29, 896  # x29 = 0x00023380
    368: 245000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x0000036c
    36c: 00221293  slli         x5, x4, 2
    370: 0022d293  srli         x5, x5, 2
    374: 00729293  slli         x5, x5, 7
    378: 3ff2f313  andi         x6, x5, 1023
    37c: 00131313  slli         x6, x6, 1
    380: 00a2d293  srli         x5, x5, 10
    384: 00028f93  addi         x31, x5, 0
    388: 2c5000ef  jal          x1, 0x00000e4c  # target 0x00000e4c; x1 = 0x0000038c
    38c: 000a8393  addi         x7, x21, 0
    390: 000b0413  addi         x8, x22, 0
    394: 006383b3  add          x7, x7, x6
    398: 00038f93  addi         x31, x7, 0
    39c: 00040f13  addi         x30, x8, 0
    3a0: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    3a4: c00e8e93  addi         x29, x29, -1024  # x29 = 0x00022c00
    3a8: 0cd000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x000003ac
    3ac: 08038493  addi         x9, x7, 128
    3b0: 00048f93  addi         x31, x9, 0
    3b4: 00040f13  addi         x30, x8, 0
    3b8: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    3bc: 400e8e93  addi         x29, x29, 1024  # x29 = 0x00023400
    3c0: 1ed000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x000003c4
    3c4: 00038f93  addi         x31, x7, 0
    3c8: 00040f13  addi         x30, x8, 0
    3cc: 00023eb7  lui          x29, 0x00023  # x29 = 0x00023000
    3d0: 480e8e93  addi         x29, x29, 1152  # x29 = 0x00023480
    3d4: 1d9000ef  jal          x1, 0x00000dac  # target 0x00000dac; x1 = 0x000003d8
    3d8: 00221293  slli         x5, x4, 2
    3dc: 0022d293  srli         x5, x5, 2
    3e0: 00729293  slli         x5, x5, 7
    3e4: 3ff2f313  andi         x6, x5, 1023
    3e8: 00131313  slli         x6, x6, 1
    3ec: 00a2d293  srli         x5, x5, 10
    3f0: 00028f93  addi         x31, x5, 0
    3f4: 2a5000ef  jal          x1, 0x00000e98  # target 0x00000e98; x1 = 0x000003f8
    3f8: 000a8393  addi         x7, x21, 0
    3fc: 000b0413  addi         x8, x22, 0
    400: 006383b3  add          x7, x7, x6
    404: 00038f93  addi         x31, x7, 0
    408: 00040f13  addi         x30, x8, 0
    40c: 00026eb7  lui          x29, 0x00026  # x29 = 0x00026000
    410: 800e8e93  addi         x29, x29, -2048  # x29 = 0x00025800
    414: 061000ef  jal          x1, 0x00000c74  # target 0x00000c74; x1 = 0x00000418
    418: 7f4000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x0000041c
    41c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    420: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    424: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    428: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    42c: 00520233  add          x4, x4, x5
    430: 00025337  lui          x6, 0x00025  # x6 = 0x00025000
    434: 80030313  addi         x6, x6, -2048  # x6 = 0x00024800
    438: 00626663  bltu         x4, x6, 0x00000444  # target 0x00000444
    43c: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    440: 40720233  sub          x4, x4, x7
loc_444:
    444: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    448: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    44c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    450: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    454: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    458: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c
    45c: 00420213  addi         x4, x4, 4
    460: 01021213  slli         x4, x4, 16
    464: 01025213  srli         x4, x4, 16
    468: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    46c: 87c28293  addi         x5, x5, -1924  # x5 = 0xffb0087c · riscv_local_mem + 0x87c
    470: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x87c · 0xffb0087c; write runtime value
    474: ffb4d2b7  lui          x5, 0xffb4d  # x5 = 0xffb4d000
    478: 02828293  addi         x5, x5, 40  # x5 = 0xffb4d028
    47c: 0042a023  sw           x4, 0(x5)  # 0xffb4d028; write runtime value
    480: 0ff0000f  fence        0xf, 0xf
    484: 000123b7  lui          x7, 0x00012  # x7 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    488: 90038393  addi         x7, x7, -1792  # x7 = 0x00011900
    48c: 0003a203  lw           x4, 0(x7)  # param attention_core; 0x00011900
    490: 00800393  addi         x7, x0, 8  # x7 = 0x00000008
    494: 02725233  divu         x4, x4, x7
    498: 79000393  addi         x7, x0, 1936  # x7 = 0x00000790
    49c: 0003a283  lw           x5, 0(x7)  # param kv_blocks; 0x00000790
    4a0: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    4a4: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    4a8: 00100313  addi         x6, x0, 1  # x6 = 0x00000001
    4ac: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    4b0: 00747a63  bgeu         x8, x7, 0x000004c4  # target 0x000004c4
    4b4: 00400313  addi         x6, x0, 4  # x6 = 0x00000004
    4b8: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    4bc: 00747463  bgeu         x8, x7, 0x000004c4  # target 0x000004c4
    4c0: 00800313  addi         x6, x0, 8  # x6 = 0x00000008
loc_4c4:
    4c4: 000124b7  lui          x9, 0x00012  # x9 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    4c8: 90448493  addi         x9, x9, -1788  # x9 = 0x00011904
    4cc: 0004a383  lw           x7, 0(x9)  # param attention_phase; 0x00011904
    4d0: 79000593  addi         x11, x0, 1936  # x11 = 0x00000790
    4d4: 0005a483  lw           x9, 0(x11)  # param kv_blocks; 0x00000790
    4d8: 00100413  addi         x8, x0, 1  # x8 = 0x00000001
    4dc: 00400513  addi         x10, x0, 4  # x10 = 0x00000004
    4e0: 00957a63  bgeu         x10, x9, 0x000004f4  # target 0x000004f4
    4e4: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    4e8: 05000513  addi         x10, x0, 80  # x10 = 0x00000050
    4ec: 00957463  bgeu         x10, x9, 0x000004f4  # target 0x000004f4
    4f0: 00800413  addi         x8, x0, 8  # x8 = 0x00000008
loc_4f4:
    4f4: 008282b3  add          x5, x5, x8
    4f8: fff28293  addi         x5, x5, -1
    4fc: 407282b3  sub          x5, x5, x7
    500: 0282d2b3  divu         x5, x5, x8
    504: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    508: 00028413  addi         x8, x5, 0
loc_50c:
    50c: 6083fa63  bgeu         x7, x8, 0x00000b20  # target 0x00000b20
    510: 00025493  srli         x9, x4, 0
    514: 00a49493  slli         x9, x9, 10
    518: 02638533  mul          x10, x7, x6
    51c: 00012637  lui          x12, 0x00012  # x12 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    520: 90460613  addi         x12, x12, -1788  # x12 = 0x00011904
    524: 00062583  lw           x11, 0(x12)  # param attention_phase; 0x00011904
    528: 00b50533  add          x10, x10, x11
    52c: 79000613  addi         x12, x0, 1936  # x12 = 0x00000790
    530: 00062583  lw           x11, 0(x12)  # param kv_blocks; 0x00000790
    534: fff58593  addi         x11, x11, -1
    538: 40b505b3  sub          x11, x10, x11
    53c: 00251513  slli         x10, x10, 2
    540: 00a484b3  add          x9, x9, x10
    544: 00058513  addi         x10, x11, 0
    548: 6a8000ef  jal          x1, 0x00000bf0  # target 0x00000bf0; x1 = 0x0000054c
    54c: 6c0000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x00000550
    550: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    554: 88480813  addi         x16, x16, -1916  # x16 = 0xffb00884 · riscv_local_mem + 0x884
    558: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x884 · 0xffb00884
loc_55c:
    55c: ffb49837  lui          x16, 0xffb49  # x16 = 0xffb49000
    560: 02080813  addi         x16, x16, 32  # x16 = 0xffb49020
    564: 00085603  lhu          x12, 0(x16)  # 0xffb49020
    568: 40c586b3  sub          x13, x11, x12
    56c: 01069693  slli         x13, x13, 16
    570: 0106d693  srli         x13, x13, 16
    574: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    578: 40d70733  sub          x14, x14, x13
    57c: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    580: 00f77663  bgeu         x14, x15, 0x0000058c  # target 0x0000058c
    584: 0ff0000f  fence        0xf, 0xf
    588: fd5ff06f  jal          x0, 0x0000055c  # target 0x0000055c
loc_58c:
    58c: 0ff0000f  fence        0xf, 0xf
    590: 00048593  addi         x11, x9, 0
    594: 00058f93  addi         x31, x11, 0
    598: 14d000ef  jal          x1, 0x00000ee4  # target 0x00000ee4; x1 = 0x0000059c
    59c: 000a8613  addi         x12, x21, 0
    5a0: 000b0693  addi         x13, x22, 0
    5a4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    5a8: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    5ac: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    5b0: 00060f93  addi         x31, x12, 0
    5b4: 00068f13  addi         x30, x13, 0
    5b8: 00070e93  addi         x29, x14, 0
    5bc: 175000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x000005c0
    5c0: 00148593  addi         x11, x9, 1
    5c4: 00058f93  addi         x31, x11, 0
    5c8: 20d000ef  jal          x1, 0x00000fd4  # target 0x00000fd4; x1 = 0x000005cc
    5cc: 000a8613  addi         x12, x21, 0
    5d0: 000b0693  addi         x13, x22, 0
    5d4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    5d8: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    5dc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    5e0: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5e4: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    5e8: 00f70733  add          x14, x14, x15
    5ec: 00060f93  addi         x31, x12, 0
    5f0: 00068f13  addi         x30, x13, 0
    5f4: 00070e93  addi         x29, x14, 0
    5f8: 139000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x000005fc
    5fc: 00248593  addi         x11, x9, 2
    600: 00058f93  addi         x31, x11, 0
    604: 21d000ef  jal          x1, 0x00001020  # target 0x00001020; x1 = 0x00000608
    608: 000a8613  addi         x12, x21, 0
    60c: 000b0693  addi         x13, x22, 0
    610: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    614: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    618: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    61c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    620: 00f70733  add          x14, x14, x15
    624: 00060f93  addi         x31, x12, 0
    628: 00068f13  addi         x30, x13, 0
    62c: 00070e93  addi         x29, x14, 0
    630: 101000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x00000634
    634: 00348593  addi         x11, x9, 3
    638: 00058f93  addi         x31, x11, 0
    63c: 0a9000ef  jal          x1, 0x00000ee4  # target 0x00000ee4; x1 = 0x00000640
    640: 000a8613  addi         x12, x21, 0
    644: 000b0693  addi         x13, x22, 0
    648: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    64c: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    650: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    654: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    658: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    65c: 00f70733  add          x14, x14, x15
    660: 00060f93  addi         x31, x12, 0
    664: 00068f13  addi         x30, x13, 0
    668: 00070e93  addi         x29, x14, 0
    66c: 0c5000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x00000670
    670: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    674: 88c80813  addi         x16, x16, -1908  # x16 = 0xffb0088c · riscv_local_mem + 0x88c
    678: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_67c:
    67c: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    680: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    684: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    688: 40c586b3  sub          x13, x11, x12
    68c: 01069693  slli         x13, x13, 16
    690: 0106d693  srli         x13, x13, 16
    694: 00800713  addi         x14, x0, 8  # x14 = 0x00000008
    698: 40d70733  sub          x14, x14, x13
    69c: 00400793  addi         x15, x0, 4  # x15 = 0x00000004
    6a0: 00f77663  bgeu         x14, x15, 0x000006ac  # target 0x000006ac
    6a4: 0ff0000f  fence        0xf, 0xf
    6a8: fd5ff06f  jal          x0, 0x0000067c  # target 0x0000067c
loc_6ac:
    6ac: 0ff0000f  fence        0xf, 0xf
    6b0: 00048593  addi         x11, x9, 0
    6b4: 00058f93  addi         x31, x11, 0
    6b8: 1b5000ef  jal          x1, 0x0000106c  # target 0x0000106c; x1 = 0x000006bc
    6bc: 000a8613  addi         x12, x21, 0
    6c0: 000b0693  addi         x13, x22, 0
    6c4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    6c8: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    6cc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    6d0: 00060f93  addi         x31, x12, 0
    6d4: 00068f13  addi         x30, x13, 0
    6d8: 00070e93  addi         x29, x14, 0
    6dc: 055000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x000006e0
    6e0: 00148593  addi         x11, x9, 1
    6e4: 00058f93  addi         x31, x11, 0
    6e8: 1d1000ef  jal          x1, 0x000010b8  # target 0x000010b8; x1 = 0x000006ec
    6ec: 000a8613  addi         x12, x21, 0
    6f0: 000b0693  addi         x13, x22, 0
    6f4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    6f8: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    6fc: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    700: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    704: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    708: 00f70733  add          x14, x14, x15
    70c: 00060f93  addi         x31, x12, 0
    710: 00068f13  addi         x30, x13, 0
    714: 00070e93  addi         x29, x14, 0
    718: 019000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x0000071c
    71c: 00248593  addi         x11, x9, 2
    720: 00058f93  addi         x31, x11, 0
    724: 1e1000ef  jal          x1, 0x00001104  # target 0x00001104; x1 = 0x00000728
    728: 000a8613  addi         x12, x21, 0
    72c: 000b0693  addi         x13, x22, 0
    730: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    734: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    738: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    73c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    740: 00f70733  add          x14, x14, x15
    744: 00060f93  addi         x31, x12, 0
    748: 00068f13  addi         x30, x13, 0
    74c: 00070e93  addi         x29, x14, 0
    750: 7e0000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x00000754
    754: 00348593  addi         x11, x9, 3
    758: 00058f93  addi         x31, x11, 0
    75c: 111000ef  jal          x1, 0x0000106c  # target 0x0000106c; x1 = 0x00000760
    760: 000a8613  addi         x12, x21, 0
    764: 000b0693  addi         x13, x22, 0
    768: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    76c: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    770: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    774: 000027b7  lui          x15, 0x00002  # x15 = 0x00002000
    778: 80078793  addi         x15, x15, -2048  # x15 = 0x00001800
    77c: 00f70733  add          x14, x14, x15
    780: 00060f93  addi         x31, x12, 0
    784: 00068f13  addi         x30, x13, 0
    788: 00070e93  addi         x29, x14, 0
    78c: 7a4000ef  jal          x1, 0x00000f30  # target 0x00000f30; x1 = 0x00000790
    790: 47c000ef  jal          x1, 0x00000c0c  # target 0x00000c0c; x1 = 0x00000794
    794: 2a051e63  bne          x10, x0, 0x00000a50  # target 0x00000a50
    798: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    79c: 89478793  addi         x15, x15, -1900  # x15 = 0xffb00894 · riscv_local_mem + 0x894
    7a0: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x894 · 0xffb00894
    7a4: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
loc_7a8:
    7a8: ffb4f7b7  lui          x15, 0xffb4f  # x15 = 0xffb4f000
    7ac: 02878793  addi         x15, x15, 40  # x15 = 0xffb4f028
    7b0: 0007d603  lhu          x12, 0(x15)  # 0xffb4f028
    7b4: 40b606b3  sub          x13, x12, x11
    7b8: 01069693  slli         x13, x13, 16
    7bc: 0106d693  srli         x13, x13, 16
    7c0: 00e6f663  bgeu         x13, x14, 0x000007cc  # target 0x000007cc
    7c4: 0ff0000f  fence        0xf, 0xf
    7c8: fe1ff06f  jal          x0, 0x000007a8  # target 0x000007a8
loc_7cc:
    7cc: 0ff0000f  fence        0xf, 0xf
    7d0: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    7d4: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    7d8: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    7dc: 7ac00793  addi         x15, x0, 1964  # x15 = 0x000007ac
    7e0: 0007a603  lw           x12, 0(x15)  # param start_pos; 0x000007ac
    7e4: 01067793  andi         x15, x12, 16
    7e8: 00679793  slli         x15, x15, 6
    7ec: 00f67613  andi         x12, x12, 15
    7f0: 00561613  slli         x12, x12, 5
    7f4: 00f60633  add          x12, x12, x15
    7f8: 00b60633  add          x12, x12, x11
    7fc: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    800: c0070713  addi         x14, x14, -1024  # x14 = 0x00024c00
    804: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    808: 00c686b3  add          x13, x13, x12
    80c: 00070f93  addi         x31, x14, 0  # x31 = 0x00024c00
    810: 00068f13  addi         x30, x13, 0
    814: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    818: 139000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x0000081c
    81c: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    820: c2070713  addi         x14, x14, -992  # x14 = 0x00024c20
    824: 20000693  addi         x13, x0, 512  # x13 = 0x00000200
    828: 00c686b3  add          x13, x13, x12
    82c: 00070f93  addi         x31, x14, 0  # x31 = 0x00024c20
    830: 00068f13  addi         x30, x13, 0
    834: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    838: 119000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x0000083c
    83c: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    840: c4070713  addi         x14, x14, -960  # x14 = 0x00024c40
    844: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    848: 80068693  addi         x13, x13, -2048  # x13 = 0x00000800
    84c: 00c686b3  add          x13, x13, x12
    850: 00070f93  addi         x31, x14, 0  # x31 = 0x00024c40
    854: 00068f13  addi         x30, x13, 0
    858: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    85c: 0f5000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x00000860
    860: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    864: c6070713  addi         x14, x14, -928  # x14 = 0x00024c60
    868: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    86c: a0068693  addi         x13, x13, -1536  # x13 = 0x00000a00
    870: 00c686b3  add          x13, x13, x12
    874: 00070f93  addi         x31, x14, 0  # x31 = 0x00024c60
    878: 00068f13  addi         x30, x13, 0
    87c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    880: 0d1000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x00000884
    884: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    888: c8070713  addi         x14, x14, -896  # x14 = 0x00024c80
    88c: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    890: 00c686b3  add          x13, x13, x12
    894: 00070f93  addi         x31, x14, 0  # x31 = 0x00024c80
    898: 00068f13  addi         x30, x13, 0
    89c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    8a0: 0b1000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x000008a4
    8a4: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    8a8: ca070713  addi         x14, x14, -864  # x14 = 0x00024ca0
    8ac: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8b0: 20068693  addi         x13, x13, 512  # x13 = 0x00001200
    8b4: 00c686b3  add          x13, x13, x12
    8b8: 00070f93  addi         x31, x14, 0  # x31 = 0x00024ca0
    8bc: 00068f13  addi         x30, x13, 0
    8c0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    8c4: 08d000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x000008c8
    8c8: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    8cc: cc070713  addi         x14, x14, -832  # x14 = 0x00024cc0
    8d0: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    8d4: 80068693  addi         x13, x13, -2048  # x13 = 0x00001800
    8d8: 00c686b3  add          x13, x13, x12
    8dc: 00070f93  addi         x31, x14, 0  # x31 = 0x00024cc0
    8e0: 00068f13  addi         x30, x13, 0
    8e4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    8e8: 069000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x000008ec
    8ec: 00025737  lui          x14, 0x00025  # x14 = 0x00025000
    8f0: ce070713  addi         x14, x14, -800  # x14 = 0x00024ce0
    8f4: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    8f8: a0068693  addi         x13, x13, -1536  # x13 = 0x00001a00
    8fc: 00c686b3  add          x13, x13, x12
    900: 00070f93  addi         x31, x14, 0  # x31 = 0x00024ce0
    904: 00068f13  addi         x30, x13, 0
    908: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    90c: 045000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x00000910
    910: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    914: 88860613  addi         x12, x12, -1912  # x12 = 0xffb00888 · riscv_local_mem + 0x888
    918: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x888 · 0xffb00888
    91c: 7ac00793  addi         x15, x0, 1964  # x15 = 0x000007ac
    920: 0007a603  lw           x12, 0(x15)  # param start_pos; 0x000007ac
    924: 01067793  andi         x15, x12, 16
    928: 00679793  slli         x15, x15, 6
    92c: 00f67613  andi         x12, x12, 15
    930: 00561613  slli         x12, x12, 5
    934: 00f60633  add          x12, x12, x15
    938: 00b60633  add          x12, x12, x11
    93c: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    940: 80070713  addi         x14, x14, -2048  # x14 = 0x00025800
    944: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    948: 00c686b3  add          x13, x13, x12
    94c: 00070f93  addi         x31, x14, 0  # x31 = 0x00025800
    950: 00068f13  addi         x30, x13, 0
    954: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    958: 7f8000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x0000095c
    95c: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    960: 82070713  addi         x14, x14, -2016  # x14 = 0x00025820
    964: 20000693  addi         x13, x0, 512  # x13 = 0x00000200
    968: 00c686b3  add          x13, x13, x12
    96c: 00070f93  addi         x31, x14, 0  # x31 = 0x00025820
    970: 00068f13  addi         x30, x13, 0
    974: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    978: 7d8000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x0000097c
    97c: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    980: 84070713  addi         x14, x14, -1984  # x14 = 0x00025840
    984: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    988: 80068693  addi         x13, x13, -2048  # x13 = 0x00000800
    98c: 00c686b3  add          x13, x13, x12
    990: 00070f93  addi         x31, x14, 0  # x31 = 0x00025840
    994: 00068f13  addi         x30, x13, 0
    998: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    99c: 7b4000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x000009a0
    9a0: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    9a4: 86070713  addi         x14, x14, -1952  # x14 = 0x00025860
    9a8: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9ac: a0068693  addi         x13, x13, -1536  # x13 = 0x00000a00
    9b0: 00c686b3  add          x13, x13, x12
    9b4: 00070f93  addi         x31, x14, 0  # x31 = 0x00025860
    9b8: 00068f13  addi         x30, x13, 0
    9bc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    9c0: 790000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x000009c4
    9c4: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    9c8: 88070713  addi         x14, x14, -1920  # x14 = 0x00025880
    9cc: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9d0: 00c686b3  add          x13, x13, x12
    9d4: 00070f93  addi         x31, x14, 0  # x31 = 0x00025880
    9d8: 00068f13  addi         x30, x13, 0
    9dc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    9e0: 770000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x000009e4
    9e4: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    9e8: 8a070713  addi         x14, x14, -1888  # x14 = 0x000258a0
    9ec: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    9f0: 20068693  addi         x13, x13, 512  # x13 = 0x00001200
    9f4: 00c686b3  add          x13, x13, x12
    9f8: 00070f93  addi         x31, x14, 0  # x31 = 0x000258a0
    9fc: 00068f13  addi         x30, x13, 0
    a00: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    a04: 74c000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x00000a08
    a08: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    a0c: 8c070713  addi         x14, x14, -1856  # x14 = 0x000258c0
    a10: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    a14: 80068693  addi         x13, x13, -2048  # x13 = 0x00001800
    a18: 00c686b3  add          x13, x13, x12
    a1c: 00070f93  addi         x31, x14, 0  # x31 = 0x000258c0
    a20: 00068f13  addi         x30, x13, 0
    a24: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    a28: 728000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x00000a2c
    a2c: 00026737  lui          x14, 0x00026  # x14 = 0x00026000
    a30: 8e070713  addi         x14, x14, -1824  # x14 = 0x000258e0
    a34: 000026b7  lui          x13, 0x00002  # x13 = 0x00002000
    a38: a0068693  addi         x13, x13, -1536  # x13 = 0x00001a00
    a3c: 00c686b3  add          x13, x13, x12
    a40: 00070f93  addi         x31, x14, 0  # x31 = 0x000258e0
    a44: 00068f13  addi         x30, x13, 0
    a48: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    a4c: 704000ef  jal          x1, 0x00001150  # target 0x00001150; x1 = 0x00000a50
loc_a50:
    a50: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a54: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    a58: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    a5c: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    a60: 00c585b3  add          x11, x11, x12
    a64: 000186b7  lui          x13, 0x00018  # x13 = 0x00018000
    a68: 00d5e663  bltu         x11, x13, 0x00000a74  # target 0x00000a74
    a6c: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    a70: 40e585b3  sub          x11, x11, x14
loc_a74:
    a74: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    a78: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    a7c: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    a80: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    a84: 88460613  addi         x12, x12, -1916  # x12 = 0xffb00884 · riscv_local_mem + 0x884
    a88: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x884 · 0xffb00884
    a8c: 00458593  addi         x11, x11, 4
    a90: 01059593  slli         x11, x11, 16
    a94: 0105d593  srli         x11, x11, 16
    a98: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    a9c: 88460613  addi         x12, x12, -1916  # x12 = 0xffb00884 · riscv_local_mem + 0x884
    aa0: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    aa4: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    aa8: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    aac: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    ab0: 0ff0000f  fence        0xf, 0xf
    ab4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    ab8: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    abc: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    ac0: 00002637  lui          x12, 0x00002  # x12 = 0x00002000
    ac4: 00c585b3  add          x11, x11, x12
    ac8: 0001c6b7  lui          x13, 0x0001c  # x13 = 0x0001c000
    acc: 00d5e663  bltu         x11, x13, 0x00000ad8  # target 0x00000ad8
    ad0: 00004737  lui          x14, 0x00004  # x14 = 0x00004000
    ad4: 40e585b3  sub          x11, x11, x14
loc_ad8:
    ad8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    adc: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    ae0: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    ae4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    ae8: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    aec: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
    af0: 00458593  addi         x11, x11, 4
    af4: 01059593  slli         x11, x11, 16
    af8: 0105d593  srli         x11, x11, 16
    afc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    b00: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    b04: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    b08: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    b0c: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    b10: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    b14: 0ff0000f  fence        0xf, 0xf
    b18: 00138393  addi         x7, x7, 1
    b1c: 9f1ff06f  jal          x0, 0x0000050c  # target 0x0000050c
loc_b20:
    b20: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b24: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    b28: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    b2c: 0c021063  bne          x4, x0, 0x00000bec  # target 0x00000bec
    b30: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    b34: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    b38: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    b3c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    b40: 00747a63  bgeu         x8, x7, 0x00000b54  # target 0x00000b54
    b44: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    b48: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    b4c: 00747463  bgeu         x8, x7, 0x00000b54  # target 0x00000b54
    b50: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_b54:
    b54: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    b58: fc030313  addi         x6, x6, -64  # x6 = 0x00011fc0
loc_b5c:
    b5c: 00032283  lw           x5, 0(x6)  # 0x00011fc0
    b60: 00428663  beq          x5, x4, 0x00000b6c  # target 0x00000b6c
    b64: 0ff0000f  fence        0xf, 0xf
    b68: ff5ff06f  jal          x0, 0x00000b5c  # target 0x00000b5c
loc_b6c:
    b6c: 00032023  sw           x0, 0(x6)  # 0x00011fc0; write 0x00000000
    b70: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    b74: 00020413  addi         x8, x4, 0
loc_b78:
    b78: 0683fa63  bgeu         x7, x8, 0x00000bec  # target 0x00000bec
    b7c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    b80: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    b84: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    b88: 00006537  lui          x10, 0x00006  # x10 = 0x00006000
    b8c: 00a484b3  add          x9, x9, x10
    b90: 000565b7  lui          x11, 0x00056  # x11 = 0x00056000
    b94: 90058593  addi         x11, x11, -1792  # x11 = 0x00055900
    b98: 00b4e663  bltu         x9, x11, 0x00000ba4  # target 0x00000ba4
    b9c: 00030637  lui          x12, 0x00030  # x12 = 0x00030000 · arc_apb_reset_unit + 0x0
    ba0: 40c484b3  sub          x9, x9, x12
loc_ba4:
    ba4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    ba8: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    bac: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    bb0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    bb4: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    bb8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    bbc: 00648493  addi         x9, x9, 6
    bc0: 01049493  slli         x9, x9, 16
    bc4: 0104d493  srli         x9, x9, 16
    bc8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    bcc: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    bd0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    bd4: ffb50537  lui          x10, 0xffb50  # x10 = 0xffb50000
    bd8: 02850513  addi         x10, x10, 40  # x10 = 0xffb50028
    bdc: 00952023  sw           x9, 0(x10)  # 0xffb50028; write runtime value
    be0: 0ff0000f  fence        0xf, 0xf
    be4: 00138393  addi         x7, x7, 1
    be8: f91ff06f  jal          x0, 0x00000b78  # target 0x00000b78
loc_bec:
    bec: 5b80006f  jal          x0, 0x000011a4  # target 0x000011a4
loc_bf0:
    bf0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bf4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    bf8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    bfc: 000a0463  beq          x20, x0, 0x00000c04  # target 0x00000c04
    c00: ff1ff06f  jal          x0, 0x00000bf0  # target 0x00000bf0
loc_c04:
    c04: 0ff0000f  fence        0xf, 0xf
    c08: 00008067  jalr         x0, 0(x1)
loc_c0c:
    c0c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c10: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c14: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c18: 000a0463  beq          x20, x0, 0x00000c20  # target 0x00000c20
    c1c: ff1ff06f  jal          x0, 0x00000c0c  # target 0x00000c0c
loc_c20:
    c20: 0ff0000f  fence        0xf, 0xf
    c24: 00008067  jalr         x0, 0(x1)
loc_c28:
    c28: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    c2c: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    c30: 007a7d13  andi         x26, x20, 7
    c34: ff8a7a13  andi         x20, x20, -8
    c38: 01af8ab3  add          x21, x31, x26
    c3c: 007afb93  andi         x23, x21, 7
    c40: 003ada93  srli         x21, x21, 3
    c44: 00ba9a93  slli         x21, x21, 11
    c48: 014a8ab3  add          x21, x21, x20
    c4c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c4c
    c50: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c64
    c54: 001b9b93  slli         x23, x23, 1
    c58: 017b0b33  add          x22, x22, x23
    c5c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c60: 00008067  jalr         x0, 0(x1)
    c64: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c68: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c6c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c70: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c74:
    c74: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c78: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    c7c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    c80: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    c84: 015a6463  bltu         x20, x21, 0x00000c8c  # target 0x00000c8c
    c88: fedff06f  jal          x0, 0x00000c74  # target 0x00000c74
loc_c8c:
    c8c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    c90: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    c94: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    c98: 014a1a13  slli         x20, x20, 20
    c9c: 014a5a13  srli         x20, x20, 20
    ca0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_ca4:
    ca4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    ca8: 000b0463  beq          x22, x0, 0x00000cb0  # target 0x00000cb0
    cac: ff9ff06f  jal          x0, 0x00000ca4  # target 0x00000ca4
loc_cb0:
    cb0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    cb4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    cb8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    cbc: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    cc0: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    cc4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    cc8: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    ccc: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    cd0: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    cd4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    cd8: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    cdc: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    ce0: 10000c13  addi         x24, x0, 256  # x24 = 0x00000100
    ce4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000100
    ce8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    cec: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    cf0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    cf4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    cf8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    cfc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    d00: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_d04:
    d04: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d08: 000b0463  beq          x22, x0, 0x00000d10  # target 0x00000d10
    d0c: ff9ff06f  jal          x0, 0x00000d04  # target 0x00000d04
loc_d10:
    d10: 00008067  jalr         x0, 0(x1)
loc_d14:
    d14: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    d18: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
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
    d60: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    d64: 000aaa03  lw           x20, 0(x21)  # param e2e_q; 0x00000798
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
    dac: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    db0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    db4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    db8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    dbc: 015a6463  bltu         x20, x21, 0x00000dc4  # target 0x00000dc4
    dc0: fedff06f  jal          x0, 0x00000dac  # target 0x00000dac
loc_dc4:
    dc4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    dc8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    dcc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    dd0: 014a1a13  slli         x20, x20, 20
    dd4: 014a5a13  srli         x20, x20, 20
    dd8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_ddc:
    ddc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    de0: 000b0463  beq          x22, x0, 0x00000de8  # target 0x00000de8
    de4: ff9ff06f  jal          x0, 0x00000ddc  # target 0x00000ddc
loc_de8:
    de8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    dec: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    df0: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    df4: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    df8: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    dfc: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    e00: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    e04: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    e08: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    e0c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    e10: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    e14: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    e18: 08000c13  addi         x24, x0, 128  # x24 = 0x00000080
    e1c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000080
    e20: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    e24: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    e28: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    e2c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    e30: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    e34: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    e38: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_e3c:
    e3c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    e40: 000b0463  beq          x22, x0, 0x00000e48  # target 0x00000e48
    e44: ff9ff06f  jal          x0, 0x00000e3c  # target 0x00000e3c
loc_e48:
    e48: 00008067  jalr         x0, 0(x1)
loc_e4c:
    e4c: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    e50: 000aaa03  lw           x20, 0(x21)  # param e2e_k; 0x0000079c
    e54: 007a7d13  andi         x26, x20, 7
    e58: ff8a7a13  andi         x20, x20, -8
    e5c: 01af8ab3  add          x21, x31, x26
    e60: 007afb93  andi         x23, x21, 7
    e64: 003ada93  srli         x21, x21, 3
    e68: 00ba9a93  slli         x21, x21, 11
    e6c: 014a8ab3  add          x21, x21, x20
    e70: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e70
    e74: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e88
    e78: 001b9b93  slli         x23, x23, 1
    e7c: 017b0b33  add          x22, x22, x23
    e80: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e84: 00008067  jalr         x0, 0(x1)
    e88: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    e8c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e90: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e94: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_e98:
    e98: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    e9c: 000aaa03  lw           x20, 0(x21)  # param e2e_v; 0x000007a0
    ea0: 007a7d13  andi         x26, x20, 7
    ea4: ff8a7a13  andi         x20, x20, -8
    ea8: 01af8ab3  add          x21, x31, x26
    eac: 007afb93  andi         x23, x21, 7
    eb0: 003ada93  srli         x21, x21, 3
    eb4: 00ba9a93  slli         x21, x21, 11
    eb8: 014a8ab3  add          x21, x21, x20
    ebc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ebc
    ec0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000ed4
    ec4: 001b9b93  slli         x23, x23, 1
    ec8: 017b0b33  add          x22, x22, x23
    ecc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ed0: 00008067  jalr         x0, 0(x1)
    ed4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ed8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    edc: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ee0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ee4:
    ee4: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    ee8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    eec: 007a7d13  andi         x26, x20, 7
    ef0: ff8a7a13  andi         x20, x20, -8
    ef4: 01af8ab3  add          x21, x31, x26
    ef8: 007afb93  andi         x23, x21, 7
    efc: 003ada93  srli         x21, x21, 3
    f00: 00ba9a93  slli         x21, x21, 11
    f04: 014a8ab3  add          x21, x21, x20
    f08: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000f08
    f0c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000f20
    f10: 001b9b93  slli         x23, x23, 1
    f14: 017b0b33  add          x22, x22, x23
    f18: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    f1c: 00008067  jalr         x0, 0(x1)
    f20: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f24: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    f28: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    f2c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_f30:
    f30: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    f34: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    f38: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    f3c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    f40: 015a6463  bltu         x20, x21, 0x00000f48  # target 0x00000f48
    f44: fedff06f  jal          x0, 0x00000f30  # target 0x00000f30
loc_f48:
    f48: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    f4c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    f50: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    f54: 014a1a13  slli         x20, x20, 20
    f58: 014a5a13  srli         x20, x20, 20
    f5c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_f60:
    f60: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    f64: 000b0463  beq          x22, x0, 0x00000f6c  # target 0x00000f6c
    f68: ff9ff06f  jal          x0, 0x00000f60  # target 0x00000f60
loc_f6c:
    f6c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    f70: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    f74: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    f78: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    f7c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    f80: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    f84: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    f88: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    f8c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    f90: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    f94: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    f98: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    f9c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    fa0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    fa4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    fa8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    fac: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    fb0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    fb4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    fb8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    fbc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    fc0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_fc4:
    fc4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    fc8: 000b0463  beq          x22, x0, 0x00000fd0  # target 0x00000fd0
    fcc: ff9ff06f  jal          x0, 0x00000fc4  # target 0x00000fc4
loc_fd0:
    fd0: 00008067  jalr         x0, 0(x1)
loc_fd4:
    fd4: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    fd8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    fdc: 007a7d13  andi         x26, x20, 7
    fe0: ff8a7a13  andi         x20, x20, -8
    fe4: 01af8ab3  add          x21, x31, x26
    fe8: 007afb93  andi         x23, x21, 7
    fec: 003ada93  srli         x21, x21, 3
    ff0: 00ba9a93  slli         x21, x21, 11
    ff4: 014a8ab3  add          x21, x21, x20
    ff8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000ff8
    ffc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001010
   1000: 001b9b93  slli         x23, x23, 1
   1004: 017b0b33  add          x22, x22, x23
   1008: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   100c: 00008067  jalr         x0, 0(x1)
   1010: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1014: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1018: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
   101c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_1020:
   1020: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
   1024: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
   1028: 007a7d13  andi         x26, x20, 7
   102c: ff8a7a13  andi         x20, x20, -8
   1030: 01af8ab3  add          x21, x31, x26
   1034: 007afb93  andi         x23, x21, 7
   1038: 003ada93  srli         x21, x21, 3
   103c: 00ba9a93  slli         x21, x21, 11
   1040: 014a8ab3  add          x21, x21, x20
   1044: 00000b17  auipc        x22, 0x00000  # x22 = 0x00001044
   1048: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000105c
   104c: 001b9b93  slli         x23, x23, 1
   1050: 017b0b33  add          x22, x22, x23
   1054: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   1058: 00008067  jalr         x0, 0(x1)
   105c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
   1060: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1064: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
   1068: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_106c:
   106c: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   1070: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   1074: 007a7d13  andi         x26, x20, 7
   1078: ff8a7a13  andi         x20, x20, -8
   107c: 01af8ab3  add          x21, x31, x26
   1080: 007afb93  andi         x23, x21, 7
   1084: 003ada93  srli         x21, x21, 3
   1088: 00ba9a93  slli         x21, x21, 11
   108c: 014a8ab3  add          x21, x21, x20
   1090: 00000b17  auipc        x22, 0x00000  # x22 = 0x00001090
   1094: 018b0b13  addi         x22, x22, 24  # x22 = 0x000010a8
   1098: 001b9b93  slli         x23, x23, 1
   109c: 017b0b33  add          x22, x22, x23
   10a0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   10a4: 00008067  jalr         x0, 0(x1)
   10a8: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   10ac: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   10b0: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
   10b4: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_10b8:
   10b8: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   10bc: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   10c0: 007a7d13  andi         x26, x20, 7
   10c4: ff8a7a13  andi         x20, x20, -8
   10c8: 01af8ab3  add          x21, x31, x26
   10cc: 007afb93  andi         x23, x21, 7
   10d0: 003ada93  srli         x21, x21, 3
   10d4: 00ba9a93  slli         x21, x21, 11
   10d8: 014a8ab3  add          x21, x21, x20
   10dc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000010dc
   10e0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000010f4
   10e4: 001b9b93  slli         x23, x23, 1
   10e8: 017b0b33  add          x22, x22, x23
   10ec: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   10f0: 00008067  jalr         x0, 0(x1)
   10f4: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
   10f8: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   10fc: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
   1100: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_1104:
   1104: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
   1108: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
   110c: 007a7d13  andi         x26, x20, 7
   1110: ff8a7a13  andi         x20, x20, -8
   1114: 01af8ab3  add          x21, x31, x26
   1118: 007afb93  andi         x23, x21, 7
   111c: 003ada93  srli         x21, x21, 3
   1120: 00ba9a93  slli         x21, x21, 11
   1124: 014a8ab3  add          x21, x21, x20
   1128: 00000b17  auipc        x22, 0x00000  # x22 = 0x00001128
   112c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00001140
   1130: 001b9b93  slli         x23, x23, 1
   1134: 017b0b33  add          x22, x22, x23
   1138: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
   113c: 00008067  jalr         x0, 0(x1)
   1140: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1144: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
   1148: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
   114c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_1150:
   1150: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
   1154: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
   1158: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
   115c: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
   1160: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
   1164: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
   1168: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
   116c: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
   1170: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
   1174: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
   1178: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
   117c: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
   1180: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
   1184: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
   1188: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
   118c: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
   1190: 020f8f93  addi         x31, x31, 32
   1194: 020f0f13  addi         x30, x30, 32
   1198: ff8e8e93  addi         x29, x29, -8
   119c: fa0e9ae3  bne          x29, x0, 0x00001150  # target 0x00001150
   11a0: 00008067  jalr         x0, 0(x1)
   11a4:           j FW_BRISC+4   # return to firmware, linked at install
