# llama3 8b-fp8 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=attention_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000212b7  lui          x5, 0x00021  # x5 = 0x00021000
      c: 04028293  addi         x5, x5, 64  # x5 = 0x00021040
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00021040
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 000222b7  lui          x5, 0x00022  # x5 = 0x00022000
     2c: 84028293  addi         x5, x5, -1984  # x5 = 0x00021840
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x00021840
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 0001d2b7  lui          x5, 0x0001d  # x5 = 0x0001d000
     4c: 04028293  addi         x5, x5, 64  # x5 = 0x0001d040
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x0001d040
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
     9c: 04020213  addi         x4, x4, 64  # x4 = 0x0000f040
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
     d8: 040f8f93  addi         x31, x31, 64  # x31 = 0x00021040
     dc: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
     e0: 040f0f13  addi         x30, x30, 64  # x30 = 0x0000f040
     e4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     e8: 62c000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x000000ec
     ec: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
     f0: 060f8f93  addi         x31, x31, 96  # x31 = 0x00021060
     f4: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
     f8: 240f0f13  addi         x30, x30, 576  # x30 = 0x0000f240
     fc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    100: 614000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000104
    104: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    108: 080f8f93  addi         x31, x31, 128  # x31 = 0x00021080
    10c: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    110: 840f0f13  addi         x30, x30, -1984  # x30 = 0x0000f840
    114: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    118: 5fc000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x0000011c
    11c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    120: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x000210a0
    124: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    128: a40f0f13  addi         x30, x30, -1472  # x30 = 0x0000fa40
    12c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    130: 5e4000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000134
    134: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    138: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x000210c0
    13c: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    140: 040f0f13  addi         x30, x30, 64  # x30 = 0x00010040
    144: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    148: 5cc000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x0000014c
    14c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    150: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x000210e0
    154: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    158: 240f0f13  addi         x30, x30, 576  # x30 = 0x00010240
    15c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    160: 5b4000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000164
    164: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    168: 100f8f93  addi         x31, x31, 256  # x31 = 0x00021100
    16c: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    170: 840f0f13  addi         x30, x30, -1984  # x30 = 0x00010840
    174: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    178: 59c000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x0000017c
    17c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    180: 120f8f93  addi         x31, x31, 288  # x31 = 0x00021120
    184: 00011f37  lui          x30, 0x00011  # x30 = 0x00011000
    188: a40f0f13  addi         x30, x30, -1472  # x30 = 0x00010a40
    18c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    190: 584000ef  jal          x1, 0x00000714  # target 0x00000714; x1 = 0x00000194
    194: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    198: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    19c: 00525293  srli         x5, x4, 5
    1a0: 00229293  slli         x5, x5, 2
    1a4: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    1a8: 90040413  addi         x8, x8, -1792  # x8 = 0x0000e900
    1ac: 00042383  lw           x7, 0(x8)  # param attention_core; 0x0000e900
    1b0: 0023d393  srli         x7, x7, 2
    1b4: 00a39393  slli         x7, x7, 10
    1b8: 007282b3  add          x5, x5, x7
    1bc: 00f27313  andi         x6, x4, 15
    1c0: 00531313  slli         x6, x6, 5
    1c4: 01027393  andi         x7, x4, 16
    1c8: 00639393  slli         x7, x7, 6
    1cc: 00730333  add          x6, x6, x7
    1d0: 598000ef  jal          x1, 0x00000768  # target 0x00000768; x1 = 0x000001d4
    1d4: 5b0000ef  jal          x1, 0x00000784  # target 0x00000784; x1 = 0x000001d8
    1d8: 00028393  addi         x7, x5, 0
    1dc: 00038f93  addi         x31, x7, 0
    1e0: 5c0000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x000001e4
    1e4: 000a8413  addi         x8, x21, 0
    1e8: 000b0493  addi         x9, x22, 0
    1ec: 00640533  add          x10, x8, x6
    1f0: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    1f4: 140f8f93  addi         x31, x31, 320  # x31 = 0x00021140
    1f8: 00050f13  addi         x30, x10, 0
    1fc: 00048e93  addi         x29, x9, 0
    200: 5ec000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000204
    204: 00640533  add          x10, x8, x6
    208: 20050513  addi         x10, x10, 512
    20c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    210: 160f8f93  addi         x31, x31, 352  # x31 = 0x00021160
    214: 00050f13  addi         x30, x10, 0
    218: 00048e93  addi         x29, x9, 0
    21c: 5d0000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000220
    220: 00038f93  addi         x31, x7, 0
    224: 680000ef  jal          x1, 0x000008a4  # target 0x000008a4; x1 = 0x00000228
    228: 000a8513  addi         x10, x21, 0
    22c: 000b0593  addi         x11, x22, 0
    230: 00650633  add          x12, x10, x6
    234: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    238: 040f8f93  addi         x31, x31, 64  # x31 = 0x00036040 · arc_apb_reset_unit + 0x6040
    23c: 00060f13  addi         x30, x12, 0
    240: 00058e93  addi         x29, x11, 0
    244: 5a8000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000248
    248: 00650633  add          x12, x10, x6
    24c: 20060613  addi         x12, x12, 512
    250: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    254: 060f8f93  addi         x31, x31, 96  # x31 = 0x00036060 · arc_apb_reset_unit + 0x6060
    258: 00060f13  addi         x30, x12, 0
    25c: 00058e93  addi         x29, x11, 0
    260: 58c000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000264
    264: 00128393  addi         x7, x5, 1
    268: 00038f93  addi         x31, x7, 0
    26c: 534000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x00000270
    270: 000a8413  addi         x8, x21, 0
    274: 000b0493  addi         x9, x22, 0
    278: 00640533  add          x10, x8, x6
    27c: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    280: 180f8f93  addi         x31, x31, 384  # x31 = 0x00021180
    284: 00050f13  addi         x30, x10, 0
    288: 00048e93  addi         x29, x9, 0
    28c: 560000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000290
    290: 00640533  add          x10, x8, x6
    294: 20050513  addi         x10, x10, 512
    298: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    29c: 1a0f8f93  addi         x31, x31, 416  # x31 = 0x000211a0
    2a0: 00050f13  addi         x30, x10, 0
    2a4: 00048e93  addi         x29, x9, 0
    2a8: 544000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000002ac
    2ac: 00038f93  addi         x31, x7, 0
    2b0: 5f4000ef  jal          x1, 0x000008a4  # target 0x000008a4; x1 = 0x000002b4
    2b4: 000a8513  addi         x10, x21, 0
    2b8: 000b0593  addi         x11, x22, 0
    2bc: 00650633  add          x12, x10, x6
    2c0: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    2c4: 080f8f93  addi         x31, x31, 128  # x31 = 0x00036080 · arc_apb_reset_unit + 0x6080
    2c8: 00060f13  addi         x30, x12, 0
    2cc: 00058e93  addi         x29, x11, 0
    2d0: 51c000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000002d4
    2d4: 00650633  add          x12, x10, x6
    2d8: 20060613  addi         x12, x12, 512
    2dc: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    2e0: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x000360a0 · arc_apb_reset_unit + 0x60a0
    2e4: 00060f13  addi         x30, x12, 0
    2e8: 00058e93  addi         x29, x11, 0
    2ec: 500000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000002f0
    2f0: 00228393  addi         x7, x5, 2
    2f4: 00038f93  addi         x31, x7, 0
    2f8: 4a8000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x000002fc
    2fc: 000a8413  addi         x8, x21, 0
    300: 000b0493  addi         x9, x22, 0
    304: 00640533  add          x10, x8, x6
    308: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    30c: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x000211c0
    310: 00050f13  addi         x30, x10, 0
    314: 00048e93  addi         x29, x9, 0
    318: 4d4000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x0000031c
    31c: 00640533  add          x10, x8, x6
    320: 20050513  addi         x10, x10, 512
    324: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    328: 1e0f8f93  addi         x31, x31, 480  # x31 = 0x000211e0
    32c: 00050f13  addi         x30, x10, 0
    330: 00048e93  addi         x29, x9, 0
    334: 4b8000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000338
    338: 00038f93  addi         x31, x7, 0
    33c: 568000ef  jal          x1, 0x000008a4  # target 0x000008a4; x1 = 0x00000340
    340: 000a8513  addi         x10, x21, 0
    344: 000b0593  addi         x11, x22, 0
    348: 00650633  add          x12, x10, x6
    34c: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    350: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x000360c0 · arc_apb_reset_unit + 0x60c0
    354: 00060f13  addi         x30, x12, 0
    358: 00058e93  addi         x29, x11, 0
    35c: 490000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000360
    360: 00650633  add          x12, x10, x6
    364: 20060613  addi         x12, x12, 512
    368: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    36c: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x000360e0 · arc_apb_reset_unit + 0x60e0
    370: 00060f13  addi         x30, x12, 0
    374: 00058e93  addi         x29, x11, 0
    378: 474000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x0000037c
    37c: 00328393  addi         x7, x5, 3
    380: 00038f93  addi         x31, x7, 0
    384: 41c000ef  jal          x1, 0x000007a0  # target 0x000007a0; x1 = 0x00000388
    388: 000a8413  addi         x8, x21, 0
    38c: 000b0493  addi         x9, x22, 0
    390: 00640533  add          x10, x8, x6
    394: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    398: 200f8f93  addi         x31, x31, 512  # x31 = 0x00021200
    39c: 00050f13  addi         x30, x10, 0
    3a0: 00048e93  addi         x29, x9, 0
    3a4: 448000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000003a8
    3a8: 00640533  add          x10, x8, x6
    3ac: 20050513  addi         x10, x10, 512
    3b0: 00021fb7  lui          x31, 0x00021  # x31 = 0x00021000
    3b4: 220f8f93  addi         x31, x31, 544  # x31 = 0x00021220
    3b8: 00050f13  addi         x30, x10, 0
    3bc: 00048e93  addi         x29, x9, 0
    3c0: 42c000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000003c4
    3c4: 00038f93  addi         x31, x7, 0
    3c8: 4dc000ef  jal          x1, 0x000008a4  # target 0x000008a4; x1 = 0x000003cc
    3cc: 000a8513  addi         x10, x21, 0
    3d0: 000b0593  addi         x11, x22, 0
    3d4: 00650633  add          x12, x10, x6
    3d8: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    3dc: 100f8f93  addi         x31, x31, 256  # x31 = 0x00036100 · arc_apb_reset_unit + 0x6100
    3e0: 00060f13  addi         x30, x12, 0
    3e4: 00058e93  addi         x29, x11, 0
    3e8: 404000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000003ec
    3ec: 00650633  add          x12, x10, x6
    3f0: 20060613  addi         x12, x12, 512
    3f4: 00036fb7  lui          x31, 0x00036  # x31 = 0x00036000 · arc_apb_reset_unit + 0x6000
    3f8: 120f8f93  addi         x31, x31, 288  # x31 = 0x00036120 · arc_apb_reset_unit + 0x6120
    3fc: 00060f13  addi         x30, x12, 0
    400: 00058e93  addi         x29, x11, 0
    404: 3e8000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000408
    408: 360000ef  jal          x1, 0x00000768  # target 0x00000768; x1 = 0x0000040c
    40c: 378000ef  jal          x1, 0x00000784  # target 0x00000784; x1 = 0x00000410
    410: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    414: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    418: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    41c: 00120213  addi         x4, x4, 1
    420: 01021213  slli         x4, x4, 16
    424: 01025213  srli         x4, x4, 16
    428: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    42c: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    430: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    434: ffb502b7  lui          x5, 0xffb50  # x5 = 0xffb50000
    438: 02028293  addi         x5, x5, 32  # x5 = 0xffb50020
    43c: 0042a023  sw           x4, 0(x5)  # 0xffb50020; write runtime value
    440: 0ff0000f  fence        0xf, 0xf
    444: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    448: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    44c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    450: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    454: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    458: 00520233  add          x4, x4, x5
    45c: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    460: 84030313  addi         x6, x6, -1984  # x6 = 0x00021840
    464: 00626863  bltu         x4, x6, 0x00000474  # target 0x00000474
    468: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    46c: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    470: 40720233  sub          x4, x4, x7
loc_474:
    474: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    478: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    47c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    480: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    484: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    488: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    48c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    490: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    494: 00520233  add          x4, x4, x5
    498: 00022337  lui          x6, 0x00022  # x6 = 0x00022000
    49c: 04030313  addi         x6, x6, 64  # x6 = 0x00022040
    4a0: 00626863  bltu         x4, x6, 0x000004b0  # target 0x000004b0
    4a4: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    4a8: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    4ac: 40720233  sub          x4, x4, x7
loc_4b0:
    4b0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4b4: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    4b8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    4bc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4c0: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4c4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    4c8: 00120213  addi         x4, x4, 1
    4cc: 01021213  slli         x4, x4, 16
    4d0: 01025213  srli         x4, x4, 16
    4d4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4d8: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4dc: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    4e0: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
    4e4: 02828293  addi         x5, x5, 40  # x5 = 0xffb51028
    4e8: 0042a023  sw           x4, 0(x5)  # 0xffb51028; write runtime value
    4ec: 0ff0000f  fence        0xf, 0xf
    4f0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4f4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    4f8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    4fc: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_500:
    500: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    504: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    508: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    50c: 40428333  sub          x6, x5, x4
    510: 01031313  slli         x6, x6, 16
    514: 01035313  srli         x6, x6, 16
    518: 00737663  bgeu         x6, x7, 0x00000524  # target 0x00000524
    51c: 0ff0000f  fence        0xf, 0xf
    520: fe1ff06f  jal          x0, 0x00000500  # target 0x00000500
loc_524:
    524: 0ff0000f  fence        0xf, 0xf
    528: 240000ef  jal          x1, 0x00000768  # target 0x00000768; x1 = 0x0000052c
    52c: 258000ef  jal          x1, 0x00000784  # target 0x00000784; x1 = 0x00000530
    530: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    534: 90028293  addi         x5, x5, -1792  # x5 = 0x0000e900
    538: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x0000e900
    53c: 00721213  slli         x4, x4, 7
    540: 00020293  addi         x5, x4, 0
    544: 00a2d313  srli         x6, x5, 10
    548: 00030f93  addi         x31, x6, 0
    54c: 3a4000ef  jal          x1, 0x000008f0  # target 0x000008f0; x1 = 0x00000550
    550: 000a8393  addi         x7, x21, 0
    554: 000b0413  addi         x8, x22, 0
    558: 3ff2f293  andi         x5, x5, 1023
    55c: 00129493  slli         x9, x5, 1
    560: 007484b3  add          x9, x9, x7
    564: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    568: 040f8f93  addi         x31, x31, 64  # x31 = 0x0001d040
    56c: 00048f13  addi         x30, x9, 0
    570: 00040e93  addi         x29, x8, 0
    574: 278000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000578
    578: 01028293  addi         x5, x5, 16
    57c: 00129493  slli         x9, x5, 1
    580: 007484b3  add          x9, x9, x7
    584: 0001dfb7  lui          x31, 0x0001d  # x31 = 0x0001d000
    588: 240f8f93  addi         x31, x31, 576  # x31 = 0x0001d240
    58c: 00048f13  addi         x30, x9, 0
    590: 00040e93  addi         x29, x8, 0
    594: 258000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000598
    598: 02020293  addi         x5, x4, 32
    59c: 00a2d313  srli         x6, x5, 10
    5a0: 00030f93  addi         x31, x6, 0
    5a4: 34c000ef  jal          x1, 0x000008f0  # target 0x000008f0; x1 = 0x000005a8
    5a8: 000a8393  addi         x7, x21, 0
    5ac: 000b0413  addi         x8, x22, 0
    5b0: 3ff2f293  andi         x5, x5, 1023
    5b4: 00129493  slli         x9, x5, 1
    5b8: 007484b3  add          x9, x9, x7
    5bc: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    5c0: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001d840
    5c4: 00048f13  addi         x30, x9, 0
    5c8: 00040e93  addi         x29, x8, 0
    5cc: 220000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000005d0
    5d0: 01028293  addi         x5, x5, 16
    5d4: 00129493  slli         x9, x5, 1
    5d8: 007484b3  add          x9, x9, x7
    5dc: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    5e0: a40f8f93  addi         x31, x31, -1472  # x31 = 0x0001da40
    5e4: 00048f13  addi         x30, x9, 0
    5e8: 00040e93  addi         x29, x8, 0
    5ec: 200000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000005f0
    5f0: 04020293  addi         x5, x4, 64
    5f4: 00a2d313  srli         x6, x5, 10
    5f8: 00030f93  addi         x31, x6, 0
    5fc: 2f4000ef  jal          x1, 0x000008f0  # target 0x000008f0; x1 = 0x00000600
    600: 000a8393  addi         x7, x21, 0
    604: 000b0413  addi         x8, x22, 0
    608: 3ff2f293  andi         x5, x5, 1023
    60c: 00129493  slli         x9, x5, 1
    610: 007484b3  add          x9, x9, x7
    614: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    618: 040f8f93  addi         x31, x31, 64  # x31 = 0x0001e040
    61c: 00048f13  addi         x30, x9, 0
    620: 00040e93  addi         x29, x8, 0
    624: 1c8000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000628
    628: 01028293  addi         x5, x5, 16
    62c: 00129493  slli         x9, x5, 1
    630: 007484b3  add          x9, x9, x7
    634: 0001efb7  lui          x31, 0x0001e  # x31 = 0x0001e000
    638: 240f8f93  addi         x31, x31, 576  # x31 = 0x0001e240
    63c: 00048f13  addi         x30, x9, 0
    640: 00040e93  addi         x29, x8, 0
    644: 1a8000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000648
    648: 06020293  addi         x5, x4, 96
    64c: 00a2d313  srli         x6, x5, 10
    650: 00030f93  addi         x31, x6, 0
    654: 29c000ef  jal          x1, 0x000008f0  # target 0x000008f0; x1 = 0x00000658
    658: 000a8393  addi         x7, x21, 0
    65c: 000b0413  addi         x8, x22, 0
    660: 3ff2f293  andi         x5, x5, 1023
    664: 00129493  slli         x9, x5, 1
    668: 007484b3  add          x9, x9, x7
    66c: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    670: 840f8f93  addi         x31, x31, -1984  # x31 = 0x0001e840
    674: 00048f13  addi         x30, x9, 0
    678: 00040e93  addi         x29, x8, 0
    67c: 170000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x00000680
    680: 01028293  addi         x5, x5, 16
    684: 00129493  slli         x9, x5, 1
    688: 007484b3  add          x9, x9, x7
    68c: 0001ffb7  lui          x31, 0x0001f  # x31 = 0x0001f000
    690: a40f8f93  addi         x31, x31, -1472  # x31 = 0x0001ea40
    694: 00048f13  addi         x30, x9, 0
    698: 00040e93  addi         x29, x8, 0
    69c: 150000ef  jal          x1, 0x000007ec  # target 0x000007ec; x1 = 0x000006a0
    6a0: 0c8000ef  jal          x1, 0x00000768  # target 0x00000768; x1 = 0x000006a4
    6a4: 0e0000ef  jal          x1, 0x00000784  # target 0x00000784; x1 = 0x000006a8
    6a8: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6ac: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    6b0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    6b4: 00420213  addi         x4, x4, 4
    6b8: 01021213  slli         x4, x4, 16
    6bc: 01025213  srli         x4, x4, 16
    6c0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    6c4: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    6c8: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    6cc: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    6d0: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    6d4: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    6d8: 0ff0000f  fence        0xf, 0xf
    6dc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6e0: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    6e4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    6e8: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    6ec: 00520233  add          x4, x4, x5
    6f0: 0001f337  lui          x6, 0x0001f  # x6 = 0x0001f000
    6f4: 04030313  addi         x6, x6, 64  # x6 = 0x0001f040
    6f8: 00626663  bltu         x4, x6, 0x00000704  # target 0x00000704
    6fc: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    700: 40720233  sub          x4, x4, x7
loc_704:
    704: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    708: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    70c: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    710: 22c0006f  jal          x0, 0x0000093c  # target 0x0000093c
loc_714:
    714: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    718: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    71c: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    720: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    724: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    728: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    72c: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    730: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    734: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    738: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    73c: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    740: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    744: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    748: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    74c: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    750: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    754: 020f8f93  addi         x31, x31, 32
    758: 020f0f13  addi         x30, x30, 32
    75c: ff8e8e93  addi         x29, x29, -8
    760: fa0e9ae3  bne          x29, x0, 0x00000714  # target 0x00000714
    764: 00008067  jalr         x0, 0(x1)
loc_768:
    768: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    76c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    770: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    774: 000a0463  beq          x20, x0, 0x0000077c  # target 0x0000077c
    778: ff1ff06f  jal          x0, 0x00000768  # target 0x00000768
loc_77c:
    77c: 0ff0000f  fence        0xf, 0xf
    780: 00008067  jalr         x0, 0(x1)
loc_784:
    784: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    788: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    78c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    790: 000a0463  beq          x20, x0, 0x00000798  # target 0x00000798
    794: ff1ff06f  jal          x0, 0x00000784  # target 0x00000784
loc_798:
    798: 0ff0000f  fence        0xf, 0xf
    79c: 00008067  jalr         x0, 0(x1)
loc_7a0:
    7a0: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    7a4: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    7a8: 007a7d13  andi         x26, x20, 7
    7ac: ff8a7a13  andi         x20, x20, -8
    7b0: 01af8ab3  add          x21, x31, x26
    7b4: 007afb93  andi         x23, x21, 7
    7b8: 003ada93  srli         x21, x21, 3
    7bc: 00ba9a93  slli         x21, x21, 11
    7c0: 014a8ab3  add          x21, x21, x20
    7c4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007c4
    7c8: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007dc
    7cc: 001b9b93  slli         x23, x23, 1
    7d0: 017b0b33  add          x22, x22, x23
    7d4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7d8: 00008067  jalr         x0, 0(x1)
    7dc: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e0: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7e4: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7e8: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_7ec:
    7ec: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    7f0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    7f4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    7f8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    7fc: 015a6463  bltu         x20, x21, 0x00000804  # target 0x00000804
    800: fedff06f  jal          x0, 0x000007ec  # target 0x000007ec
loc_804:
    804: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    808: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    80c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    810: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    814: 015a6463  bltu         x20, x21, 0x0000081c  # target 0x0000081c
    818: fedff06f  jal          x0, 0x00000804  # target 0x00000804
loc_81c:
    81c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    820: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    824: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    828: 014a1a13  slli         x20, x20, 20
    82c: 014a5a13  srli         x20, x20, 20
    830: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_834:
    834: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    838: 000b0463  beq          x22, x0, 0x00000840  # target 0x00000840
    83c: ff9ff06f  jal          x0, 0x00000834  # target 0x00000834
loc_840:
    840: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    844: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    848: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    84c: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    850: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    854: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    858: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    85c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    860: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    864: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    868: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    86c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    870: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    874: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    878: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    87c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    880: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    884: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    888: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    88c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    890: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_894:
    894: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    898: 000b0463  beq          x22, x0, 0x000008a0  # target 0x000008a0
    89c: ff9ff06f  jal          x0, 0x00000894  # target 0x00000894
loc_8a0:
    8a0: 00008067  jalr         x0, 0(x1)
loc_8a4:
    8a4: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    8a8: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    8ac: 007a7d13  andi         x26, x20, 7
    8b0: ff8a7a13  andi         x20, x20, -8
    8b4: 01af8ab3  add          x21, x31, x26
    8b8: 007afb93  andi         x23, x21, 7
    8bc: 003ada93  srli         x21, x21, 3
    8c0: 00ba9a93  slli         x21, x21, 11
    8c4: 014a8ab3  add          x21, x21, x20
    8c8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000008c8
    8cc: 018b0b13  addi         x22, x22, 24  # x22 = 0x000008e0
    8d0: 001b9b93  slli         x23, x23, 1
    8d4: 017b0b33  add          x22, x22, x23
    8d8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    8dc: 00008067  jalr         x0, 0(x1)
    8e0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8e4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8e8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    8ec: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_8f0:
    8f0: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    8f4: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x0000078c
    8f8: 007a7d13  andi         x26, x20, 7
    8fc: ff8a7a13  andi         x20, x20, -8
    900: 01af8ab3  add          x21, x31, x26
    904: 007afb93  andi         x23, x21, 7
    908: 003ada93  srli         x21, x21, 3
    90c: 00ba9a93  slli         x21, x21, 11
    910: 014a8ab3  add          x21, x21, x20
    914: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000914
    918: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000092c
    91c: 001b9b93  slli         x23, x23, 1
    920: 017b0b33  add          x22, x22, x23
    924: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    928: 00008067  jalr         x0, 0(x1)
    92c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    930: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    934: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    938: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    93c:           j FW_NCRISC+4   # return to firmware, linked at install
