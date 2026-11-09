# llama3 8b-fp8 decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama3.py.
# cores (32): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 2,10 2,11 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 3,10 3,11 4,2 4,3
# params: 0x7c0=e2e_q_heads, 0x7c4=e2e_l0_key_cache, 0x7c8=e2e_l0_value_cache, 0x7cc=e2e_context, 0x7d0=kv_blocks, 0x7d4=valid_columns, 0x7d8=attention_e2e_q_compact, 0x7dc=attention_e2e_k_compact, 0x7e0=attention_e2e_v_compact, 0x7e4=e2e_rope_cos, 0x7e8=e2e_rope_sin, 0x7ec=start_pos, 0x80c0=attention_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama3.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000a22b7  lui          x5, 0x000a2  # x5 = 0x000a2000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x000a2000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     24: 000a32b7  lui          x5, 0x000a3  # x5 = 0x000a3000
     28: 80028293  addi         x5, x5, -2048  # x5 = 0x000a2800
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x000a2800
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     3c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     40: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     44: 0009e2b7  lui          x5, 0x0009e  # x5 = 0x0009e000
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x0009e000
     4c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     50: 87820213  addi         x4, x4, -1928  # x4 = 0xffb00878 · riscv_local_mem + 0x878
     54: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x878 · 0xffb00878; write 0x00000000
     58: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
     5c: 86840413  addi         x8, x8, -1944  # x8 = 0xffb00868 · riscv_local_mem + 0x868
     60: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x868 · 0xffb00868
     64: 00100393  addi         x7, x0, 1  # x7 = 0x00000001
loc_68:
     68: ffb50437  lui          x8, 0xffb50  # x8 = 0xffb50000
     6c: 02840413  addi         x8, x8, 40  # x8 = 0xffb50028
     70: 00045283  lhu          x5, 0(x8)  # 0xffb50028
     74: 40428333  sub          x6, x5, x4
     78: 01031313  slli         x6, x6, 16
     7c: 01035313  srli         x6, x6, 16
     80: 00737663  bgeu         x6, x7, 0x0000008c  # target 0x0000008c
     84: 0ff0000f  fence        0xf, 0xf
     88: fe1ff06f  jal          x0, 0x00000068  # target 0x00000068
loc_8c:
     8c: 0ff0000f  fence        0xf, 0xf
     90: 00090237  lui          x4, 0x00090  # x4 = 0x00090000
     94: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
     98: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
loc_9c:
     9c: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     a0: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     a4: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     a8: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     ac: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     b0: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     b4: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     b8: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     bc: 02020213  addi         x4, x4, 32
     c0: ff828293  addi         x5, x5, -8
     c4: fc029ce3  bne          x5, x0, 0x0000009c  # target 0x0000009c
     c8: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
     cc: 00090f37  lui          x30, 0x00090  # x30 = 0x00090000
     d0: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     d4: 614000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000000d8
     d8: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
     dc: 020f8f93  addi         x31, x31, 32  # x31 = 0x000a2020
     e0: 00090f37  lui          x30, 0x00090  # x30 = 0x00090000
     e4: 200f0f13  addi         x30, x30, 512  # x30 = 0x00090200
     e8: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     ec: 5fc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x000000f0
     f0: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
     f4: 040f8f93  addi         x31, x31, 64  # x31 = 0x000a2040
     f8: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
     fc: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00090800
    100: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    104: 5e4000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000108
    108: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    10c: 060f8f93  addi         x31, x31, 96  # x31 = 0x000a2060
    110: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
    114: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00090a00
    118: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    11c: 5cc000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000120
    120: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    124: 080f8f93  addi         x31, x31, 128  # x31 = 0x000a2080
    128: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
    12c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    130: 5b8000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000134
    134: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    138: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x000a20a0
    13c: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
    140: 200f0f13  addi         x30, x30, 512  # x30 = 0x00091200
    144: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    148: 5a0000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x0000014c
    14c: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    150: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x000a20c0
    154: 00092f37  lui          x30, 0x00092  # x30 = 0x00092000
    158: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00091800
    15c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    160: 588000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x00000164
    164: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    168: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x000a20e0
    16c: 00092f37  lui          x30, 0x00092  # x30 = 0x00092000
    170: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00091a00
    174: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    178: 570000ef  jal          x1, 0x000006e8  # target 0x000006e8; x1 = 0x0000017c
    17c: 7ec00393  addi         x7, x0, 2028  # x7 = 0x000007ec
    180: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ec
    184: 00525293  srli         x5, x4, 5
    188: 00229293  slli         x5, x5, 2
    18c: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    190: 0c040413  addi         x8, x8, 192  # x8 = 0x000080c0
    194: 00042383  lw           x7, 0(x8)  # param attention_core; 0x000080c0
    198: 0023d393  srli         x7, x7, 2
    19c: 00a39393  slli         x7, x7, 10
    1a0: 007282b3  add          x5, x5, x7
    1a4: 00f27313  andi         x6, x4, 15
    1a8: 00531313  slli         x6, x6, 5
    1ac: 01027393  andi         x7, x4, 16
    1b0: 00639393  slli         x7, x7, 6
    1b4: 00730333  add          x6, x6, x7
    1b8: 584000ef  jal          x1, 0x0000073c  # target 0x0000073c; x1 = 0x000001bc
    1bc: 59c000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x000001c0
    1c0: 00028393  addi         x7, x5, 0
    1c4: 00038f93  addi         x31, x7, 0
    1c8: 5ac000ef  jal          x1, 0x00000774  # target 0x00000774; x1 = 0x000001cc
    1cc: 000a8413  addi         x8, x21, 0
    1d0: 000b0493  addi         x9, x22, 0
    1d4: 00640533  add          x10, x8, x6
    1d8: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    1dc: 100f8f93  addi         x31, x31, 256  # x31 = 0x000a2100
    1e0: 00050f13  addi         x30, x10, 0
    1e4: 00048e93  addi         x29, x9, 0
    1e8: 5d8000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000001ec
    1ec: 00640533  add          x10, x8, x6
    1f0: 20050513  addi         x10, x10, 512
    1f4: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    1f8: 120f8f93  addi         x31, x31, 288  # x31 = 0x000a2120
    1fc: 00050f13  addi         x30, x10, 0
    200: 00048e93  addi         x29, x9, 0
    204: 5bc000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000208
    208: 00038f93  addi         x31, x7, 0
    20c: 66c000ef  jal          x1, 0x00000878  # target 0x00000878; x1 = 0x00000210
    210: 000a8513  addi         x10, x21, 0
    214: 000b0593  addi         x11, x22, 0
    218: 00650633  add          x12, x10, x6
    21c: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    220: 00060f13  addi         x30, x12, 0
    224: 00058e93  addi         x29, x11, 0
    228: 598000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x0000022c
    22c: 00650633  add          x12, x10, x6
    230: 20060613  addi         x12, x12, 512
    234: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    238: 020f8f93  addi         x31, x31, 32  # x31 = 0x000b7020
    23c: 00060f13  addi         x30, x12, 0
    240: 00058e93  addi         x29, x11, 0
    244: 57c000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000248
    248: 00128393  addi         x7, x5, 1
    24c: 00038f93  addi         x31, x7, 0
    250: 524000ef  jal          x1, 0x00000774  # target 0x00000774; x1 = 0x00000254
    254: 000a8413  addi         x8, x21, 0
    258: 000b0493  addi         x9, x22, 0
    25c: 00640533  add          x10, x8, x6
    260: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    264: 140f8f93  addi         x31, x31, 320  # x31 = 0x000a2140
    268: 00050f13  addi         x30, x10, 0
    26c: 00048e93  addi         x29, x9, 0
    270: 550000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000274
    274: 00640533  add          x10, x8, x6
    278: 20050513  addi         x10, x10, 512
    27c: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    280: 160f8f93  addi         x31, x31, 352  # x31 = 0x000a2160
    284: 00050f13  addi         x30, x10, 0
    288: 00048e93  addi         x29, x9, 0
    28c: 534000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000290
    290: 00038f93  addi         x31, x7, 0
    294: 5e4000ef  jal          x1, 0x00000878  # target 0x00000878; x1 = 0x00000298
    298: 000a8513  addi         x10, x21, 0
    29c: 000b0593  addi         x11, x22, 0
    2a0: 00650633  add          x12, x10, x6
    2a4: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    2a8: 040f8f93  addi         x31, x31, 64  # x31 = 0x000b7040
    2ac: 00060f13  addi         x30, x12, 0
    2b0: 00058e93  addi         x29, x11, 0
    2b4: 50c000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000002b8
    2b8: 00650633  add          x12, x10, x6
    2bc: 20060613  addi         x12, x12, 512
    2c0: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    2c4: 060f8f93  addi         x31, x31, 96  # x31 = 0x000b7060
    2c8: 00060f13  addi         x30, x12, 0
    2cc: 00058e93  addi         x29, x11, 0
    2d0: 4f0000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000002d4
    2d4: 00228393  addi         x7, x5, 2
    2d8: 00038f93  addi         x31, x7, 0
    2dc: 498000ef  jal          x1, 0x00000774  # target 0x00000774; x1 = 0x000002e0
    2e0: 000a8413  addi         x8, x21, 0
    2e4: 000b0493  addi         x9, x22, 0
    2e8: 00640533  add          x10, x8, x6
    2ec: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    2f0: 180f8f93  addi         x31, x31, 384  # x31 = 0x000a2180
    2f4: 00050f13  addi         x30, x10, 0
    2f8: 00048e93  addi         x29, x9, 0
    2fc: 4c4000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000300
    300: 00640533  add          x10, x8, x6
    304: 20050513  addi         x10, x10, 512
    308: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    30c: 1a0f8f93  addi         x31, x31, 416  # x31 = 0x000a21a0
    310: 00050f13  addi         x30, x10, 0
    314: 00048e93  addi         x29, x9, 0
    318: 4a8000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x0000031c
    31c: 00038f93  addi         x31, x7, 0
    320: 558000ef  jal          x1, 0x00000878  # target 0x00000878; x1 = 0x00000324
    324: 000a8513  addi         x10, x21, 0
    328: 000b0593  addi         x11, x22, 0
    32c: 00650633  add          x12, x10, x6
    330: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    334: 080f8f93  addi         x31, x31, 128  # x31 = 0x000b7080
    338: 00060f13  addi         x30, x12, 0
    33c: 00058e93  addi         x29, x11, 0
    340: 480000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000344
    344: 00650633  add          x12, x10, x6
    348: 20060613  addi         x12, x12, 512
    34c: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    350: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x000b70a0
    354: 00060f13  addi         x30, x12, 0
    358: 00058e93  addi         x29, x11, 0
    35c: 464000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000360
    360: 00328393  addi         x7, x5, 3
    364: 00038f93  addi         x31, x7, 0
    368: 40c000ef  jal          x1, 0x00000774  # target 0x00000774; x1 = 0x0000036c
    36c: 000a8413  addi         x8, x21, 0
    370: 000b0493  addi         x9, x22, 0
    374: 00640533  add          x10, x8, x6
    378: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    37c: 1c0f8f93  addi         x31, x31, 448  # x31 = 0x000a21c0
    380: 00050f13  addi         x30, x10, 0
    384: 00048e93  addi         x29, x9, 0
    388: 438000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x0000038c
    38c: 00640533  add          x10, x8, x6
    390: 20050513  addi         x10, x10, 512
    394: 000a2fb7  lui          x31, 0x000a2  # x31 = 0x000a2000
    398: 1e0f8f93  addi         x31, x31, 480  # x31 = 0x000a21e0
    39c: 00050f13  addi         x30, x10, 0
    3a0: 00048e93  addi         x29, x9, 0
    3a4: 41c000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000003a8
    3a8: 00038f93  addi         x31, x7, 0
    3ac: 4cc000ef  jal          x1, 0x00000878  # target 0x00000878; x1 = 0x000003b0
    3b0: 000a8513  addi         x10, x21, 0
    3b4: 000b0593  addi         x11, x22, 0
    3b8: 00650633  add          x12, x10, x6
    3bc: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    3c0: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x000b70c0
    3c4: 00060f13  addi         x30, x12, 0
    3c8: 00058e93  addi         x29, x11, 0
    3cc: 3f4000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000003d0
    3d0: 00650633  add          x12, x10, x6
    3d4: 20060613  addi         x12, x12, 512
    3d8: 000b7fb7  lui          x31, 0x000b7  # x31 = 0x000b7000
    3dc: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x000b70e0
    3e0: 00060f13  addi         x30, x12, 0
    3e4: 00058e93  addi         x29, x11, 0
    3e8: 3d8000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000003ec
    3ec: 350000ef  jal          x1, 0x0000073c  # target 0x0000073c; x1 = 0x000003f0
    3f0: 368000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x000003f4
    3f4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3f8: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    3fc: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    400: 00120213  addi         x4, x4, 1
    404: 01021213  slli         x4, x4, 16
    408: 01025213  srli         x4, x4, 16
    40c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    410: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    414: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    418: ffb502b7  lui          x5, 0xffb50  # x5 = 0xffb50000
    41c: 02028293  addi         x5, x5, 32  # x5 = 0xffb50020
    420: 0042a023  sw           x4, 0(x5)  # 0xffb50020; write runtime value
    424: 0ff0000f  fence        0xf, 0xf
    428: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    42c: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    430: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    434: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    438: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    43c: 00520233  add          x4, x4, x5
    440: 000a3337  lui          x6, 0x000a3  # x6 = 0x000a3000
    444: 80030313  addi         x6, x6, -2048  # x6 = 0x000a2800
    448: 00626863  bltu         x4, x6, 0x00000458  # target 0x00000458
    44c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    450: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    454: 40720233  sub          x4, x4, x7
loc_458:
    458: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    45c: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    460: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    464: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    468: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    46c: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    470: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    474: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    478: 00520233  add          x4, x4, x5
    47c: 000a3337  lui          x6, 0x000a3  # x6 = 0x000a3000
    480: 00626863  bltu         x4, x6, 0x00000490  # target 0x00000490
    484: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    488: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    48c: 40720233  sub          x4, x4, x7
loc_490:
    490: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    494: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    498: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    49c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4a0: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4a4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    4a8: 00120213  addi         x4, x4, 1
    4ac: 01021213  slli         x4, x4, 16
    4b0: 01025213  srli         x4, x4, 16
    4b4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    4b8: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    4bc: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    4c0: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
    4c4: 02828293  addi         x5, x5, 40  # x5 = 0xffb51028
    4c8: 0042a023  sw           x4, 0(x5)  # 0xffb51028; write runtime value
    4cc: 0ff0000f  fence        0xf, 0xf
    4d0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    4d4: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    4d8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    4dc: 00400393  addi         x7, x0, 4  # x7 = 0x00000004
loc_4e0:
    4e0: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    4e4: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    4e8: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    4ec: 40428333  sub          x6, x5, x4
    4f0: 01031313  slli         x6, x6, 16
    4f4: 01035313  srli         x6, x6, 16
    4f8: 00737663  bgeu         x6, x7, 0x00000504  # target 0x00000504
    4fc: 0ff0000f  fence        0xf, 0xf
    500: fe1ff06f  jal          x0, 0x000004e0  # target 0x000004e0
loc_504:
    504: 0ff0000f  fence        0xf, 0xf
    508: 234000ef  jal          x1, 0x0000073c  # target 0x0000073c; x1 = 0x0000050c
    50c: 24c000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x00000510
    510: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    514: 0c028293  addi         x5, x5, 192  # x5 = 0x000080c0
    518: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x000080c0
    51c: 00721213  slli         x4, x4, 7
    520: 00020293  addi         x5, x4, 0
    524: 00a2d313  srli         x6, x5, 10
    528: 00030f93  addi         x31, x6, 0
    52c: 398000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x00000530
    530: 000a8393  addi         x7, x21, 0
    534: 000b0413  addi         x8, x22, 0
    538: 3ff2f293  andi         x5, x5, 1023
    53c: 00129493  slli         x9, x5, 1
    540: 007484b3  add          x9, x9, x7
    544: 0009efb7  lui          x31, 0x0009e  # x31 = 0x0009e000
    548: 00048f13  addi         x30, x9, 0
    54c: 00040e93  addi         x29, x8, 0
    550: 270000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000554
    554: 01028293  addi         x5, x5, 16
    558: 00129493  slli         x9, x5, 1
    55c: 007484b3  add          x9, x9, x7
    560: 0009efb7  lui          x31, 0x0009e  # x31 = 0x0009e000
    564: 200f8f93  addi         x31, x31, 512  # x31 = 0x0009e200
    568: 00048f13  addi         x30, x9, 0
    56c: 00040e93  addi         x29, x8, 0
    570: 250000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000574
    574: 02020293  addi         x5, x4, 32
    578: 00a2d313  srli         x6, x5, 10
    57c: 00030f93  addi         x31, x6, 0
    580: 344000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x00000584
    584: 000a8393  addi         x7, x21, 0
    588: 000b0413  addi         x8, x22, 0
    58c: 3ff2f293  andi         x5, x5, 1023
    590: 00129493  slli         x9, x5, 1
    594: 007484b3  add          x9, x9, x7
    598: 0009ffb7  lui          x31, 0x0009f  # x31 = 0x0009f000
    59c: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0009e800
    5a0: 00048f13  addi         x30, x9, 0
    5a4: 00040e93  addi         x29, x8, 0
    5a8: 218000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000005ac
    5ac: 01028293  addi         x5, x5, 16
    5b0: 00129493  slli         x9, x5, 1
    5b4: 007484b3  add          x9, x9, x7
    5b8: 0009ffb7  lui          x31, 0x0009f  # x31 = 0x0009f000
    5bc: a00f8f93  addi         x31, x31, -1536  # x31 = 0x0009ea00
    5c0: 00048f13  addi         x30, x9, 0
    5c4: 00040e93  addi         x29, x8, 0
    5c8: 1f8000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x000005cc
    5cc: 04020293  addi         x5, x4, 64
    5d0: 00a2d313  srli         x6, x5, 10
    5d4: 00030f93  addi         x31, x6, 0
    5d8: 2ec000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x000005dc
    5dc: 000a8393  addi         x7, x21, 0
    5e0: 000b0413  addi         x8, x22, 0
    5e4: 3ff2f293  andi         x5, x5, 1023
    5e8: 00129493  slli         x9, x5, 1
    5ec: 007484b3  add          x9, x9, x7
    5f0: 0009ffb7  lui          x31, 0x0009f  # x31 = 0x0009f000
    5f4: 00048f13  addi         x30, x9, 0
    5f8: 00040e93  addi         x29, x8, 0
    5fc: 1c4000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000600
    600: 01028293  addi         x5, x5, 16
    604: 00129493  slli         x9, x5, 1
    608: 007484b3  add          x9, x9, x7
    60c: 0009ffb7  lui          x31, 0x0009f  # x31 = 0x0009f000
    610: 200f8f93  addi         x31, x31, 512  # x31 = 0x0009f200
    614: 00048f13  addi         x30, x9, 0
    618: 00040e93  addi         x29, x8, 0
    61c: 1a4000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000620
    620: 06020293  addi         x5, x4, 96
    624: 00a2d313  srli         x6, x5, 10
    628: 00030f93  addi         x31, x6, 0
    62c: 298000ef  jal          x1, 0x000008c4  # target 0x000008c4; x1 = 0x00000630
    630: 000a8393  addi         x7, x21, 0
    634: 000b0413  addi         x8, x22, 0
    638: 3ff2f293  andi         x5, x5, 1023
    63c: 00129493  slli         x9, x5, 1
    640: 007484b3  add          x9, x9, x7
    644: 000a0fb7  lui          x31, 0x000a0  # x31 = 0x000a0000
    648: 800f8f93  addi         x31, x31, -2048  # x31 = 0x0009f800
    64c: 00048f13  addi         x30, x9, 0
    650: 00040e93  addi         x29, x8, 0
    654: 16c000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000658
    658: 01028293  addi         x5, x5, 16
    65c: 00129493  slli         x9, x5, 1
    660: 007484b3  add          x9, x9, x7
    664: 000a0fb7  lui          x31, 0x000a0  # x31 = 0x000a0000
    668: a00f8f93  addi         x31, x31, -1536  # x31 = 0x0009fa00
    66c: 00048f13  addi         x30, x9, 0
    670: 00040e93  addi         x29, x8, 0
    674: 14c000ef  jal          x1, 0x000007c0  # target 0x000007c0; x1 = 0x00000678
    678: 0c4000ef  jal          x1, 0x0000073c  # target 0x0000073c; x1 = 0x0000067c
    67c: 0dc000ef  jal          x1, 0x00000758  # target 0x00000758; x1 = 0x00000680
    680: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    684: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    688: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    68c: 00420213  addi         x4, x4, 4
    690: 01021213  slli         x4, x4, 16
    694: 01025213  srli         x4, x4, 16
    698: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    69c: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    6a0: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    6a4: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    6a8: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    6ac: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    6b0: 0ff0000f  fence        0xf, 0xf
    6b4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6b8: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    6bc: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    6c0: 000022b7  lui          x5, 0x00002  # x5 = 0x00002000
    6c4: 00520233  add          x4, x4, x5
    6c8: 000a0337  lui          x6, 0x000a0  # x6 = 0x000a0000
    6cc: 00626663  bltu         x4, x6, 0x000006d8  # target 0x000006d8
    6d0: 000023b7  lui          x7, 0x00002  # x7 = 0x00002000
    6d4: 40720233  sub          x4, x4, x7
loc_6d8:
    6d8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    6dc: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    6e0: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    6e4: 22c0006f  jal          x0, 0x00000910  # target 0x00000910
loc_6e8:
    6e8: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    6ec: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    6f0: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    6f4: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    6f8: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    6fc: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    700: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    704: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    708: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    70c: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    710: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    714: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    718: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    71c: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    720: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    724: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    728: 020f8f93  addi         x31, x31, 32
    72c: 020f0f13  addi         x30, x30, 32
    730: ff8e8e93  addi         x29, x29, -8
    734: fa0e9ae3  bne          x29, x0, 0x000006e8  # target 0x000006e8
    738: 00008067  jalr         x0, 0(x1)
loc_73c:
    73c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    740: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    744: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    748: 000a0463  beq          x20, x0, 0x00000750  # target 0x00000750
    74c: ff1ff06f  jal          x0, 0x0000073c  # target 0x0000073c
loc_750:
    750: 0ff0000f  fence        0xf, 0xf
    754: 00008067  jalr         x0, 0(x1)
loc_758:
    758: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    75c: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    760: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    764: 000a0463  beq          x20, x0, 0x0000076c  # target 0x0000076c
    768: ff1ff06f  jal          x0, 0x00000758  # target 0x00000758
loc_76c:
    76c: 0ff0000f  fence        0xf, 0xf
    770: 00008067  jalr         x0, 0(x1)
loc_774:
    774: 7c400a93  addi         x21, x0, 1988  # x21 = 0x000007c4
    778: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x000007c4
    77c: 007a7d13  andi         x26, x20, 7
    780: ff8a7a13  andi         x20, x20, -8
    784: 01af8ab3  add          x21, x31, x26
    788: 007afb93  andi         x23, x21, 7
    78c: 003ada93  srli         x21, x21, 3
    790: 00ba9a93  slli         x21, x21, 11
    794: 014a8ab3  add          x21, x21, x20
    798: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000798
    79c: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007b0
    7a0: 001b9b93  slli         x23, x23, 1
    7a4: 017b0b33  add          x22, x22, x23
    7a8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7ac: 00008067  jalr         x0, 0(x1)
    7b0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7b4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7b8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7bc: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_7c0:
    7c0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    7c4: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    7c8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    7cc: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    7d0: 015a6463  bltu         x20, x21, 0x000007d8  # target 0x000007d8
    7d4: fedff06f  jal          x0, 0x000007c0  # target 0x000007c0
loc_7d8:
    7d8: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    7dc: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    7e0: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    7e4: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    7e8: 015a6463  bltu         x20, x21, 0x000007f0  # target 0x000007f0
    7ec: fedff06f  jal          x0, 0x000007d8  # target 0x000007d8
loc_7f0:
    7f0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    7f4: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    7f8: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    7fc: 014a1a13  slli         x20, x20, 20
    800: 014a5a13  srli         x20, x20, 20
    804: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_808:
    808: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    80c: 000b0463  beq          x22, x0, 0x00000814  # target 0x00000814
    810: ff9ff06f  jal          x0, 0x00000808  # target 0x00000808
loc_814:
    814: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    818: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    81c: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    820: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    824: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    828: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    82c: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    830: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    834: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    838: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    83c: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    840: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    844: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    848: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    84c: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    850: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    854: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    858: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    85c: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    860: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    864: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_868:
    868: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    86c: 000b0463  beq          x22, x0, 0x00000874  # target 0x00000874
    870: ff9ff06f  jal          x0, 0x00000868  # target 0x00000868
loc_874:
    874: 00008067  jalr         x0, 0(x1)
loc_878:
    878: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    87c: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x000007c8
    880: 007a7d13  andi         x26, x20, 7
    884: ff8a7a13  andi         x20, x20, -8
    888: 01af8ab3  add          x21, x31, x26
    88c: 007afb93  andi         x23, x21, 7
    890: 003ada93  srli         x21, x21, 3
    894: 00ba9a93  slli         x21, x21, 11
    898: 014a8ab3  add          x21, x21, x20
    89c: 00000b17  auipc        x22, 0x00000  # x22 = 0x0000089c
    8a0: 018b0b13  addi         x22, x22, 24  # x22 = 0x000008b4
    8a4: 001b9b93  slli         x23, x23, 1
    8a8: 017b0b33  add          x22, x22, x23
    8ac: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    8b0: 00008067  jalr         x0, 0(x1)
    8b4: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8b8: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    8bc: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    8c0: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_8c4:
    8c4: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    8c8: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x000007cc
    8cc: 007a7d13  andi         x26, x20, 7
    8d0: ff8a7a13  andi         x20, x20, -8
    8d4: 01af8ab3  add          x21, x31, x26
    8d8: 007afb93  andi         x23, x21, 7
    8dc: 003ada93  srli         x21, x21, 3
    8e0: 00ba9a93  slli         x21, x21, 11
    8e4: 014a8ab3  add          x21, x21, x20
    8e8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000008e8
    8ec: 018b0b13  addi         x22, x22, 24  # x22 = 0x00000900
    8f0: 001b9b93  slli         x23, x23, 1
    8f4: 017b0b33  add          x22, x22, x23
    8f8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    8fc: 00008067  jalr         x0, 0(x1)
    900: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    904: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    908: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    90c: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    910:           j FW_NCRISC+4   # return to firmware, linked at install
