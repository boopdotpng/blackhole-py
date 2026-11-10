# llama3 1b decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (16): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7
# params: 0x780=e2e_q_heads, 0x784=e2e_l0_key_cache, 0x788=e2e_l0_value_cache, 0x78c=e2e_context, 0x790=kv_blocks, 0x794=valid_columns, 0x798=attention_e2e_q_compact, 0x79c=attention_e2e_k_compact, 0x7a0=attention_e2e_v_compact, 0x7a4=e2e_rope_cos, 0x7a8=e2e_rope_sin, 0x7ac=start_pos, 0xe900=attention_core
#   0x780.. uniform, sent with every EXEC; 0xe840.. this core's resident per-core table
# pcs are offsets from the image start; position-independent, llama3.py runs it from either code slot.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 0001a2b7  lui          x5, 0x0001a  # x5 = 0x0001a000
      c: fc028293  addi         x5, x5, -64  # x5 = 0x00019fc0
     10: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00019fc0
     14: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     18: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     1c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     20: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     24: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     28: 0001a2b7  lui          x5, 0x0001a  # x5 = 0x0001a000
     2c: 7c028293  addi         x5, x5, 1984  # x5 = 0x0001a7c0
     30: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x0001a7c0
     34: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     38: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     3c: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     40: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     44: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     48: 000172b7  lui          x5, 0x00017  # x5 = 0x00017000
     4c: fc028293  addi         x5, x5, -64  # x5 = 0x00016fc0
     50: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00016fc0
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
     a0: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
loc_a4:
     a4: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     a8: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     ac: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     b0: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     b4: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     b8: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     bc: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     c0: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     c4: 02020213  addi         x4, x4, 32
     c8: ff828293  addi         x5, x5, -8
     cc: fc029ce3  bne          x5, x0, 0x000000a4  # target 0x000000a4
     d0: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
     d4: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00019fc0
     d8: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
     dc: fc0f0f13  addi         x30, x30, -64  # x30 = 0x0000efc0
     e0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     e4: 50c000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x000000e8
     e8: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
     ec: fe0f8f93  addi         x31, x31, -32  # x31 = 0x00019fe0
     f0: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
     f4: 1c0f0f13  addi         x30, x30, 448  # x30 = 0x0000f1c0
     f8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     fc: 4f4000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x00000100
    100: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    104: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    108: 7c0f0f13  addi         x30, x30, 1984  # x30 = 0x0000f7c0
    10c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    110: 4e0000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x00000114
    114: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    118: 020f8f93  addi         x31, x31, 32  # x31 = 0x0001a020
    11c: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    120: 9c0f0f13  addi         x30, x30, -1600  # x30 = 0x0000f9c0
    124: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    128: 4c8000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x0000012c
    12c: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    130: 040f8f93  addi         x31, x31, 64  # x31 = 0x0001a040
    134: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    138: fe0f0f13  addi         x30, x30, -32  # x30 = 0x0000efe0
    13c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    140: 4b0000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x00000144
    144: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    148: 060f8f93  addi         x31, x31, 96  # x31 = 0x0001a060
    14c: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    150: 1e0f0f13  addi         x30, x30, 480  # x30 = 0x0000f1e0
    154: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    158: 498000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x0000015c
    15c: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    160: 080f8f93  addi         x31, x31, 128  # x31 = 0x0001a080
    164: 0000ff37  lui          x30, 0x0000f  # x30 = 0x0000f000
    168: 7e0f0f13  addi         x30, x30, 2016  # x30 = 0x0000f7e0
    16c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    170: 480000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x00000174
    174: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    178: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x0001a0a0
    17c: 00010f37  lui          x30, 0x00010  # x30 = 0x00010000
    180: 9e0f0f13  addi         x30, x30, -1568  # x30 = 0x0000f9e0
    184: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    188: 468000ef  jal          x1, 0x000005f0  # target 0x000005f0; x1 = 0x0000018c
    18c: 7ac00393  addi         x7, x0, 1964  # x7 = 0x000007ac
    190: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ac
    194: 00525293  srli         x5, x4, 5
    198: 00129293  slli         x5, x5, 1
    19c: 0000f437  lui          x8, 0x0000f  # x8 = 0x0000f000
    1a0: 90040413  addi         x8, x8, -1792  # x8 = 0x0000e900
    1a4: 00042383  lw           x7, 0(x8)  # param attention_core; 0x0000e900
    1a8: 0013d393  srli         x7, x7, 1
    1ac: 00939393  slli         x7, x7, 9
    1b0: 007282b3  add          x5, x5, x7
    1b4: 00f27313  andi         x6, x4, 15
    1b8: 00531313  slli         x6, x6, 5
    1bc: 01027393  andi         x7, x4, 16
    1c0: 00639393  slli         x7, x7, 6
    1c4: 00730333  add          x6, x6, x7
    1c8: 47c000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x000001cc
    1cc: 494000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x000001d0
    1d0: 00028393  addi         x7, x5, 0
    1d4: 00038f93  addi         x31, x7, 0
    1d8: 4a4000ef  jal          x1, 0x0000067c  # target 0x0000067c; x1 = 0x000001dc
    1dc: 000a8413  addi         x8, x21, 0
    1e0: 000b0493  addi         x9, x22, 0
    1e4: 00640533  add          x10, x8, x6
    1e8: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    1ec: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x0001a0c0
    1f0: 00050f13  addi         x30, x10, 0
    1f4: 00048e93  addi         x29, x9, 0
    1f8: 4d0000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000001fc
    1fc: 00640533  add          x10, x8, x6
    200: 20050513  addi         x10, x10, 512
    204: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    208: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x0001a0e0
    20c: 00050f13  addi         x30, x10, 0
    210: 00048e93  addi         x29, x9, 0
    214: 4b4000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000218
    218: 00038f93  addi         x31, x7, 0
    21c: 564000ef  jal          x1, 0x00000780  # target 0x00000780; x1 = 0x00000220
    220: 000a8513  addi         x10, x21, 0
    224: 000b0593  addi         x11, x22, 0
    228: 00650633  add          x12, x10, x6
    22c: 0002ffb7  lui          x31, 0x0002f  # x31 = 0x0002f000
    230: fc0f8f93  addi         x31, x31, -64  # x31 = 0x0002efc0
    234: 00060f13  addi         x30, x12, 0
    238: 00058e93  addi         x29, x11, 0
    23c: 48c000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000240
    240: 00650633  add          x12, x10, x6
    244: 20060613  addi         x12, x12, 512
    248: 0002ffb7  lui          x31, 0x0002f  # x31 = 0x0002f000
    24c: fe0f8f93  addi         x31, x31, -32  # x31 = 0x0002efe0
    250: 00060f13  addi         x30, x12, 0
    254: 00058e93  addi         x29, x11, 0
    258: 470000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x0000025c
    25c: 00128393  addi         x7, x5, 1
    260: 00038f93  addi         x31, x7, 0
    264: 418000ef  jal          x1, 0x0000067c  # target 0x0000067c; x1 = 0x00000268
    268: 000a8413  addi         x8, x21, 0
    26c: 000b0493  addi         x9, x22, 0
    270: 00640533  add          x10, x8, x6
    274: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    278: 100f8f93  addi         x31, x31, 256  # x31 = 0x0001a100
    27c: 00050f13  addi         x30, x10, 0
    280: 00048e93  addi         x29, x9, 0
    284: 444000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000288
    288: 00640533  add          x10, x8, x6
    28c: 20050513  addi         x10, x10, 512
    290: 0001afb7  lui          x31, 0x0001a  # x31 = 0x0001a000
    294: 120f8f93  addi         x31, x31, 288  # x31 = 0x0001a120
    298: 00050f13  addi         x30, x10, 0
    29c: 00048e93  addi         x29, x9, 0
    2a0: 428000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000002a4
    2a4: 00038f93  addi         x31, x7, 0
    2a8: 4d8000ef  jal          x1, 0x00000780  # target 0x00000780; x1 = 0x000002ac
    2ac: 000a8513  addi         x10, x21, 0
    2b0: 000b0593  addi         x11, x22, 0
    2b4: 00650633  add          x12, x10, x6
    2b8: 0002ffb7  lui          x31, 0x0002f  # x31 = 0x0002f000
    2bc: 00060f13  addi         x30, x12, 0
    2c0: 00058e93  addi         x29, x11, 0
    2c4: 404000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000002c8
    2c8: 00650633  add          x12, x10, x6
    2cc: 20060613  addi         x12, x12, 512
    2d0: 0002ffb7  lui          x31, 0x0002f  # x31 = 0x0002f000
    2d4: 020f8f93  addi         x31, x31, 32  # x31 = 0x0002f020
    2d8: 00060f13  addi         x30, x12, 0
    2dc: 00058e93  addi         x29, x11, 0
    2e0: 3e8000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000002e4
    2e4: 360000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x000002e8
    2e8: 378000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x000002ec
    2ec: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2f0: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    2f4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    2f8: 00120213  addi         x4, x4, 1
    2fc: 01021213  slli         x4, x4, 16
    300: 01025213  srli         x4, x4, 16
    304: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    308: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    30c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    310: ffb502b7  lui          x5, 0xffb50  # x5 = 0xffb50000
    314: 02028293  addi         x5, x5, 32  # x5 = 0xffb50020
    318: 0042a023  sw           x4, 0(x5)  # 0xffb50020; write runtime value
    31c: 0ff0000f  fence        0xf, 0xf
    320: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    324: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    328: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    32c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    330: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    334: 00520233  add          x4, x4, x5
    338: 0001a337  lui          x6, 0x0001a  # x6 = 0x0001a000
    33c: 7c030313  addi         x6, x6, 1984  # x6 = 0x0001a7c0
    340: 00626863  bltu         x4, x6, 0x00000350  # target 0x00000350
    344: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    348: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    34c: 40720233  sub          x4, x4, x7
loc_350:
    350: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    354: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    358: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    35c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    360: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    364: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    368: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    36c: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    370: 00520233  add          x4, x4, x5
    374: 0001b337  lui          x6, 0x0001b  # x6 = 0x0001b000
    378: fc030313  addi         x6, x6, -64  # x6 = 0x0001afc0
    37c: 00626863  bltu         x4, x6, 0x0000038c  # target 0x0000038c
    380: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    384: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    388: 40720233  sub          x4, x4, x7
loc_38c:
    38c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    390: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    394: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    398: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    39c: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    3a0: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    3a4: 00120213  addi         x4, x4, 1
    3a8: 01021213  slli         x4, x4, 16
    3ac: 01025213  srli         x4, x4, 16
    3b0: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3b4: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    3b8: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    3bc: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
    3c0: 02828293  addi         x5, x5, 40  # x5 = 0xffb51028
    3c4: 0042a023  sw           x4, 0(x5)  # 0xffb51028; write runtime value
    3c8: 0ff0000f  fence        0xf, 0xf
    3cc: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3d0: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    3d4: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    3d8: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
loc_3dc:
    3dc: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    3e0: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    3e4: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    3e8: 40428333  sub          x6, x5, x4
    3ec: 01031313  slli         x6, x6, 16
    3f0: 01035313  srli         x6, x6, 16
    3f4: 00737663  bgeu         x6, x7, 0x00000400  # target 0x00000400
    3f8: 0ff0000f  fence        0xf, 0xf
    3fc: fe1ff06f  jal          x0, 0x000003dc  # target 0x000003dc
loc_400:
    400: 0ff0000f  fence        0xf, 0xf
    404: 240000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x00000408
    408: 258000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x0000040c
    40c: 0000f2b7  lui          x5, 0x0000f  # x5 = 0x0000f000
    410: 90028293  addi         x5, x5, -1792  # x5 = 0x0000e900
    414: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x0000e900
    418: 00721213  slli         x4, x4, 7
    41c: 00020293  addi         x5, x4, 0
    420: 00a2d313  srli         x6, x5, 10
    424: 00030f93  addi         x31, x6, 0
    428: 3a4000ef  jal          x1, 0x000007cc  # target 0x000007cc; x1 = 0x0000042c
    42c: 000a8393  addi         x7, x21, 0
    430: 000b0413  addi         x8, x22, 0
    434: 3ff2f293  andi         x5, x5, 1023
    438: 00129493  slli         x9, x5, 1
    43c: 007484b3  add          x9, x9, x7
    440: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    444: fc0f8f93  addi         x31, x31, -64  # x31 = 0x00016fc0
    448: 00048f13  addi         x30, x9, 0
    44c: 00040e93  addi         x29, x8, 0
    450: 278000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000454
    454: 01028293  addi         x5, x5, 16
    458: 00129493  slli         x9, x5, 1
    45c: 007484b3  add          x9, x9, x7
    460: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    464: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x000171c0
    468: 00048f13  addi         x30, x9, 0
    46c: 00040e93  addi         x29, x8, 0
    470: 258000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000474
    474: 02020293  addi         x5, x4, 32
    478: 00a2d313  srli         x6, x5, 10
    47c: 00030f93  addi         x31, x6, 0
    480: 34c000ef  jal          x1, 0x000007cc  # target 0x000007cc; x1 = 0x00000484
    484: 000a8393  addi         x7, x21, 0
    488: 000b0413  addi         x8, x22, 0
    48c: 3ff2f293  andi         x5, x5, 1023
    490: 00129493  slli         x9, x5, 1
    494: 007484b3  add          x9, x9, x7
    498: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    49c: 7c0f8f93  addi         x31, x31, 1984  # x31 = 0x000177c0
    4a0: 00048f13  addi         x30, x9, 0
    4a4: 00040e93  addi         x29, x8, 0
    4a8: 220000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000004ac
    4ac: 01028293  addi         x5, x5, 16
    4b0: 00129493  slli         x9, x5, 1
    4b4: 007484b3  add          x9, x9, x7
    4b8: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    4bc: 9c0f8f93  addi         x31, x31, -1600  # x31 = 0x000179c0
    4c0: 00048f13  addi         x30, x9, 0
    4c4: 00040e93  addi         x29, x8, 0
    4c8: 200000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x000004cc
    4cc: 04020293  addi         x5, x4, 64
    4d0: 00a2d313  srli         x6, x5, 10
    4d4: 00030f93  addi         x31, x6, 0
    4d8: 2f4000ef  jal          x1, 0x000007cc  # target 0x000007cc; x1 = 0x000004dc
    4dc: 000a8393  addi         x7, x21, 0
    4e0: 000b0413  addi         x8, x22, 0
    4e4: 3ff2f293  andi         x5, x5, 1023
    4e8: 00129493  slli         x9, x5, 1
    4ec: 007484b3  add          x9, x9, x7
    4f0: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    4f4: fe0f8f93  addi         x31, x31, -32  # x31 = 0x00016fe0
    4f8: 00048f13  addi         x30, x9, 0
    4fc: 00040e93  addi         x29, x8, 0
    500: 1c8000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000504
    504: 01028293  addi         x5, x5, 16
    508: 00129493  slli         x9, x5, 1
    50c: 007484b3  add          x9, x9, x7
    510: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    514: 1e0f8f93  addi         x31, x31, 480  # x31 = 0x000171e0
    518: 00048f13  addi         x30, x9, 0
    51c: 00040e93  addi         x29, x8, 0
    520: 1a8000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x00000524
    524: 06020293  addi         x5, x4, 96
    528: 00a2d313  srli         x6, x5, 10
    52c: 00030f93  addi         x31, x6, 0
    530: 29c000ef  jal          x1, 0x000007cc  # target 0x000007cc; x1 = 0x00000534
    534: 000a8393  addi         x7, x21, 0
    538: 000b0413  addi         x8, x22, 0
    53c: 3ff2f293  andi         x5, x5, 1023
    540: 00129493  slli         x9, x5, 1
    544: 007484b3  add          x9, x9, x7
    548: 00017fb7  lui          x31, 0x00017  # x31 = 0x00017000
    54c: 7e0f8f93  addi         x31, x31, 2016  # x31 = 0x000177e0
    550: 00048f13  addi         x30, x9, 0
    554: 00040e93  addi         x29, x8, 0
    558: 170000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x0000055c
    55c: 01028293  addi         x5, x5, 16
    560: 00129493  slli         x9, x5, 1
    564: 007484b3  add          x9, x9, x7
    568: 00018fb7  lui          x31, 0x00018  # x31 = 0x00018000
    56c: 9e0f8f93  addi         x31, x31, -1568  # x31 = 0x000179e0
    570: 00048f13  addi         x30, x9, 0
    574: 00040e93  addi         x29, x8, 0
    578: 150000ef  jal          x1, 0x000006c8  # target 0x000006c8; x1 = 0x0000057c
    57c: 0c8000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x00000580
    580: 0e0000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x00000584
    584: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    588: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    58c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    590: 00220213  addi         x4, x4, 2
    594: 01021213  slli         x4, x4, 16
    598: 01025213  srli         x4, x4, 16
    59c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    5a0: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    5a4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    5a8: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    5ac: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    5b0: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    5b4: 0ff0000f  fence        0xf, 0xf
    5b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5bc: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    5c0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    5c4: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c8: 00520233  add          x4, x4, x5
    5cc: 00018337  lui          x6, 0x00018  # x6 = 0x00018000
    5d0: fc030313  addi         x6, x6, -64  # x6 = 0x00017fc0
    5d4: 00626663  bltu         x4, x6, 0x000005e0  # target 0x000005e0
    5d8: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5dc: 40720233  sub          x4, x4, x7
loc_5e0:
    5e0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5e4: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    5e8: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    5ec: 22c0006f  jal          x0, 0x00000818  # target 0x00000818
loc_5f0:
    5f0: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    5f4: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    5f8: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    5fc: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    600: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    604: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    608: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    60c: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    610: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    614: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    618: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    61c: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    620: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    624: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    628: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    62c: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    630: 020f8f93  addi         x31, x31, 32
    634: 020f0f13  addi         x30, x30, 32
    638: ff8e8e93  addi         x29, x29, -8
    63c: fa0e9ae3  bne          x29, x0, 0x000005f0  # target 0x000005f0
    640: 00008067  jalr         x0, 0(x1)
loc_644:
    644: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    648: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    64c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    650: 000a0463  beq          x20, x0, 0x00000658  # target 0x00000658
    654: ff1ff06f  jal          x0, 0x00000644  # target 0x00000644
loc_658:
    658: 0ff0000f  fence        0xf, 0xf
    65c: 00008067  jalr         x0, 0(x1)
loc_660:
    660: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    664: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    668: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    66c: 000a0463  beq          x20, x0, 0x00000674  # target 0x00000674
    670: ff1ff06f  jal          x0, 0x00000660  # target 0x00000660
loc_674:
    674: 0ff0000f  fence        0xf, 0xf
    678: 00008067  jalr         x0, 0(x1)
loc_67c:
    67c: 78400a93  addi         x21, x0, 1924  # x21 = 0x00000784
    680: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x00000784
    684: 007a7d13  andi         x26, x20, 7
    688: ff8a7a13  andi         x20, x20, -8
    68c: 01af8ab3  add          x21, x31, x26
    690: 007afb93  andi         x23, x21, 7
    694: 003ada93  srli         x21, x21, 3
    698: 00ba9a93  slli         x21, x21, 11
    69c: 014a8ab3  add          x21, x21, x20
    6a0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000006a0
    6a4: 018b0b13  addi         x22, x22, 24  # x22 = 0x000006b8
    6a8: 001b9b93  slli         x23, x23, 1
    6ac: 017b0b33  add          x22, x22, x23
    6b0: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    6b4: 00008067  jalr         x0, 0(x1)
    6b8: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6bc: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6c0: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6c4: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_6c8:
    6c8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6cc: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    6d0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    6d4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6d8: 015a6463  bltu         x20, x21, 0x000006e0  # target 0x000006e0
    6dc: fedff06f  jal          x0, 0x000006c8  # target 0x000006c8
loc_6e0:
    6e0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6e4: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    6e8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    6ec: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6f0: 015a6463  bltu         x20, x21, 0x000006f8  # target 0x000006f8
    6f4: fedff06f  jal          x0, 0x000006e0  # target 0x000006e0
loc_6f8:
    6f8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6fc: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    700: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    704: 014a1a13  slli         x20, x20, 20
    708: 014a5a13  srli         x20, x20, 20
    70c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_710:
    710: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    714: 000b0463  beq          x22, x0, 0x0000071c  # target 0x0000071c
    718: ff9ff06f  jal          x0, 0x00000710  # target 0x00000710
loc_71c:
    71c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    720: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    724: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    728: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    72c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    730: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    734: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    738: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    73c: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    740: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    744: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    748: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    74c: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    750: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    754: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    758: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    75c: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    760: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    764: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    768: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    76c: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_770:
    770: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    774: 000b0463  beq          x22, x0, 0x0000077c  # target 0x0000077c
    778: ff9ff06f  jal          x0, 0x00000770  # target 0x00000770
loc_77c:
    77c: 00008067  jalr         x0, 0(x1)
loc_780:
    780: 78800a93  addi         x21, x0, 1928  # x21 = 0x00000788
    784: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x00000788
    788: 007a7d13  andi         x26, x20, 7
    78c: ff8a7a13  andi         x20, x20, -8
    790: 01af8ab3  add          x21, x31, x26
    794: 007afb93  andi         x23, x21, 7
    798: 003ada93  srli         x21, x21, 3
    79c: 00ba9a93  slli         x21, x21, 11
    7a0: 014a8ab3  add          x21, x21, x20
    7a4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007a4
    7a8: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007bc
    7ac: 001b9b93  slli         x23, x23, 1
    7b0: 017b0b33  add          x22, x22, x23
    7b4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7b8: 00008067  jalr         x0, 0(x1)
    7bc: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7c0: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7c4: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7c8: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_7cc:
    7cc: 78c00a93  addi         x21, x0, 1932  # x21 = 0x0000078c
    7d0: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x0000078c
    7d4: 007a7d13  andi         x26, x20, 7
    7d8: ff8a7a13  andi         x20, x20, -8
    7dc: 01af8ab3  add          x21, x31, x26
    7e0: 007afb93  andi         x23, x21, 7
    7e4: 003ada93  srli         x21, x21, 3
    7e8: 00ba9a93  slli         x21, x21, 11
    7ec: 014a8ab3  add          x21, x21, x20
    7f0: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007f0
    7f4: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000808
    7f8: 001b9b93  slli         x23, x23, 1
    7fc: 017b0b33  add          x22, x22, x23
    800: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    804: 00008067  jalr         x0, 0(x1)
    808: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    80c: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    810: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    814: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    818:           j FW_NCRISC+4   # return to firmware, linked at install
