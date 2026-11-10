# llama3 8b-bf16 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=attention_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000212b7  lui          x5, 0x00021  # x5 = 0x00021000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x00020fc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00020fc0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000212b7  lui          x5, 0x00021  # x5 = 0x00021000
     2c: 7c028293  addi         x5, x5, 1984  # x5 = 0x000217c0
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x000217c0
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 0001d2b7  lui          x5, 0x0001d  # x5 = 0x0001d000
     4c: fc028293  addi         x5, x5, -64  # x5 = 0x0001cfc0
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x0001cfc0
     54: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     58: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     5c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     60: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     64: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     68: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     6c: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_70:
     70: ffb50437  lui          x8, 0xffb50  # x8 = 0xffb50000
     74: 02840413  addi         x8, x8, 40  # x8 = 0xffb50028
     78: 00045283  lhu          x5, 0(x8)  # 0xffb50028
     7c: 40428333  sub          x6, x5, x4
     80: 01031313  slli         x6, x6, 16
     84: 01035313  srli         x6, x6, 16
     88: 00737663  bgeu         x6, x7, 0x00000094  # target 0x00000094
     8c: 0ff0000f  fence        0xf, 0xf
     90: fe1ff06f  jal          x0, 0x00000070  # target 0x00000070
loc_94:
     94: 0ff0000f  fence        0xf, 0xf
     98: 0000f237  lui          x4, 0x0000f  # x4 = 0x0000f000
     9c: fc020213  addi         x4, x4, -64  # x4 = 0x0000efc0
     a0: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     a4: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
loc_a8:
     a8: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     ac: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     b0: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     b4: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     b8: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     bc: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     c0: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     c4: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     c8: 02020213  addi         x4, x4, 32
     cc: ff828293  addi         x5, x5, -8
     d0: fc029ce3  bne          x5, x0, 0x000000a8  # target 0x000000a8
     d4: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
     d8: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00020fc0
     dc: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
     e0: fc0f0f13  addi         x30, x30, -64  # x30 = 0x0000efc0
     e4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     e8: 624000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x000000ec
     ec: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
     f0: fe0f8f93  addi         x31, x31, -32  # x31 = 0x00020fe0
     f4: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
     f8: 1c0f0f13  addi         x30, x30, 448  # x30 = 0x0000f1c0
     fc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    100: 60c000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000104
    104: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    108: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    10c: 7c0f0f13  addi         x30, x30, 1984  # x30 = 0x0000f7c0
    110: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    114: 5f8000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000118
    118: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    11c: 020f8f93  addi         x31, x31, 32  # x31 = 0x00021020
    120: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    124: 9c0f0f13  addi         x30, x30, -1600  # x30 = 0x0000f9c0
    128: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    12c: 5e0000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000130
    130: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    134: 040f8f93  addi         x31, x31, 64  # x31 = 0x00021040
    138: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    13c: fc0f0f13  addi         x30, x30, -64  # x30 = 0x0000ffc0
    140: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    144: 5c8000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000148
    148: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    14c: 060f8f93  addi         x31, x31, 96  # x31 = 0x00021060
    150: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    154: 1c0f0f13  addi         x30, x30, 448  # x30 = 0x000101c0
    158: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    15c: 5b0000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000160
    160: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    164: 080f8f93  addi         x31, x31, 128  # x31 = 0x00021080
    168: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    16c: 7c0f0f13  addi         x30, x30, 1984  # x30 = 0x000107c0
    170: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    174: 598000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000178
    178: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    17c: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x000210a0
    180: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    184: 9c0f0f13  addi         x30, x30, -1600  # x30 = 0x000109c0
    188: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    18c: 580000ef  jal          x1, 0x0000070c  # target 0x0000070c; x1 = 0x00000190
    190: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    194: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    198: 00525293  srli         x5, x4, 5
    19c: 00229293  slli         x5, x5, 2
    1a0: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    1a4: 90040413  addi         x8, x8, -1792  # x8 = 0x0000e900
    1a8: 00042383  lw           x7, 0(x8)  # param attention_core; 0x0000e900
    1ac: 0023d393  srli         x7, x7, 2
    1b0: 00a39393  slli         x7, x7, 10
    1b4: 007282b3  add          x5, x5, x7
    1b8: 00f27313  andi         x6, x4, 15
    1bc: 00531313  slli         x6, x6, 5
    1c0: 01027393  andi         x7, x4, 16
    1c4: 00639393  slli         x7, x7, 6
    1c8: 00730333  add          x6, x6, x7
    1cc: 594000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x000001d0
    1d0: 5ac000ef  jal          x1, 0x0000077c  # target 0x0000077c; x1 = 0x000001d4
    1d4: 00028393  addi         x7, x5, 0
    1d8: 00038f93  addi         x31, x7, 0
    1dc: 5bc000ef  jal          x1, 0x00000798  # target 0x00000798; x1 = 0x000001e0
    1e0: 000a8413  addi         x8, x21, 0
    1e4: 000b0493  addi         x9, x22, 0
    1e8: 00640533  add          x10, x8, x6
    1ec: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    1f0: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x000210c0
    1f4: 00050f13  addi         x30, x10, 0
    1f8: 00048e93  addi         x29, x9, 0
    1fc: 5e8000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000200
    200: 00640533  add          x10, x8, x6
    204: 20050513  addi         x10, x10, 512
    208: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    20c: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x000210e0
    210: 00050f13  addi         x30, x10, 0
    214: 00048e93  addi         x29, x9, 0
    218: 5cc000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x0000021c
    21c: 00038f93  addi         x31, x7, 0
    220: 67c000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x00000224
    224: 000a8513  addi         x10, x21, 0
    228: 000b0593  addi         x11, x22, 0
    22c: 00650633  add          x12, x10, x6
    230: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    234: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00035fc0 · arc_apb_reset_unit + 0x5fc0
    238: 00060f13  addi         x30, x12, 0
    23c: 00058e93  addi         x29, x11, 0
    240: 5a4000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000244
    244: 00650633  add          x12, x10, x6
    248: 20060613  addi         x12, x12, 512
    24c: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    250: fe0f8f93  addi         x31, x31, -32  # x31 = 0x00035fe0 · arc_apb_reset_unit + 0x5fe0
    254: 00060f13  addi         x30, x12, 0
    258: 00058e93  addi         x29, x11, 0
    25c: 588000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000260
    260: 00128393  addi         x7, x5, 1
    264: 00038f93  addi         x31, x7, 0
    268: 530000ef  jal          x1, 0x00000798  # target 0x00000798; x1 = 0x0000026c
    26c: 000a8413  addi         x8, x21, 0
    270: 000b0493  addi         x9, x22, 0
    274: 00640533  add          x10, x8, x6
    278: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    27c: 100f8f93  addi         x31, x31, 256  # x31 = 0x00021100
    280: 00050f13  addi         x30, x10, 0
    284: 00048e93  addi         x29, x9, 0
    288: 55c000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x0000028c
    28c: 00640533  add          x10, x8, x6
    290: 20050513  addi         x10, x10, 512
    294: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    298: 120f8f93  addi         x31, x31, 288  # x31 = 0x00021120
    29c: 00050f13  addi         x30, x10, 0
    2a0: 00048e93  addi         x29, x9, 0
    2a4: 540000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000002a8
    2a8: 00038f93  addi         x31, x7, 0
    2ac: 5f0000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000002b0
    2b0: 000a8513  addi         x10, x21, 0
    2b4: 000b0593  addi         x11, x22, 0
    2b8: 00650633  add          x12, x10, x6
    2bc: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    2c0: 00060f13  addi         x30, x12, 0
    2c4: 00058e93  addi         x29, x11, 0
    2c8: 51c000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000002cc
    2cc: 00650633  add          x12, x10, x6
    2d0: 20060613  addi         x12, x12, 512
    2d4: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    2d8: 020f8f93  addi         x31, x31, 32  # x31 = 0x00036020 · arc_apb_reset_unit + 0x6020
    2dc: 00060f13  addi         x30, x12, 0
    2e0: 00058e93  addi         x29, x11, 0
    2e4: 500000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000002e8
    2e8: 00228393  addi         x7, x5, 2
    2ec: 00038f93  addi         x31, x7, 0
    2f0: 4a8000ef  jal          x1, 0x00000798  # target 0x00000798; x1 = 0x000002f4
    2f4: 000a8413  addi         x8, x21, 0
    2f8: 000b0493  addi         x9, x22, 0
    2fc: 00640533  add          x10, x8, x6
    300: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    304: 140f8f93  addi         x31, x31, 320  # x31 = 0x00021140
    308: 00050f13  addi         x30, x10, 0
    30c: 00048e93  addi         x29, x9, 0
    310: 4d4000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000314
    314: 00640533  add          x10, x8, x6
    318: 20050513  addi         x10, x10, 512
    31c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    320: 160f8f93  addi         x31, x31, 352  # x31 = 0x00021160
    324: 00050f13  addi         x30, x10, 0
    328: 00048e93  addi         x29, x9, 0
    32c: 4b8000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000330
    330: 00038f93  addi         x31, x7, 0
    334: 568000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x00000338
    338: 000a8513  addi         x10, x21, 0
    33c: 000b0593  addi         x11, x22, 0
    340: 00650633  add          x12, x10, x6
    344: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    348: 040f8f93  addi         x31, x31, 64  # x31 = 0x00036040 · arc_apb_reset_unit + 0x6040
    34c: 00060f13  addi         x30, x12, 0
    350: 00058e93  addi         x29, x11, 0
    354: 490000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000358
    358: 00650633  add          x12, x10, x6
    35c: 20060613  addi         x12, x12, 512
    360: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    364: 060f8f93  addi         x31, x31, 96  # x31 = 0x00036060 · arc_apb_reset_unit + 0x6060
    368: 00060f13  addi         x30, x12, 0
    36c: 00058e93  addi         x29, x11, 0
    370: 474000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000374
    374: 00328393  addi         x7, x5, 3
    378: 00038f93  addi         x31, x7, 0
    37c: 41c000ef  jal          x1, 0x00000798  # target 0x00000798; x1 = 0x00000380
    380: 000a8413  addi         x8, x21, 0
    384: 000b0493  addi         x9, x22, 0
    388: 00640533  add          x10, x8, x6
    38c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    390: 180f8f93  addi         x31, x31, 384  # x31 = 0x00021180
    394: 00050f13  addi         x30, x10, 0
    398: 00048e93  addi         x29, x9, 0
    39c: 448000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000003a0
    3a0: 00640533  add          x10, x8, x6
    3a4: 20050513  addi         x10, x10, 512
    3a8: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    3ac: 1a0f8f93  addi         x31, x31, 416  # x31 = 0x000211a0
    3b0: 00050f13  addi         x30, x10, 0
    3b4: 00048e93  addi         x29, x9, 0
    3b8: 42c000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000003bc
    3bc: 00038f93  addi         x31, x7, 0
    3c0: 4dc000ef  jal          x1, 0x0000089c  # target 0x0000089c; x1 = 0x000003c4
    3c4: 000a8513  addi         x10, x21, 0
    3c8: 000b0593  addi         x11, x22, 0
    3cc: 00650633  add          x12, x10, x6
    3d0: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    3d4: 080f8f93  addi         x31, x31, 128  # x31 = 0x00036080 · arc_apb_reset_unit + 0x6080
    3d8: 00060f13  addi         x30, x12, 0
    3dc: 00058e93  addi         x29, x11, 0
    3e0: 404000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000003e4
    3e4: 00650633  add          x12, x10, x6
    3e8: 20060613  addi         x12, x12, 512
    3ec: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    3f0: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x000360a0 · arc_apb_reset_unit + 0x60a0
    3f4: 00060f13  addi         x30, x12, 0
    3f8: 00058e93  addi         x29, x11, 0
    3fc: 3e8000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000400
    400: 360000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000404
    404: 378000ef  jal          x1, 0x0000077c  # target 0x0000077c; x1 = 0x00000408
    408: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    40c: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    410: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    414: 00120213  addi         x4, x4, 1
    418: 01021213  slli         x4, x4, 16
    41c: 01025213  srli         x4, x4, 16
    420: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    424: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    428: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    42c: ffb502b7  lui          x5, 0xffb50  # x5 = 0xffb50000
    430: 02028293  addi         x5, x5, 32  # x5 = 0xffb50020
    434: 0042a023  sw           x4, 0(x5)  # 0xffb50020; write runtime value
    438: 0ff0000f  fence        0xf, 0xf
    43c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    440: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    444: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    448: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    44c: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    450: 00520233  add          x4, x4, x5
    454: 00021337  lui          x6, 0x00021  # x6 = 0x00021000
    458: 7c030313  addi         x6, x6, 1984  # x6 = 0x000217c0
    45c: 00626863  bltu         x4, x6, 0x0000046c  # target 0x0000046c
    460: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    464: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    468: 40720233  sub          x4, x4, x7
loc_46c:
    46c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    470: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    474: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    478: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    47c: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    480: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    484: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    488: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    48c: 00520233  add          x4, x4, x5
    490: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    494: fc030313  addi         x6, x6, -64  # x6 = 0x00021fc0
    498: 00626863  bltu         x4, x6, 0x000004a8  # target 0x000004a8
    49c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4a0: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    4a4: 40720233  sub          x4, x4, x7
loc_4a8:
    4a8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4ac: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    4b0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    4b4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4b8: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4bc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    4c0: 00120213  addi         x4, x4, 1
    4c4: 01021213  slli         x4, x4, 16
    4c8: 01025213  srli         x4, x4, 16
    4cc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4d0: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4d4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    4d8: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
    4dc: 02828293  addi         x5, x5, 40  # x5 = 0xffb51028
    4e0: 0042a023  sw           x4, 0(x5)  # 0xffb51028; write runtime value
    4e4: 0ff0000f  fence        0xf, 0xf
    4e8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4ec: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    4f0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    4f4: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_4f8:
    4f8: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    4fc: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    500: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    504: 40428333  sub          x6, x5, x4
    508: 01031313  slli         x6, x6, 16
    50c: 01035313  srli         x6, x6, 16
    510: 00737663  bgeu         x6, x7, 0x0000051c  # target 0x0000051c
    514: 0ff0000f  fence        0xf, 0xf
    518: fe1ff06f  jal          x0, 0x000004f8  # target 0x000004f8
loc_51c:
    51c: 0ff0000f  fence        0xf, 0xf
    520: 240000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x00000524
    524: 258000ef  jal          x1, 0x0000077c  # target 0x0000077c; x1 = 0x00000528
    528: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    52c: 90028293  addi         x5, x5, -1792  # x5 = 0x0000e900
    530: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x0000e900
    534: 00721213  slli         x4, x4, 7
    538: 00020293  addi         x5, x4, 0
    53c: 00a2d313  srli         x6, x5, 10
    540: 00030f93  addi         x31, x6, 0
    544: 3a4000ef  jal          x1, 0x000008e8  # target 0x000008e8; x1 = 0x00000548
    548: 000a8393  addi         x7, x21, 0
    54c: 000b0413  addi         x8, x22, 0
    550: 3ff2f293  andi         x5, x5, 1023
    554: 00129493  slli         x9, x5, 1
    558: 007484b3  add          x9, x9, x7
    55c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    560: fc0f8f93  addi         x31, x31, -64  # x31 = 0x0001cfc0
    564: 00048f13  addi         x30, x9, 0
    568: 00040e93  addi         x29, x8, 0
    56c: 278000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000570
    570: 01028293  addi         x5, x5, 16
    574: 00129493  slli         x9, x5, 1
    578: 007484b3  add          x9, x9, x7
    57c: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    580: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x0001d1c0
    584: 00048f13  addi         x30, x9, 0
    588: 00040e93  addi         x29, x8, 0
    58c: 258000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000590
    590: 02020293  addi         x5, x4, 32
    594: 00a2d313  srli         x6, x5, 10
    598: 00030f93  addi         x31, x6, 0
    59c: 34c000ef  jal          x1, 0x000008e8  # target 0x000008e8; x1 = 0x000005a0
    5a0: 000a8393  addi         x7, x21, 0
    5a4: 000b0413  addi         x8, x22, 0
    5a8: 3ff2f293  andi         x5, x5, 1023
    5ac: 00129493  slli         x9, x5, 1
    5b0: 007484b3  add          x9, x9, x7
    5b4: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    5b8: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x0001d7c0
    5bc: 00048f13  addi         x30, x9, 0
    5c0: 00040e93  addi         x29, x8, 0
    5c4: 220000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000005c8
    5c8: 01028293  addi         x5, x5, 16
    5cc: 00129493  slli         x9, x5, 1
    5d0: 007484b3  add          x9, x9, x7
    5d4: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    5d8: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x0001d9c0
    5dc: 00048f13  addi         x30, x9, 0
    5e0: 00040e93  addi         x29, x8, 0
    5e4: 200000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x000005e8
    5e8: 04020293  addi         x5, x4, 64
    5ec: 00a2d313  srli         x6, x5, 10
    5f0: 00030f93  addi         x31, x6, 0
    5f4: 2f4000ef  jal          x1, 0x000008e8  # target 0x000008e8; x1 = 0x000005f8
    5f8: 000a8393  addi         x7, x21, 0
    5fc: 000b0413  addi         x8, x22, 0
    600: 3ff2f293  andi         x5, x5, 1023
    604: 00129493  slli         x9, x5, 1
    608: 007484b3  add          x9, x9, x7
    60c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    610: fc0f8f93  addi         x31, x31, -64  # x31 = 0x0001dfc0
    614: 00048f13  addi         x30, x9, 0
    618: 00040e93  addi         x29, x8, 0
    61c: 1c8000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000620
    620: 01028293  addi         x5, x5, 16
    624: 00129493  slli         x9, x5, 1
    628: 007484b3  add          x9, x9, x7
    62c: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    630: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x0001e1c0
    634: 00048f13  addi         x30, x9, 0
    638: 00040e93  addi         x29, x8, 0
    63c: 1a8000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000640
    640: 06020293  addi         x5, x4, 96
    644: 00a2d313  srli         x6, x5, 10
    648: 00030f93  addi         x31, x6, 0
    64c: 29c000ef  jal          x1, 0x000008e8  # target 0x000008e8; x1 = 0x00000650
    650: 000a8393  addi         x7, x21, 0
    654: 000b0413  addi         x8, x22, 0
    658: 3ff2f293  andi         x5, x5, 1023
    65c: 00129493  slli         x9, x5, 1
    660: 007484b3  add          x9, x9, x7
    664: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    668: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x0001e7c0
    66c: 00048f13  addi         x30, x9, 0
    670: 00040e93  addi         x29, x8, 0
    674: 170000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000678
    678: 01028293  addi         x5, x5, 16
    67c: 00129493  slli         x9, x5, 1
    680: 007484b3  add          x9, x9, x7
    684: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    688: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x0001e9c0
    68c: 00048f13  addi         x30, x9, 0
    690: 00040e93  addi         x29, x8, 0
    694: 150000ef  jal          x1, 0x000007e4  # target 0x000007e4; x1 = 0x00000698
    698: 0c8000ef  jal          x1, 0x00000760  # target 0x00000760; x1 = 0x0000069c
    69c: 0e0000ef  jal          x1, 0x0000077c  # target 0x0000077c; x1 = 0x000006a0
    6a0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6a4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    6a8: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    6ac: 00420213  addi         x4, x4, 4
    6b0: 01021213  slli         x4, x4, 16
    6b4: 01025213  srli         x4, x4, 16
    6b8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6bc: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    6c0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    6c4: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    6c8: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    6cc: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    6d0: 0ff0000f  fence        0xf, 0xf
    6d4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6d8: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    6dc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    6e0: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    6e4: 00520233  add          x4, x4, x5
    6e8: 0001f337  lui          x6, 0x0001f  # x6 = 0x0001f000
    6ec: fc030313  addi         x6, x6, -64  # x6 = 0x0001efc0
    6f0: 00626663  bltu         x4, x6, 0x000006fc  # target 0x000006fc
    6f4: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    6f8: 40720233  sub          x4, x4, x7
loc_6fc:
    6fc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    700: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    704: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    708: 22c0006f  jal          x0, 0x00000934  # target 0x00000934
loc_70c:
    70c: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    710: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    714: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    718: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    71c: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    720: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    724: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    728: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    72c: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    730: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    734: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    738: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    73c: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    740: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    744: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    748: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    74c: 020f8f93  addi         x31, x31, 32
    750: 020f0f13  addi         x30, x30, 32
    754: ff8e8e93  addi         x29, x29, -8
    758: fa0e9ae3  bne          x29, x0, 0x0000070c  # target 0x0000070c
    75c: 00008067  jalr         x0, 0(x1)
loc_760:
    760: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    764: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    768: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    76c: 000a0463  beq          x20, x0, 0x00000774  # target 0x00000774
    770: ff1ff06f  jal          x0, 0x00000760  # target 0x00000760
loc_774:
    774: 0ff0000f  fence        0xf, 0xf
    778: 00008067  jalr         x0, 0(x1)
loc_77c:
    77c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    780: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    784: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    788: 000a0463  beq          x20, x0, 0x00000790  # target 0x00000790
    78c: ff1ff06f  jal          x0, 0x0000077c  # target 0x0000077c
loc_790:
    790: 0ff0000f  fence        0xf, 0xf
    794: 00008067  jalr         x0, 0(x1)
loc_798:
    798: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    79c: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    7a0: 007a7d13  andi         x26, x20, 7
    7a4: ff8a7a13  andi         x20, x20, -8
    7a8: 01af8ab3  add          x21, x31, x26
    7ac: 007afb93  andi         x23, x21, 7
    7b0: 003ada93  srli         x21, x21, 3
    7b4: 00ba9a93  slli         x21, x21, 11
    7b8: 014a8ab3  add          x21, x21, x20
    7bc: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007bc
    7c0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007d4
    7c4: 001b9b93  slli         x23, x23, 1
    7c8: 017b0b33  add          x22, x22, x23
    7cc: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7d0: 00008067  jalr         x0, 0(x1)
    7d4: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7d8: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7dc: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7e0: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_7e4:
    7e4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    7e8: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    7ec: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    7f0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    7f4: 015a6463  bltu         x20, x21, 0x000007fc  # target 0x000007fc
    7f8: fedff06f  jal          x0, 0x000007e4  # target 0x000007e4
loc_7fc:
    7fc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    800: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    804: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    808: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    80c: 015a6463  bltu         x20, x21, 0x00000814  # target 0x00000814
    810: fedff06f  jal          x0, 0x000007fc  # target 0x000007fc
loc_814:
    814: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    818: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    81c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    820: 014a1a13  slli         x20, x20, 20
    824: 014a5a13  srli         x20, x20, 20
    828: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_82c:
    82c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    830: 000b0463  beq          x22, x0, 0x00000838  # target 0x00000838
    834: ff9ff06f  jal          x0, 0x0000082c  # target 0x0000082c
loc_838:
    838: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    83c: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    840: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    844: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    848: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    84c: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    850: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    854: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    858: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    85c: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    860: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    864: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    868: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    86c: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    870: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    874: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    878: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    87c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    880: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    884: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    888: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_88c:
    88c: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    890: 000b0463  beq          x22, x0, 0x00000898  # target 0x00000898
    894: ff9ff06f  jal          x0, 0x0000088c  # target 0x0000088c
loc_898:
    898: 00008067  jalr         x0, 0(x1)
loc_89c:
    89c: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    8a0: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    8a4: 007a7d13  andi         x26, x20, 7
    8a8: ff8a7a13  andi         x20, x20, -8
    8ac: 01af8ab3  add          x21, x31, x26
    8b0: 007afb93  andi         x23, x21, 7
    8b4: 003ada93  srli         x21, x21, 3
    8b8: 00ba9a93  slli         x21, x21, 11
    8bc: 014a8ab3  add          x21, x21, x20
    8c0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000008c0
    8c4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000008d8
    8c8: 001b9b93  slli         x23, x23, 1
    8cc: 017b0b33  add          x22, x22, x23
    8d0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    8d4: 00008067  jalr         x0, 0(x1)
    8d8: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8dc: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8e0: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    8e4: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_8e8:
    8e8: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    8ec: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x0000078c
    8f0: 007a7d13  andi         x26, x20, 7
    8f4: ff8a7a13  andi         x20, x20, -8
    8f8: 01af8ab3  add          x21, x31, x26
    8fc: 007afb93  andi         x23, x21, 7
    900: 003ada93  srli         x21, x21, 3
    904: 00ba9a93  slli         x21, x21, 11
    908: 014a8ab3  add          x21, x21, x20
    90c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000090c
    910: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000924
    914: 001b9b93  slli         x23, x23, 1
    918: 017b0b33  add          x22, x22, x23
    91c: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    920: 00008067  jalr         x0, 0(x1)
    924: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    928: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    92c: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    930: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    934:           j FW_NCRISC+4   # return to firmware, linked at install
