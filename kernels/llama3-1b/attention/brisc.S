# llama3 1b decode: attention, brisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (64): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3 4,4 4,5 4,6 4,7 4,8 4,9 4,10 4,11 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9 5,10 5,11 6,2 6,3 6,4 6,5 6,6 6,7 6,8 6,9 6,10 6,11 7,2 7,3 7,4 7,5
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=e2e_q, 0x79c=e2e_k, 0x7a0=e2e_v, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0x11900=attention_core, 0x11904=attention_phase, 0x11908=attention_merger
#   0x780.. uniform, sent with every EXEC; 0x11840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
      8: 0001c2b7  lui          x5, 0x0001c  # x5 = 0x0001c000
      c: 80028293  addi         x5, x5, -2048  # x5 = 0x0001b800
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x0001b800
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 87c20213  addi         x4, x4, -1924  # x4 = 0xffb0087c · riscv_local_mem + 0x87c
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x87c · 0xffb0087c; write 0x00000000
     20: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     24: 88058593  addi         x11, x11, -1920  # x11 = 0xffb00880 · riscv_local_mem + 0x880
     28: 00013637  lui          x12, 0x00013  # x12 = 0x00013000
     2c: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x880 · 0xffb00880; write 0x00013000
     30: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     34: 88458593  addi         x11, x11, -1916  # x11 = 0xffb00884 · riscv_local_mem + 0x884
     38: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x884 · 0xffb00884; write 0x00000000
     3c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     40: 88858593  addi         x11, x11, -1912  # x11 = 0xffb00888 · riscv_local_mem + 0x888
     44: 00015637  lui          x12, 0x00015  # x12 = 0x00015000
     48: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x888 · 0xffb00888; write 0x00015000
     4c: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     50: 88c58593  addi         x11, x11, -1908  # x11 = 0xffb0088c · riscv_local_mem + 0x88c
     54: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x88c · 0xffb0088c; write 0x00000000
     58: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     5c: 89058593  addi         x11, x11, -1904  # x11 = 0xffb00890 · riscv_local_mem + 0x890
     60: 0001e637  lui          x12, 0x0001e  # x12 = 0x0001e000
     64: 00c5a023  sw           x12, 0(x11)  # riscv_local_mem + 0x890 · 0xffb00890; write 0x0001e000
     68: ffb015b7  lui          x11, 0xffb01  # x11 = 0xffb01000
     6c: 89458593  addi         x11, x11, -1900  # x11 = 0xffb00894 · riscv_local_mem + 0x894
     70: 0005a023  sw           x0, 0(x11)  # riscv_local_mem + 0x894 · 0xffb00894; write 0x00000000
     74: ffb014b7  lui          x9, 0xffb01  # x9 = 0xffb01000
     78: 89848493  addi         x9, x9, -1896  # x9 = 0xffb00898 · riscv_local_mem + 0x898
     7c: 0001f537  lui          x10, 0x0001f  # x10 = 0x0001f000
     80: 88050513  addi         x10, x10, -1920  # x10 = 0x0001e880
     84: 00a4a023  sw           x10, 0(x9)  # riscv_local_mem + 0x898 · 0xffb00898; write 0x0001e880
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
     c4: 125274e3  bgeu         x4, x5, 0x000009ec  # target 0x000009ec
     c8: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
     cc: 90028293  addi         x5, x5, -1792  # x5 = 0x00011900
     d0: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x00011900
     d4: 00800293  addi         x5, x0, 8  # x5 = 0x00000008
     d8: 02525233  divu         x4, x4, x5
     dc: 115000ef  jal          x1, 0x000009f0  # target 0x000009f0; x1 = 0x000000e0
     e0: 12d000ef  jal          x1, 0x00000a0c  # target 0x00000a0c; x1 = 0x000000e4
     e4: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
     e8: 0003a283  lw           x5, 0(x7)  # param start_pos; 0x000007ac
     ec: 00f2f313  andi         x6, x5, 15
     f0: 00731313  slli         x6, x6, 7
     f4: 0042d293  srli         x5, x5, 4
     f8: 00028f93  addi         x31, x5, 0
     fc: 12d000ef  jal          x1, 0x00000a28  # target 0x00000a28; x1 = 0x00000100
    100: 000a8393  addi         x7, x21, 0
    104: 000b0413  addi         x8, x22, 0
    108: 006383b3  add          x7, x7, x6
    10c: 00038f93  addi         x31, x7, 0
    110: 00040f13  addi         x30, x8, 0
    114: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    118: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001c800
    11c: 159000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x00000120
    120: 00038f93  addi         x31, x7, 0
    124: 00040f13  addi         x30, x8, 0
    128: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    12c: 880e8e93  addi         x29, x29, -1920  # x29 = 0x0001c880
    130: 145000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x00000134
    134: 00038f93  addi         x31, x7, 0
    138: 00040f13  addi         x30, x8, 0
    13c: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    140: 900e8e93  addi         x29, x29, -1792  # x29 = 0x0001c900
    144: 131000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x00000148
    148: 00038f93  addi         x31, x7, 0
    14c: 00040f13  addi         x30, x8, 0
    150: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    154: 980e8e93  addi         x29, x29, -1664  # x29 = 0x0001c980
    158: 11d000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x0000015c
    15c: 00038f93  addi         x31, x7, 0
    160: 00040f13  addi         x30, x8, 0
    164: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    168: a00e8e93  addi         x29, x29, -1536  # x29 = 0x0001ca00
    16c: 109000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x00000170
    170: 00028f93  addi         x31, x5, 0
    174: 1a1000ef  jal          x1, 0x00000b14  # target 0x00000b14; x1 = 0x00000178
    178: 000a8393  addi         x7, x21, 0
    17c: 000b0413  addi         x8, x22, 0
    180: 006383b3  add          x7, x7, x6
    184: 00038f93  addi         x31, x7, 0
    188: 00040f13  addi         x30, x8, 0
    18c: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    190: 0e5000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x00000194
    194: 00038f93  addi         x31, x7, 0
    198: 00040f13  addi         x30, x8, 0
    19c: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    1a0: 080e8e93  addi         x29, x29, 128  # x29 = 0x0001d080
    1a4: 0d1000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x000001a8
    1a8: 00038f93  addi         x31, x7, 0
    1ac: 00040f13  addi         x30, x8, 0
    1b0: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    1b4: 100e8e93  addi         x29, x29, 256  # x29 = 0x0001d100
    1b8: 0bd000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x000001bc
    1bc: 00038f93  addi         x31, x7, 0
    1c0: 00040f13  addi         x30, x8, 0
    1c4: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    1c8: 180e8e93  addi         x29, x29, 384  # x29 = 0x0001d180
    1cc: 0a9000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x000001d0
    1d0: 00038f93  addi         x31, x7, 0
    1d4: 00040f13  addi         x30, x8, 0
    1d8: 0001deb7  lui          x29, 0x0001d  # x29 = 0x0001d000
    1dc: 200e8e93  addi         x29, x29, 512  # x29 = 0x0001d200
    1e0: 095000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x000001e4
    1e4: 00821293  slli         x5, x4, 8
    1e8: 3ff2f313  andi         x6, x5, 1023
    1ec: 00131313  slli         x6, x6, 1
    1f0: 00a2d293  srli         x5, x5, 10
    1f4: 00028f93  addi         x31, x5, 0
    1f8: 169000ef  jal          x1, 0x00000b60  # target 0x00000b60; x1 = 0x000001fc
    1fc: 000a8393  addi         x7, x21, 0
    200: 000b0413  addi         x8, x22, 0
    204: 006383b3  add          x7, x7, x6
    208: 00038f93  addi         x31, x7, 0
    20c: 00040f13  addi         x30, x8, 0
    210: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    214: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001b800
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
    264: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write 0x0001b800
    268: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    26c: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    270: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    274: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    278: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    27c: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    280: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    284: 20000c13  addi         x24, x0, 512  # x24 = 0x00000200
    288: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000200
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
    2b4: 04038493  addi         x9, x7, 64
    2b8: 00048f93  addi         x31, x9, 0
    2bc: 00040f13  addi         x30, x8, 0
    2c0: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    2c4: 0e9000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000002c8
    2c8: 00038f93  addi         x31, x7, 0
    2cc: 00040f13  addi         x30, x8, 0
    2d0: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    2d4: 040e8e93  addi         x29, x29, 64  # x29 = 0x0001c040
    2d8: 0d5000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000002dc
    2dc: 0c038493  addi         x9, x7, 192
    2e0: 00048f93  addi         x31, x9, 0
    2e4: 00040f13  addi         x30, x8, 0
    2e8: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    2ec: 080e8e93  addi         x29, x29, 128  # x29 = 0x0001c080
    2f0: 0bd000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000002f4
    2f4: 08038493  addi         x9, x7, 128
    2f8: 00048f93  addi         x31, x9, 0
    2fc: 00040f13  addi         x30, x8, 0
    300: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    304: 0c0e8e93  addi         x29, x29, 192  # x29 = 0x0001c0c0
    308: 0a5000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x0000030c
    30c: 14038493  addi         x9, x7, 320
    310: 00048f93  addi         x31, x9, 0
    314: 00040f13  addi         x30, x8, 0
    318: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    31c: 100e8e93  addi         x29, x29, 256  # x29 = 0x0001c100
    320: 08d000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x00000324
    324: 10038493  addi         x9, x7, 256
    328: 00048f93  addi         x31, x9, 0
    32c: 00040f13  addi         x30, x8, 0
    330: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    334: 140e8e93  addi         x29, x29, 320  # x29 = 0x0001c140
    338: 075000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x0000033c
    33c: 1c038493  addi         x9, x7, 448
    340: 00048f93  addi         x31, x9, 0
    344: 00040f13  addi         x30, x8, 0
    348: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    34c: 180e8e93  addi         x29, x29, 384  # x29 = 0x0001c180
    350: 05d000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x00000354
    354: 18038493  addi         x9, x7, 384
    358: 00048f93  addi         x31, x9, 0
    35c: 00040f13  addi         x30, x8, 0
    360: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    364: 1c0e8e93  addi         x29, x29, 448  # x29 = 0x0001c1c0
    368: 045000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x0000036c
    36c: 00221293  slli         x5, x4, 2
    370: 0022d293  srli         x5, x5, 2
    374: 00629293  slli         x5, x5, 6
    378: 3ff2f313  andi         x6, x5, 1023
    37c: 00131313  slli         x6, x6, 1
    380: 00a2d293  srli         x5, x5, 10
    384: 00028f93  addi         x31, x5, 0
    388: 0c5000ef  jal          x1, 0x00000c4c  # target 0x00000c4c; x1 = 0x0000038c
    38c: 000a8393  addi         x7, x21, 0
    390: 000b0413  addi         x8, x22, 0
    394: 006383b3  add          x7, x7, x6
    398: 00038f93  addi         x31, x7, 0
    39c: 00040f13  addi         x30, x8, 0
    3a0: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    3a4: a00e8e93  addi         x29, x29, -1536  # x29 = 0x0001ba00
    3a8: 6cc000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x000003ac
    3ac: 04038493  addi         x9, x7, 64
    3b0: 00048f93  addi         x31, x9, 0
    3b4: 00040f13  addi         x30, x8, 0
    3b8: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    3bc: 200e8e93  addi         x29, x29, 512  # x29 = 0x0001c200
    3c0: 7ec000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000003c4
    3c4: 00038f93  addi         x31, x7, 0
    3c8: 00040f13  addi         x30, x8, 0
    3cc: 0001ceb7  lui          x29, 0x0001c  # x29 = 0x0001c000
    3d0: 240e8e93  addi         x29, x29, 576  # x29 = 0x0001c240
    3d4: 7d8000ef  jal          x1, 0x00000bac  # target 0x00000bac; x1 = 0x000003d8
    3d8: 00221293  slli         x5, x4, 2
    3dc: 0022d293  srli         x5, x5, 2
    3e0: 00629293  slli         x5, x5, 6
    3e4: 3ff2f313  andi         x6, x5, 1023
    3e8: 00131313  slli         x6, x6, 1
    3ec: 00a2d293  srli         x5, x5, 10
    3f0: 00028f93  addi         x31, x5, 0
    3f4: 0a5000ef  jal          x1, 0x00000c98  # target 0x00000c98; x1 = 0x000003f8
    3f8: 000a8393  addi         x7, x21, 0
    3fc: 000b0413  addi         x8, x22, 0
    400: 006383b3  add          x7, x7, x6
    404: 00038f93  addi         x31, x7, 0
    408: 00040f13  addi         x30, x8, 0
    40c: 0001feb7  lui          x29, 0x0001f  # x29 = 0x0001f000
    410: 800e8e93  addi         x29, x29, -2048  # x29 = 0x0001e800
    414: 660000ef  jal          x1, 0x00000a74  # target 0x00000a74; x1 = 0x00000418
    418: 5f4000ef  jal          x1, 0x00000a0c  # target 0x00000a0c; x1 = 0x0000041c
    41c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    420: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    424: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    428: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    42c: 00520233  add          x4, x4, x5
    430: 0001e337  lui          x6, 0x0001e  # x6 = 0x0001e000
    434: 80030313  addi         x6, x6, -2048  # x6 = 0x0001d800
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
    50c: 4083fa63  bgeu         x7, x8, 0x00000920  # target 0x00000920
    510: 00025493  srli         x9, x4, 0
    514: 00949493  slli         x9, x9, 9
    518: 02638533  mul          x10, x7, x6
    51c: 00012637  lui          x12, 0x00012  # x12 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    520: 90460613  addi         x12, x12, -1788  # x12 = 0x00011904
    524: 00062583  lw           x11, 0(x12)  # param attention_phase; 0x00011904
    528: 00b50533  add          x10, x10, x11
    52c: 79000613  addi         x12, x0, 1936  # x12 = 0x00000790
    530: 00062583  lw           x11, 0(x12)  # param kv_blocks; 0x00000790
    534: fff58593  addi         x11, x11, -1
    538: 40b505b3  sub          x11, x10, x11
    53c: 00151513  slli         x10, x10, 1
    540: 00a484b3  add          x9, x9, x10
    544: 00058513  addi         x10, x11, 0
    548: 4a8000ef  jal          x1, 0x000009f0  # target 0x000009f0; x1 = 0x0000054c
    54c: 4c0000ef  jal          x1, 0x00000a0c  # target 0x00000a0c; x1 = 0x00000550
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
    574: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    578: 40d70733  sub          x14, x14, x13
    57c: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    580: 00f77663  bgeu         x14, x15, 0x0000058c  # target 0x0000058c
    584: 0ff0000f  fence        0xf, 0xf
    588: fd5ff06f  jal          x0, 0x0000055c  # target 0x0000055c
loc_58c:
    58c: 0ff0000f  fence        0xf, 0xf
    590: 00048593  addi         x11, x9, 0
    594: 00058f93  addi         x31, x11, 0
    598: 74c000ef  jal          x1, 0x00000ce4  # target 0x00000ce4; x1 = 0x0000059c
    59c: 000a8613  addi         x12, x21, 0
    5a0: 000b0693  addi         x13, x22, 0
    5a4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    5a8: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    5ac: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    5b0: 00060f93  addi         x31, x12, 0
    5b4: 00068f13  addi         x30, x13, 0
    5b8: 00070e93  addi         x29, x14, 0
    5bc: 774000ef  jal          x1, 0x00000d30  # target 0x00000d30; x1 = 0x000005c0
    5c0: 00148593  addi         x11, x9, 1
    5c4: 00058f93  addi         x31, x11, 0
    5c8: 00d000ef  jal          x1, 0x00000dd4  # target 0x00000dd4; x1 = 0x000005cc
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
    5f8: 738000ef  jal          x1, 0x00000d30  # target 0x00000d30; x1 = 0x000005fc
    5fc: ffb01837  lui          x16, 0xffb01  # x16 = 0xffb01000
    600: 88c80813  addi         x16, x16, -1908  # x16 = 0xffb0088c · riscv_local_mem + 0x88c
    604: 00082583  lw           x11, 0(x16)  # riscv_local_mem + 0x88c · 0xffb0088c
loc_608:
    608: ffb4a837  lui          x16, 0xffb4a  # x16 = 0xffb4a000
    60c: 02080813  addi         x16, x16, 32  # x16 = 0xffb4a020
    610: 00085603  lhu          x12, 0(x16)  # 0xffb4a020
    614: 40c586b3  sub          x13, x11, x12
    618: 01069693  slli         x13, x13, 16
    61c: 0106d693  srli         x13, x13, 16
    620: 00400713  addi         x14, x0, 4  # x14 = 0x00000004
    624: 40d70733  sub          x14, x14, x13
    628: 00200793  addi         x15, x0, 2  # x15 = 0x00000002
    62c: 00f77663  bgeu         x14, x15, 0x00000638  # target 0x00000638
    630: 0ff0000f  fence        0xf, 0xf
    634: fd5ff06f  jal          x0, 0x00000608  # target 0x00000608
loc_638:
    638: 0ff0000f  fence        0xf, 0xf
    63c: 00048593  addi         x11, x9, 0
    640: 00058f93  addi         x31, x11, 0
    644: 7dc000ef  jal          x1, 0x00000e20  # target 0x00000e20; x1 = 0x00000648
    648: 000a8613  addi         x12, x21, 0
    64c: 000b0693  addi         x13, x22, 0
    650: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    654: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    658: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    65c: 00060f93  addi         x31, x12, 0
    660: 00068f13  addi         x30, x13, 0
    664: 00070e93  addi         x29, x14, 0
    668: 6c8000ef  jal          x1, 0x00000d30  # target 0x00000d30; x1 = 0x0000066c
    66c: 00148593  addi         x11, x9, 1
    670: 00058f93  addi         x31, x11, 0
    674: 7f8000ef  jal          x1, 0x00000e6c  # target 0x00000e6c; x1 = 0x00000678
    678: 000a8613  addi         x12, x21, 0
    67c: 000b0693  addi         x13, x22, 0
    680: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    684: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    688: 0007a703  lw           x14, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    68c: 000017b7  lui          x15, 0x00001  # x15 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    690: 80078793  addi         x15, x15, -2048  # x15 = 0x00000800
    694: 00f70733  add          x14, x14, x15
    698: 00060f93  addi         x31, x12, 0
    69c: 00068f13  addi         x30, x13, 0
    6a0: 00070e93  addi         x29, x14, 0
    6a4: 68c000ef  jal          x1, 0x00000d30  # target 0x00000d30; x1 = 0x000006a8
    6a8: 364000ef  jal          x1, 0x00000a0c  # target 0x00000a0c; x1 = 0x000006ac
    6ac: 1a051263  bne          x10, x0, 0x00000850  # target 0x00000850
    6b0: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    6b4: 89478793  addi         x15, x15, -1900  # x15 = 0xffb00894 · riscv_local_mem + 0x894
    6b8: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x894 · 0xffb00894
    6bc: 00100713  addi         x14, x0, 1  # x14 = 0x00000001
loc_6c0:
    6c0: ffb4f7b7  lui          x15, 0xffb4f  # x15 = 0xffb4f000
    6c4: 02878793  addi         x15, x15, 40  # x15 = 0xffb4f028
    6c8: 0007d603  lhu          x12, 0(x15)  # 0xffb4f028
    6cc: 40b606b3  sub          x13, x12, x11
    6d0: 01069693  slli         x13, x13, 16
    6d4: 0106d693  srli         x13, x13, 16
    6d8: 00e6f663  bgeu         x13, x14, 0x000006e4  # target 0x000006e4
    6dc: 0ff0000f  fence        0xf, 0xf
    6e0: fe1ff06f  jal          x0, 0x000006c0  # target 0x000006c0
loc_6e4:
    6e4: 0ff0000f  fence        0xf, 0xf
    6e8: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    6ec: 88060613  addi         x12, x12, -1920  # x12 = 0xffb00880 · riscv_local_mem + 0x880
    6f0: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x880 · 0xffb00880
    6f4: 7ac00793  addi         x15, x0, 1964  # x15 = 0x000007ac
    6f8: 0007a603  lw           x12, 0(x15)  # param start_pos; 0x000007ac
    6fc: 01067793  andi         x15, x12, 16
    700: 00679793  slli         x15, x15, 6
    704: 00f67613  andi         x12, x12, 15
    708: 00561613  slli         x12, x12, 5
    70c: 00f60633  add          x12, x12, x15
    710: 00b60633  add          x12, x12, x11
    714: 0001e737  lui          x14, 0x0001e  # x14 = 0x0001e000
    718: a0070713  addi         x14, x14, -1536  # x14 = 0x0001da00
    71c: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    720: 00c686b3  add          x13, x13, x12
    724: 00070f93  addi         x31, x14, 0  # x31 = 0x0001da00
    728: 00068f13  addi         x30, x13, 0
    72c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    730: 788000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x00000734
    734: 0001e737  lui          x14, 0x0001e  # x14 = 0x0001e000
    738: a2070713  addi         x14, x14, -1504  # x14 = 0x0001da20
    73c: 20000693  addi         x13, x0, 512  # x13 = 0x00000200
    740: 00c686b3  add          x13, x13, x12
    744: 00070f93  addi         x31, x14, 0  # x31 = 0x0001da20
    748: 00068f13  addi         x30, x13, 0
    74c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    750: 768000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x00000754
    754: 0001e737  lui          x14, 0x0001e  # x14 = 0x0001e000
    758: a4070713  addi         x14, x14, -1472  # x14 = 0x0001da40
    75c: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    760: 80068693  addi         x13, x13, -2048  # x13 = 0x00000800
    764: 00c686b3  add          x13, x13, x12
    768: 00070f93  addi         x31, x14, 0  # x31 = 0x0001da40
    76c: 00068f13  addi         x30, x13, 0
    770: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    774: 744000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x00000778
    778: 0001e737  lui          x14, 0x0001e  # x14 = 0x0001e000
    77c: a6070713  addi         x14, x14, -1440  # x14 = 0x0001da60
    780: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    784: a0068693  addi         x13, x13, -1536  # x13 = 0x00000a00
    788: 00c686b3  add          x13, x13, x12
    78c: 00070f93  addi         x31, x14, 0  # x31 = 0x0001da60
    790: 00068f13  addi         x30, x13, 0
    794: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    798: 720000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x0000079c
    79c: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    7a0: 88860613  addi         x12, x12, -1912  # x12 = 0xffb00888 · riscv_local_mem + 0x888
    7a4: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x888 · 0xffb00888
    7a8: 7ac00793  addi         x15, x0, 1964  # x15 = 0x000007ac
    7ac: 0007a603  lw           x12, 0(x15)  # param start_pos; 0x000007ac
    7b0: 01067793  andi         x15, x12, 16
    7b4: 00679793  slli         x15, x15, 6
    7b8: 00f67613  andi         x12, x12, 15
    7bc: 00561613  slli         x12, x12, 5
    7c0: 00f60633  add          x12, x12, x15
    7c4: 00b60633  add          x12, x12, x11
    7c8: 0001f737  lui          x14, 0x0001f  # x14 = 0x0001f000
    7cc: 80070713  addi         x14, x14, -2048  # x14 = 0x0001e800
    7d0: 00000693  addi         x13, x0, 0  # x13 = 0x00000000
    7d4: 00c686b3  add          x13, x13, x12
    7d8: 00070f93  addi         x31, x14, 0  # x31 = 0x0001e800
    7dc: 00068f13  addi         x30, x13, 0
    7e0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    7e4: 6d4000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x000007e8
    7e8: 0001f737  lui          x14, 0x0001f  # x14 = 0x0001f000
    7ec: 82070713  addi         x14, x14, -2016  # x14 = 0x0001e820
    7f0: 20000693  addi         x13, x0, 512  # x13 = 0x00000200
    7f4: 00c686b3  add          x13, x13, x12
    7f8: 00070f93  addi         x31, x14, 0  # x31 = 0x0001e820
    7fc: 00068f13  addi         x30, x13, 0
    800: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    804: 6b4000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x00000808
    808: 0001f737  lui          x14, 0x0001f  # x14 = 0x0001f000
    80c: 84070713  addi         x14, x14, -1984  # x14 = 0x0001e840
    810: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    814: 80068693  addi         x13, x13, -2048  # x13 = 0x00000800
    818: 00c686b3  add          x13, x13, x12
    81c: 00070f93  addi         x31, x14, 0  # x31 = 0x0001e840
    820: 00068f13  addi         x30, x13, 0
    824: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    828: 690000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x0000082c
    82c: 0001f737  lui          x14, 0x0001f  # x14 = 0x0001f000
    830: 86070713  addi         x14, x14, -1952  # x14 = 0x0001e860
    834: 000016b7  lui          x13, 0x00001  # x13 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    838: a0068693  addi         x13, x13, -1536  # x13 = 0x00000a00
    83c: 00c686b3  add          x13, x13, x12
    840: 00070f93  addi         x31, x14, 0  # x31 = 0x0001e860
    844: 00068f13  addi         x30, x13, 0
    848: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    84c: 66c000ef  jal          x1, 0x00000eb8  # target 0x00000eb8; x1 = 0x00000850
loc_850:
    850: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    854: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    858: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880
    85c: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    860: 00c585b3  add          x11, x11, x12
    864: 000156b7  lui          x13, 0x00015  # x13 = 0x00015000
    868: 00d5e663  bltu         x11, x13, 0x00000874  # target 0x00000874
    86c: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    870: 40e585b3  sub          x11, x11, x14
loc_874:
    874: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    878: 88078793  addi         x15, x15, -1920  # x15 = 0xffb00880 · riscv_local_mem + 0x880
    87c: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x880 · 0xffb00880; write runtime value
    880: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    884: 88460613  addi         x12, x12, -1916  # x12 = 0xffb00884 · riscv_local_mem + 0x884
    888: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x884 · 0xffb00884
    88c: 00258593  addi         x11, x11, 2
    890: 01059593  slli         x11, x11, 16
    894: 0105d593  srli         x11, x11, 16
    898: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    89c: 88460613  addi         x12, x12, -1916  # x12 = 0xffb00884 · riscv_local_mem + 0x884
    8a0: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x884 · 0xffb00884; write runtime value
    8a4: ffb49637  lui          x12, 0xffb49  # x12 = 0xffb49000
    8a8: 02860613  addi         x12, x12, 40  # x12 = 0xffb49028
    8ac: 00b62023  sw           x11, 0(x12)  # 0xffb49028; write runtime value
    8b0: 0ff0000f  fence        0xf, 0xf
    8b4: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    8b8: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    8bc: 0007a583  lw           x11, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888
    8c0: 00001637  lui          x12, 0x00001  # x12 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    8c4: 00c585b3  add          x11, x11, x12
    8c8: 000176b7  lui          x13, 0x00017  # x13 = 0x00017000
    8cc: 00d5e663  bltu         x11, x13, 0x000008d8  # target 0x000008d8
    8d0: 00002737  lui          x14, 0x00002  # x14 = 0x00002000
    8d4: 40e585b3  sub          x11, x11, x14
loc_8d8:
    8d8: ffb017b7  lui          x15, 0xffb01  # x15 = 0xffb01000
    8dc: 88878793  addi         x15, x15, -1912  # x15 = 0xffb00888 · riscv_local_mem + 0x888
    8e0: 00b7a023  sw           x11, 0(x15)  # riscv_local_mem + 0x888 · 0xffb00888; write runtime value
    8e4: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    8e8: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    8ec: 00062583  lw           x11, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c
    8f0: 00258593  addi         x11, x11, 2
    8f4: 01059593  slli         x11, x11, 16
    8f8: 0105d593  srli         x11, x11, 16
    8fc: ffb01637  lui          x12, 0xffb01  # x12 = 0xffb01000
    900: 88c60613  addi         x12, x12, -1908  # x12 = 0xffb0088c · riscv_local_mem + 0x88c
    904: 00b62023  sw           x11, 0(x12)  # riscv_local_mem + 0x88c · 0xffb0088c; write runtime value
    908: ffb4a637  lui          x12, 0xffb4a  # x12 = 0xffb4a000
    90c: 02860613  addi         x12, x12, 40  # x12 = 0xffb4a028
    910: 00b62023  sw           x11, 0(x12)  # 0xffb4a028; write runtime value
    914: 0ff0000f  fence        0xf, 0xf
    918: 00138393  addi         x7, x7, 1
    91c: bf1ff06f  jal          x0, 0x0000050c  # target 0x0000050c
loc_920:
    920: 000122b7  lui          x5, 0x00012  # x5 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    924: 90428293  addi         x5, x5, -1788  # x5 = 0x00011904
    928: 0002a203  lw           x4, 0(x5)  # param attention_phase; 0x00011904
    92c: 0c021063  bne          x4, x0, 0x000009ec  # target 0x000009ec
    930: 79000493  addi         x9, x0, 1936  # x9 = 0x00000790
    934: 0004a383  lw           x7, 0(x9)  # param kv_blocks; 0x00000790
    938: 00100213  addi         x4, x0, 1  # x4 = 0x00000001
    93c: 00400413  addi         x8, x0, 4  # x8 = 0x00000004
    940: 00747a63  bgeu         x8, x7, 0x00000954  # target 0x00000954
    944: 00400213  addi         x4, x0, 4  # x4 = 0x00000004
    948: 05000413  addi         x8, x0, 80  # x8 = 0x00000050
    94c: 00747463  bgeu         x8, x7, 0x00000954  # target 0x00000954
    950: 00800213  addi         x4, x0, 8  # x4 = 0x00000008
loc_954:
    954: 00012337  lui          x6, 0x00012  # x6 = 0x00012000 · TensixL1.KERNEL_CACHE_BASE
    958: fc030313  addi         x6, x6, -64  # x6 = 0x00011fc0
loc_95c:
    95c: 00032283  lw           x5, 0(x6)  # 0x00011fc0
    960: 00428663  beq          x5, x4, 0x0000096c  # target 0x0000096c
    964: 0ff0000f  fence        0xf, 0xf
    968: ff5ff06f  jal          x0, 0x0000095c  # target 0x0000095c
loc_96c:
    96c: 00032023  sw           x0, 0(x6)  # 0x00011fc0; write 0x00000000
    970: 00000393  addi         x7, x0, 0  # x7 = 0x00000000
    974: 00020413  addi         x8, x4, 0
loc_978:
    978: 0683fa63  bgeu         x7, x8, 0x000009ec  # target 0x000009ec
    97c: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    980: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    984: 0006a483  lw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898
    988: 00004537  lui          x10, 0x00004  # x10 = 0x00004000
    98c: 00a484b3  add          x9, x9, x10
    990: 0003f5b7  lui          x11, 0x0003f  # x11 = 0x0003f000 · arc_apb_reset_unit + 0xf000
    994: 88058593  addi         x11, x11, -1920  # x11 = 0x0003e880 · arc_apb_reset_unit + 0xe880
    998: 00b4e663  bltu         x9, x11, 0x000009a4  # target 0x000009a4
    99c: 00020637  lui          x12, 0x00020  # x12 = 0x00020000
    9a0: 40c484b3  sub          x9, x9, x12
loc_9a4:
    9a4: ffb016b7  lui          x13, 0xffb01  # x13 = 0xffb01000
    9a8: 89868693  addi         x13, x13, -1896  # x13 = 0xffb00898 · riscv_local_mem + 0x898
    9ac: 0096a023  sw           x9, 0(x13)  # riscv_local_mem + 0x898 · 0xffb00898; write runtime value
    9b0: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    9b4: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    9b8: 00052483  lw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c
    9bc: 00448493  addi         x9, x9, 4
    9c0: 01049493  slli         x9, x9, 16
    9c4: 0104d493  srli         x9, x9, 16
    9c8: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    9cc: 89c50513  addi         x10, x10, -1892  # x10 = 0xffb0089c · riscv_local_mem + 0x89c
    9d0: 00952023  sw           x9, 0(x10)  # riscv_local_mem + 0x89c · 0xffb0089c; write runtime value
    9d4: ffb50537  lui          x10, 0xffb50  # x10 = 0xffb50000
    9d8: 02850513  addi         x10, x10, 40  # x10 = 0xffb50028
    9dc: 00952023  sw           x9, 0(x10)  # 0xffb50028; write runtime value
    9e0: 0ff0000f  fence        0xf, 0xf
    9e4: 00138393  addi         x7, x7, 1
    9e8: f91ff06f  jal          x0, 0x00000978  # target 0x00000978
loc_9ec:
    9ec: 5200006f  jal          x0, 0x00000f0c  # target 0x00000f0c
loc_9f0:
    9f0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    9f4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb20284 · noc0_regs + 0x284
    9f8: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x284 · 0xffb20284
    9fc: 000a0463  beq          x20, x0, 0x00000a04  # target 0x00000a04
    a00: ff1ff06f  jal          x0, 0x000009f0  # target 0x000009f0
loc_a04:
    a04: 0ff0000f  fence        0xf, 0xf
    a08: 00008067  jalr         x0, 0(x1)
loc_a0c:
    a0c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a10: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    a14: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    a18: 000a0463  beq          x20, x0, 0x00000a20  # target 0x00000a20
    a1c: ff1ff06f  jal          x0, 0x00000a0c  # target 0x00000a0c
loc_a20:
    a20: 0ff0000f  fence        0xf, 0xf
    a24: 00008067  jalr         x0, 0(x1)
loc_a28:
    a28: 7a400a93  addi         x21, x0, 1956  # x21 = 0x000007a4
    a2c: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_cos; 0x000007a4
    a30: 007a7d13  andi         x26, x20, 7
    a34: ff8a7a13  andi         x20, x20, -8
    a38: 01af8ab3  add          x21, x31, x26
    a3c: 007afb93  andi         x23, x21, 7
    a40: 003ada93  srli         x21, x21, 3
    a44: 00ba9a93  slli         x21, x21, 11
    a48: 014a8ab3  add          x21, x21, x20
    a4c: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000a4c
    a50: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000a64
    a54: 001b9b93  slli         x23, x23, 1
    a58: 017b0b33  add          x22, x22, x23
    a5c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    a60: 00008067  jalr         x0, 0(x1)
    a64: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    a68: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    a6c: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    a70: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_a74:
    a74: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a78: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    a7c: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    a80: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    a84: 015a6463  bltu         x20, x21, 0x00000a8c  # target 0x00000a8c
    a88: fedff06f  jal          x0, 0x00000a74  # target 0x00000a74
loc_a8c:
    a8c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    a90: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    a94: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    a98: 014a1a13  slli         x20, x20, 20
    a9c: 014a5a13  srli         x20, x20, 20
    aa0: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_aa4:
    aa4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    aa8: 000b0463  beq          x22, x0, 0x00000ab0  # target 0x00000ab0
    aac: ff9ff06f  jal          x0, 0x00000aa4  # target 0x00000aa4
loc_ab0:
    ab0: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    ab4: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    ab8: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    abc: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    ac0: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    ac4: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    ac8: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    acc: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    ad0: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    ad4: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    ad8: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    adc: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    ae0: 08000c13  addi         x24, x0, 128  # x24 = 0x00000080
    ae4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000080
    ae8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    aec: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    af0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    af4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    af8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    afc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    b00: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_b04:
    b04: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    b08: 000b0463  beq          x22, x0, 0x00000b10  # target 0x00000b10
    b0c: ff9ff06f  jal          x0, 0x00000b04  # target 0x00000b04
loc_b10:
    b10: 00008067  jalr         x0, 0(x1)
loc_b14:
    b14: 7a800a93  addi         x21, x0, 1960  # x21 = 0x000007a8
    b18: 000aaa03  lw           x20, 0(x21)  # param e2e_rope_sin; 0x000007a8
    b1c: 007a7d13  andi         x26, x20, 7
    b20: ff8a7a13  andi         x20, x20, -8
    b24: 01af8ab3  add          x21, x31, x26
    b28: 007afb93  andi         x23, x21, 7
    b2c: 003ada93  srli         x21, x21, 3
    b30: 00ba9a93  slli         x21, x21, 11
    b34: 014a8ab3  add          x21, x21, x20
    b38: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000b38
    b3c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b50
    b40: 001b9b93  slli         x23, x23, 1
    b44: 017b0b33  add          x22, x22, x23
    b48: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b4c: 00008067  jalr         x0, 0(x1)
    b50: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    b54: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    b58: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    b5c: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_b60:
    b60: 79800a93  addi         x21, x0, 1944  # x21 = 0x00000798
    b64: 000aaa03  lw           x20, 0(x21)  # param e2e_q; 0x00000798
    b68: 007a7d13  andi         x26, x20, 7
    b6c: ff8a7a13  andi         x20, x20, -8
    b70: 01af8ab3  add          x21, x31, x26
    b74: 007afb93  andi         x23, x21, 7
    b78: 003ada93  srli         x21, x21, 3
    b7c: 00ba9a93  slli         x21, x21, 11
    b80: 014a8ab3  add          x21, x21, x20
    b84: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000b84
    b88: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000b9c
    b8c: 001b9b93  slli         x23, x23, 1
    b90: 017b0b33  add          x22, x22, x23
    b94: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    b98: 00008067  jalr         x0, 0(x1)
    b9c: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    ba0: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    ba4: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ba8: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_bac:
    bac: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bb0: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    bb4: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    bb8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    bbc: 015a6463  bltu         x20, x21, 0x00000bc4  # target 0x00000bc4
    bc0: fedff06f  jal          x0, 0x00000bac  # target 0x00000bac
loc_bc4:
    bc4: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    bc8: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    bcc: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    bd0: 014a1a13  slli         x20, x20, 20
    bd4: 014a5a13  srli         x20, x20, 20
    bd8: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_bdc:
    bdc: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    be0: 000b0463  beq          x22, x0, 0x00000be8  # target 0x00000be8
    be4: ff9ff06f  jal          x0, 0x00000bdc  # target 0x00000bdc
loc_be8:
    be8: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    bec: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    bf0: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    bf4: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    bf8: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    bfc: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    c00: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    c04: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    c08: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    c0c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    c10: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    c14: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    c18: 04000c13  addi         x24, x0, 64  # x24 = 0x00000040
    c1c: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000040
    c20: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    c24: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    c28: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    c2c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    c30: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    c34: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    c38: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_c3c:
    c3c: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    c40: 000b0463  beq          x22, x0, 0x00000c48  # target 0x00000c48
    c44: ff9ff06f  jal          x0, 0x00000c3c  # target 0x00000c3c
loc_c48:
    c48: 00008067  jalr         x0, 0(x1)
loc_c4c:
    c4c: 79c00a93  addi         x21, x0, 1948  # x21 = 0x0000079c
    c50: 000aaa03  lw           x20, 0(x21)  # param e2e_k; 0x0000079c
    c54: 007a7d13  andi         x26, x20, 7
    c58: ff8a7a13  andi         x20, x20, -8
    c5c: 01af8ab3  add          x21, x31, x26
    c60: 007afb93  andi         x23, x21, 7
    c64: 003ada93  srli         x21, x21, 3
    c68: 00ba9a93  slli         x21, x21, 11
    c6c: 014a8ab3  add          x21, x21, x20
    c70: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000c70
    c74: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000c88
    c78: 001b9b93  slli         x23, x23, 1
    c7c: 017b0b33  add          x22, x22, x23
    c80: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    c84: 00008067  jalr         x0, 0(x1)
    c88: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    c8c: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    c90: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    c94: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_c98:
    c98: 7a000a93  addi         x21, x0, 1952  # x21 = 0x000007a0
    c9c: 000aaa03  lw           x20, 0(x21)  # param e2e_v; 0x000007a0
    ca0: 007a7d13  andi         x26, x20, 7
    ca4: ff8a7a13  andi         x20, x20, -8
    ca8: 01af8ab3  add          x21, x31, x26
    cac: 007afb93  andi         x23, x21, 7
    cb0: 003ada93  srli         x21, x21, 3
    cb4: 00ba9a93  slli         x21, x21, 11
    cb8: 014a8ab3  add          x21, x21, x20
    cbc: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000cbc
    cc0: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000cd4
    cc4: 001b9b93  slli         x23, x23, 1
    cc8: 017b0b33  add          x22, x22, x23
    ccc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    cd0: 00008067  jalr         x0, 0(x1)
    cd4: 03d10391  XMOV         Mov_block_selection=1, Last=7618788  # Unreachable by statically known control flow
    cd8: 05510491  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    cdc: 04520392  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    ce0: 05d20512  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_ce4:
    ce4: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    ce8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    cec: 007a7d13  andi         x26, x20, 7
    cf0: ff8a7a13  andi         x20, x20, -8
    cf4: 01af8ab3  add          x21, x31, x26
    cf8: 007afb93  andi         x23, x21, 7
    cfc: 003ada93  srli         x21, x21, 3
    d00: 00ba9a93  slli         x21, x21, 11
    d04: 014a8ab3  add          x21, x21, x20
    d08: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000d08
    d0c: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000d20
    d10: 001b9b93  slli         x23, x23, 1
    d14: 017b0b33  add          x22, x22, x23
    d18: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    d1c: 00008067  jalr         x0, 0(x1)
    d20: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d24: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    d28: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    d2c: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_d30:
    d30: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    d34: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb20244 · noc0_regs + 0x244
    d38: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x244 · 0xffb20244
    d3c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    d40: 015a6463  bltu         x20, x21, 0x00000d48  # target 0x00000d48
    d44: fedff06f  jal          x0, 0x00000d30  # target 0x00000d30
loc_d48:
    d48: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
    d4c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb20148 · noc0_regs + 0x148
    d50: 000aaa03  lw           x20, 0(x21)  # noc0_regs + 0x148 · 0xffb20148
    d54: 014a1a13  slli         x20, x20, 20
    d58: 014a5a13  srli         x20, x20, 20
    d5c: ffb20ab7  lui          x21, 0xffb20  # x21 = 0xffb20000 · noc0_regs + 0x0
loc_d60:
    d60: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    d64: 000b0463  beq          x22, x0, 0x00000d6c  # target 0x00000d6c
    d68: ff9ff06f  jal          x0, 0x00000d60  # target 0x00000d60
loc_d6c:
    d6c: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    d70: 01fba023  sw           x31, 0(x23)  # noc0_regs + 0x0 · 0xffb20000; write runtime value
    d74: 000ba223  sw           x0, 4(x23)  # noc0_regs + 0x4 · 0xffb20004; write 0x00000000
    d78: 01eba423  sw           x30, 8(x23)  # noc0_regs + 0x8 · 0xffb20008; write runtime value
    d7c: 01dba623  sw           x29, 12(x23)  # noc0_regs + 0xc · 0xffb2000c; write runtime value
    d80: 000ba823  sw           x0, 16(x23)  # noc0_regs + 0x10 · 0xffb20010; write 0x00000000
    d84: 014baa23  sw           x20, 20(x23)  # noc0_regs + 0x14 · 0xffb20014; write runtime value
    d88: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    d8c: 018bac23  sw           x24, 24(x23)  # noc0_regs + 0x18 · 0xffb20018; write 0x00000400
    d90: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    d94: 090c0c13  addi         x24, x24, 144  # x24 = 0x00002090
    d98: 018bae23  sw           x24, 28(x23)  # noc0_regs + 0x1c · 0xffb2001c; write 0x00002090
    d9c: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    da0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    da4: 038ba023  sw           x24, 32(x23)  # noc0_regs + 0x20 · 0xffb20020; write 0x00000800
    da8: 020ba223  sw           x0, 36(x23)  # noc0_regs + 0x24 · 0xffb20024; write 0x00000000
    dac: 020ba423  sw           x0, 40(x23)  # noc0_regs + 0x28 · 0xffb20028; write 0x00000000
    db0: 020ba623  sw           x0, 44(x23)  # noc0_regs + 0x2c · 0xffb2002c; write 0x00000000
    db4: ffb20bb7  lui          x23, 0xffb20  # x23 = 0xffb20000 · noc0_regs + 0x0
    db8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb20040 · noc0_regs + 0x40
    dbc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    dc0: 018ba023  sw           x24, 0(x23)  # noc0_regs + 0x40 · 0xffb20040; write 0x00000001
loc_dc4:
    dc4: 040aab03  lw           x22, 64(x21)  # noc0_regs + 0x40 · 0xffb20040
    dc8: 000b0463  beq          x22, x0, 0x00000dd0  # target 0x00000dd0
    dcc: ff9ff06f  jal          x0, 0x00000dc4  # target 0x00000dc4
loc_dd0:
    dd0: 00008067  jalr         x0, 0(x1)
loc_dd4:
    dd4: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    dd8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    ddc: 007a7d13  andi         x26, x20, 7
    de0: ff8a7a13  andi         x20, x20, -8
    de4: 01af8ab3  add          x21, x31, x26
    de8: 007afb93  andi         x23, x21, 7
    dec: 003ada93  srli         x21, x21, 3
    df0: 00ba9a93  slli         x21, x21, 11
    df4: 014a8ab3  add          x21, x21, x20
    df8: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000df8
    dfc: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e10
    e00: 001b9b93  slli         x23, x23, 1
    e04: 017b0b33  add          x22, x22, x23
    e08: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e0c: 00008067  jalr         x0, 0(x1)
    e10: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e14: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e18: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    e1c: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_e20:
    e20: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    e24: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    e28: 007a7d13  andi         x26, x20, 7
    e2c: ff8a7a13  andi         x20, x20, -8
    e30: 01af8ab3  add          x21, x31, x26
    e34: 007afb93  andi         x23, x21, 7
    e38: 003ada93  srli         x21, x21, 3
    e3c: 00ba9a93  slli         x21, x21, 11
    e40: 014a8ab3  add          x21, x21, x20
    e44: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e44
    e48: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000e5c
    e4c: 001b9b93  slli         x23, x23, 1
    e50: 017b0b33  add          x22, x22, x23
    e54: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    e58: 00008067  jalr         x0, 0(x1)
    e5c: 03d10311  XMOV         Mov_block_selection=1, Last=7618756  # Unreachable by statically known control flow
    e60: 05d104d1  PACR         CfgContext=3, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    e64: 04120392  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=14, instr_mod1=4  # lreg_c: L0; lreg_dest: L14; Unreachable by statically known control flow
    e68: 05d20492  SFPLZ        imm12_math=1864, lreg_c=1, lreg_dest=2, instr_mod1=4  # lreg_c: L1; lreg_dest: L2; Unreachable by statically known control flow
loc_e6c:
    e6c: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    e70: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    e74: 007a7d13  andi         x26, x20, 7
    e78: ff8a7a13  andi         x20, x20, -8
    e7c: 01af8ab3  add          x21, x31, x26
    e80: 007afb93  andi         x23, x21, 7
    e84: 003ada93  srli         x21, x21, 3
    e88: 00ba9a93  slli         x21, x21, 11
    e8c: 014a8ab3  add          x21, x21, x20
    e90: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000e90
    e94: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000ea8
    e98: 001b9b93  slli         x23, x23, 1
    e9c: 017b0b33  add          x22, x22, x23
    ea0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    ea4: 00008067  jalr         x0, 0(x1)
    ea8: 04110391  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=6, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    eac: 05510511  PACR         CfgContext=2, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=4, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    eb0: 03d20352  SFPNOT       imm12_math=3912, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    eb4: 05920512  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=4, instr_mod1=4  # lreg_c: L1; lreg_dest: L4; Unreachable by statically known control flow
loc_eb8:
    eb8: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    ebc: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    ec0: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    ec4: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    ec8: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    ecc: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    ed0: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    ed4: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    ed8: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    edc: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    ee0: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    ee4: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    ee8: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    eec: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    ef0: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    ef4: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    ef8: 020f8f93  addi         x31, x31, 32
    efc: 020f0f13  addi         x30, x30, 32
    f00: ff8e8e93  addi         x29, x29, -8
    f04: fa0e9ae3  bne          x29, x0, 0x00000eb8  # target 0x00000eb8
    f08: 00008067  jalr         x0, 0(x1)
    f0c:           j FW_BRISC+4   # return to firmware, linked at install
