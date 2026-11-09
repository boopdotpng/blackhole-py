# llama3 1B decode: attention, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/rewrite_export/export_llama1b.py.
# cores (16): 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 1,10 1,11 2,2 2,3 2,4 2,5 2,6 2,7
# params: 0x7c0=e2e_q_heads, 0x7c4=e2e_l0_key_cache, 0x7c8=e2e_l0_value_cache, 0x7cc=e2e_context, 0x7d0=kv_blocks, 0x7d4=valid_columns, 0x7d8=attention_e2e_q_compact, 0x7dc=attention_e2e_k_compact, 0x7e0=attention_e2e_v_compact, 0x7e4=e2e_rope_cos, 0x7e8=e2e_rope_sin, 0x7ec=start_pos, 0x80c0=attention_core
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
      4: 86420213  addi         x4, x4, -1948  # x4 = 0xffb00864 · riscv_local_mem + 0x864
      8: 0009b2b7  lui          x5, 0x0009b  # x5 = 0x0009b000
      c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x0009b000
     10: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     14: 86820213  addi         x4, x4, -1944  # x4 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     20: 86c20213  addi         x4, x4, -1940  # x4 = 0xffb0086c · riscv_local_mem + 0x86c
     24: 0009c2b7  lui          x5, 0x0009c  # x5 = 0x0009c000
     28: 80028293  addi         x5, x5, -2048  # x5 = 0x0009b800
     2c: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x86c · 0xffb0086c; write 0x0009b800
     30: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     34: 87020213  addi         x4, x4, -1936  # x4 = 0xffb00870 · riscv_local_mem + 0x870
     38: 00022023  sw           x0, 0(x4)  # riscv_local_mem + 0x870 · 0xffb00870; write 0x00000000
     3c: ffb01237  lui          x4, 0xffb01  # x4 = 0xffb01000
     40: 87420213  addi         x4, x4, -1932  # x4 = 0xffb00874 · riscv_local_mem + 0x874
     44: 000982b7  lui          x5, 0x00098  # x5 = 0x00098000
     48: 00522023  sw           x5, 0(x4)  # riscv_local_mem + 0x874 · 0xffb00874; write 0x00098000
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
     94: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
loc_98:
     98: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     9c: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     a0: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     a4: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     a8: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     ac: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     b0: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     b4: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     b8: 02020213  addi         x4, x4, 32
     bc: ff828293  addi         x5, x5, -8
     c0: fc029ce3  bne          x5, x0, 0x00000098  # target 0x00000098
     c4: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
     c8: 00090f37  lui          x30, 0x00090  # x30 = 0x00090000
     cc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     d0: 504000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x000000d4
     d4: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
     d8: 020f8f93  addi         x31, x31, 32  # x31 = 0x0009b020
     dc: 00090f37  lui          x30, 0x00090  # x30 = 0x00090000
     e0: 200f0f13  addi         x30, x30, 512  # x30 = 0x00090200
     e4: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
     e8: 4ec000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x000000ec
     ec: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
     f0: 040f8f93  addi         x31, x31, 64  # x31 = 0x0009b040
     f4: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
     f8: 800f0f13  addi         x30, x30, -2048  # x30 = 0x00090800
     fc: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    100: 4d4000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x00000104
    104: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    108: 060f8f93  addi         x31, x31, 96  # x31 = 0x0009b060
    10c: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
    110: a00f0f13  addi         x30, x30, -1536  # x30 = 0x00090a00
    114: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    118: 4bc000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x0000011c
    11c: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    120: 080f8f93  addi         x31, x31, 128  # x31 = 0x0009b080
    124: 00090f37  lui          x30, 0x00090  # x30 = 0x00090000
    128: 020f0f13  addi         x30, x30, 32  # x30 = 0x00090020
    12c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    130: 4a4000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x00000134
    134: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    138: 0a0f8f93  addi         x31, x31, 160  # x31 = 0x0009b0a0
    13c: 00090f37  lui          x30, 0x00090  # x30 = 0x00090000
    140: 220f0f13  addi         x30, x30, 544  # x30 = 0x00090220
    144: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    148: 48c000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x0000014c
    14c: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    150: 0c0f8f93  addi         x31, x31, 192  # x31 = 0x0009b0c0
    154: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
    158: 820f0f13  addi         x30, x30, -2016  # x30 = 0x00090820
    15c: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    160: 474000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x00000164
    164: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    168: 0e0f8f93  addi         x31, x31, 224  # x31 = 0x0009b0e0
    16c: 00091f37  lui          x30, 0x00091  # x30 = 0x00091000
    170: a20f0f13  addi         x30, x30, -1504  # x30 = 0x00090a20
    174: 00800e93  addi         x29, x0, 8  # x29 = 0x00000008
    178: 45c000ef  jal          x1, 0x000005d4  # target 0x000005d4; x1 = 0x0000017c
    17c: 7ec00393  addi         x7, x0, 2028  # x7 = 0x000007ec
    180: 0003a203  lw           x4, 0(x7)  # param start_pos; 0x000007ec
    184: 00525293  srli         x5, x4, 5
    188: 00129293  slli         x5, x5, 1
    18c: 00008437  lui          x8, 0x00008  # x8 = 0x00008000
    190: 0c040413  addi         x8, x8, 192  # x8 = 0x000080c0
    194: 00042383  lw           x7, 0(x8)  # param attention_core; 0x000080c0
    198: 0013d393  srli         x7, x7, 1
    19c: 00939393  slli         x7, x7, 9
    1a0: 007282b3  add          x5, x5, x7
    1a4: 00f27313  andi         x6, x4, 15
    1a8: 00531313  slli         x6, x6, 5
    1ac: 01027393  andi         x7, x4, 16
    1b0: 00639393  slli         x7, x7, 6
    1b4: 00730333  add          x6, x6, x7
    1b8: 470000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000001bc
    1bc: 488000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x000001c0
    1c0: 00028393  addi         x7, x5, 0
    1c4: 00038f93  addi         x31, x7, 0
    1c8: 498000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x000001cc
    1cc: 000a8413  addi         x8, x21, 0
    1d0: 000b0493  addi         x9, x22, 0
    1d4: 00640533  add          x10, x8, x6
    1d8: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    1dc: 100f8f93  addi         x31, x31, 256  # x31 = 0x0009b100
    1e0: 00050f13  addi         x30, x10, 0
    1e4: 00048e93  addi         x29, x9, 0
    1e8: 4c4000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000001ec
    1ec: 00640533  add          x10, x8, x6
    1f0: 20050513  addi         x10, x10, 512
    1f4: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    1f8: 120f8f93  addi         x31, x31, 288  # x31 = 0x0009b120
    1fc: 00050f13  addi         x30, x10, 0
    200: 00048e93  addi         x29, x9, 0
    204: 4a8000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000208
    208: 00038f93  addi         x31, x7, 0
    20c: 558000ef  jal          x1, 0x00000764  # target 0x00000764; x1 = 0x00000210
    210: 000a8513  addi         x10, x21, 0
    214: 000b0593  addi         x11, x22, 0
    218: 00650633  add          x12, x10, x6
    21c: 000b0fb7  lui          x31, 0x000b0  # x31 = 0x000b0000 · arc_apb_msi_fifo + 0x0
    220: 00060f13  addi         x30, x12, 0
    224: 00058e93  addi         x29, x11, 0
    228: 484000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x0000022c
    22c: 00650633  add          x12, x10, x6
    230: 20060613  addi         x12, x12, 512
    234: 000b0fb7  lui          x31, 0x000b0  # x31 = 0x000b0000 · arc_apb_msi_fifo + 0x0
    238: 020f8f93  addi         x31, x31, 32  # x31 = 0x000b0020 · arc_apb_msi_fifo + 0x20
    23c: 00060f13  addi         x30, x12, 0
    240: 00058e93  addi         x29, x11, 0
    244: 468000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000248
    248: 00128393  addi         x7, x5, 1
    24c: 00038f93  addi         x31, x7, 0
    250: 410000ef  jal          x1, 0x00000660  # target 0x00000660; x1 = 0x00000254
    254: 000a8413  addi         x8, x21, 0
    258: 000b0493  addi         x9, x22, 0
    25c: 00640533  add          x10, x8, x6
    260: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    264: 140f8f93  addi         x31, x31, 320  # x31 = 0x0009b140
    268: 00050f13  addi         x30, x10, 0
    26c: 00048e93  addi         x29, x9, 0
    270: 43c000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000274
    274: 00640533  add          x10, x8, x6
    278: 20050513  addi         x10, x10, 512
    27c: 0009bfb7  lui          x31, 0x0009b  # x31 = 0x0009b000
    280: 160f8f93  addi         x31, x31, 352  # x31 = 0x0009b160
    284: 00050f13  addi         x30, x10, 0
    288: 00048e93  addi         x29, x9, 0
    28c: 420000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000290
    290: 00038f93  addi         x31, x7, 0
    294: 4d0000ef  jal          x1, 0x00000764  # target 0x00000764; x1 = 0x00000298
    298: 000a8513  addi         x10, x21, 0
    29c: 000b0593  addi         x11, x22, 0
    2a0: 00650633  add          x12, x10, x6
    2a4: 000b0fb7  lui          x31, 0x000b0  # x31 = 0x000b0000 · arc_apb_msi_fifo + 0x0
    2a8: 040f8f93  addi         x31, x31, 64  # x31 = 0x000b0040 · arc_apb_msi_fifo + 0x40
    2ac: 00060f13  addi         x30, x12, 0
    2b0: 00058e93  addi         x29, x11, 0
    2b4: 3f8000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000002b8
    2b8: 00650633  add          x12, x10, x6
    2bc: 20060613  addi         x12, x12, 512
    2c0: 000b0fb7  lui          x31, 0x000b0  # x31 = 0x000b0000 · arc_apb_msi_fifo + 0x0
    2c4: 060f8f93  addi         x31, x31, 96  # x31 = 0x000b0060 · arc_apb_msi_fifo + 0x60
    2c8: 00060f13  addi         x30, x12, 0
    2cc: 00058e93  addi         x29, x11, 0
    2d0: 3dc000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000002d4
    2d4: 354000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000002d8
    2d8: 36c000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x000002dc
    2dc: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2e0: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    2e4: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868
    2e8: 00120213  addi         x4, x4, 1
    2ec: 01021213  slli         x4, x4, 16
    2f0: 01025213  srli         x4, x4, 16
    2f4: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    2f8: 86828293  addi         x5, x5, -1944  # x5 = 0xffb00868 · riscv_local_mem + 0x868
    2fc: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
    300: ffb502b7  lui          x5, 0xffb50  # x5 = 0xffb50000
    304: 02028293  addi         x5, x5, 32  # x5 = 0xffb50020
    308: 0042a023  sw           x4, 0(x5)  # 0xffb50020; write runtime value
    30c: 0ff0000f  fence        0xf, 0xf
    310: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    314: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    318: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864
    31c: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    320: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    324: 00520233  add          x4, x4, x5
    328: 0009c337  lui          x6, 0x0009c  # x6 = 0x0009c000
    32c: 80030313  addi         x6, x6, -2048  # x6 = 0x0009b800
    330: 00626863  bltu         x4, x6, 0x00000340  # target 0x00000340
    334: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    338: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    33c: 40720233  sub          x4, x4, x7
loc_340:
    340: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    344: 86440413  addi         x8, x8, -1948  # x8 = 0xffb00864 · riscv_local_mem + 0x864
    348: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    34c: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    350: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    354: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c
    358: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    35c: 80028293  addi         x5, x5, -2048  # x5 = 0x00000800
    360: 00520233  add          x4, x4, x5
    364: 0009c337  lui          x6, 0x0009c  # x6 = 0x0009c000
    368: 00626863  bltu         x4, x6, 0x00000378  # target 0x00000378
    36c: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    370: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    374: 40720233  sub          x4, x4, x7
loc_378:
    378: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    37c: 86c40413  addi         x8, x8, -1940  # x8 = 0xffb0086c · riscv_local_mem + 0x86c
    380: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x86c · 0xffb0086c; write runtime value
    384: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    388: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    38c: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870
    390: 00120213  addi         x4, x4, 1
    394: 01021213  slli         x4, x4, 16
    398: 01025213  srli         x4, x4, 16
    39c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    3a0: 87028293  addi         x5, x5, -1936  # x5 = 0xffb00870 · riscv_local_mem + 0x870
    3a4: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x870 · 0xffb00870; write runtime value
    3a8: ffb512b7  lui          x5, 0xffb51  # x5 = 0xffb51000
    3ac: 02828293  addi         x5, x5, 40  # x5 = 0xffb51028
    3b0: 0042a023  sw           x4, 0(x5)  # 0xffb51028; write runtime value
    3b4: 0ff0000f  fence        0xf, 0xf
    3b8: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    3bc: 87840413  addi         x8, x8, -1928  # x8 = 0xffb00878 · riscv_local_mem + 0x878
    3c0: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x878 · 0xffb00878
    3c4: 00200393  addi         x7, x0, 2  # x7 = 0x00000002
loc_3c8:
    3c8: ffb4e437  lui          x8, 0xffb4e  # x8 = 0xffb4e000
    3cc: 02840413  addi         x8, x8, 40  # x8 = 0xffb4e028
    3d0: 00045283  lhu          x5, 0(x8)  # 0xffb4e028
    3d4: 40428333  sub          x6, x5, x4
    3d8: 01031313  slli         x6, x6, 16
    3dc: 01035313  srli         x6, x6, 16
    3e0: 00737663  bgeu         x6, x7, 0x000003ec  # target 0x000003ec
    3e4: 0ff0000f  fence        0xf, 0xf
    3e8: fe1ff06f  jal          x0, 0x000003c8  # target 0x000003c8
loc_3ec:
    3ec: 0ff0000f  fence        0xf, 0xf
    3f0: 238000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x000003f4
    3f4: 250000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x000003f8
    3f8: 000082b7  lui          x5, 0x00008  # x5 = 0x00008000
    3fc: 0c028293  addi         x5, x5, 192  # x5 = 0x000080c0
    400: 0002a203  lw           x4, 0(x5)  # param attention_core; 0x000080c0
    404: 00721213  slli         x4, x4, 7
    408: 00020293  addi         x5, x4, 0
    40c: 00a2d313  srli         x6, x5, 10
    410: 00030f93  addi         x31, x6, 0
    414: 39c000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x00000418
    418: 000a8393  addi         x7, x21, 0
    41c: 000b0413  addi         x8, x22, 0
    420: 3ff2f293  andi         x5, x5, 1023
    424: 00129493  slli         x9, x5, 1
    428: 007484b3  add          x9, x9, x7
    42c: 00098fb7  lui          x31, 0x00098  # x31 = 0x00098000
    430: 00048f13  addi         x30, x9, 0
    434: 00040e93  addi         x29, x8, 0
    438: 274000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x0000043c
    43c: 01028293  addi         x5, x5, 16
    440: 00129493  slli         x9, x5, 1
    444: 007484b3  add          x9, x9, x7
    448: 00098fb7  lui          x31, 0x00098  # x31 = 0x00098000
    44c: 200f8f93  addi         x31, x31, 512  # x31 = 0x00098200
    450: 00048f13  addi         x30, x9, 0
    454: 00040e93  addi         x29, x8, 0
    458: 254000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x0000045c
    45c: 02020293  addi         x5, x4, 32
    460: 00a2d313  srli         x6, x5, 10
    464: 00030f93  addi         x31, x6, 0
    468: 348000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x0000046c
    46c: 000a8393  addi         x7, x21, 0
    470: 000b0413  addi         x8, x22, 0
    474: 3ff2f293  andi         x5, x5, 1023
    478: 00129493  slli         x9, x5, 1
    47c: 007484b3  add          x9, x9, x7
    480: 00099fb7  lui          x31, 0x00099  # x31 = 0x00099000
    484: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00098800
    488: 00048f13  addi         x30, x9, 0
    48c: 00040e93  addi         x29, x8, 0
    490: 21c000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000494
    494: 01028293  addi         x5, x5, 16
    498: 00129493  slli         x9, x5, 1
    49c: 007484b3  add          x9, x9, x7
    4a0: 00099fb7  lui          x31, 0x00099  # x31 = 0x00099000
    4a4: a00f8f93  addi         x31, x31, -1536  # x31 = 0x00098a00
    4a8: 00048f13  addi         x30, x9, 0
    4ac: 00040e93  addi         x29, x8, 0
    4b0: 1fc000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000004b4
    4b4: 04020293  addi         x5, x4, 64
    4b8: 00a2d313  srli         x6, x5, 10
    4bc: 00030f93  addi         x31, x6, 0
    4c0: 2f0000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x000004c4
    4c4: 000a8393  addi         x7, x21, 0
    4c8: 000b0413  addi         x8, x22, 0
    4cc: 3ff2f293  andi         x5, x5, 1023
    4d0: 00129493  slli         x9, x5, 1
    4d4: 007484b3  add          x9, x9, x7
    4d8: 00098fb7  lui          x31, 0x00098  # x31 = 0x00098000
    4dc: 020f8f93  addi         x31, x31, 32  # x31 = 0x00098020
    4e0: 00048f13  addi         x30, x9, 0
    4e4: 00040e93  addi         x29, x8, 0
    4e8: 1c4000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x000004ec
    4ec: 01028293  addi         x5, x5, 16
    4f0: 00129493  slli         x9, x5, 1
    4f4: 007484b3  add          x9, x9, x7
    4f8: 00098fb7  lui          x31, 0x00098  # x31 = 0x00098000
    4fc: 220f8f93  addi         x31, x31, 544  # x31 = 0x00098220
    500: 00048f13  addi         x30, x9, 0
    504: 00040e93  addi         x29, x8, 0
    508: 1a4000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x0000050c
    50c: 06020293  addi         x5, x4, 96
    510: 00a2d313  srli         x6, x5, 10
    514: 00030f93  addi         x31, x6, 0
    518: 298000ef  jal          x1, 0x000007b0  # target 0x000007b0; x1 = 0x0000051c
    51c: 000a8393  addi         x7, x21, 0
    520: 000b0413  addi         x8, x22, 0
    524: 3ff2f293  andi         x5, x5, 1023
    528: 00129493  slli         x9, x5, 1
    52c: 007484b3  add          x9, x9, x7
    530: 00099fb7  lui          x31, 0x00099  # x31 = 0x00099000
    534: 820f8f93  addi         x31, x31, -2016  # x31 = 0x00098820
    538: 00048f13  addi         x30, x9, 0
    53c: 00040e93  addi         x29, x8, 0
    540: 16c000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000544
    544: 01028293  addi         x5, x5, 16
    548: 00129493  slli         x9, x5, 1
    54c: 007484b3  add          x9, x9, x7
    550: 00099fb7  lui          x31, 0x00099  # x31 = 0x00099000
    554: a20f8f93  addi         x31, x31, -1504  # x31 = 0x00098a20
    558: 00048f13  addi         x30, x9, 0
    55c: 00040e93  addi         x29, x8, 0
    560: 14c000ef  jal          x1, 0x000006ac  # target 0x000006ac; x1 = 0x00000564
    564: 0c4000ef  jal          x1, 0x00000628  # target 0x00000628; x1 = 0x00000568
    568: 0dc000ef  jal          x1, 0x00000644  # target 0x00000644; x1 = 0x0000056c
    56c: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    570: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    574: 0002a203  lw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878
    578: 00220213  addi         x4, x4, 2
    57c: 01021213  slli         x4, x4, 16
    580: 01025213  srli         x4, x4, 16
    584: ffb012b7  lui          x5, 0xffb01  # x5 = 0xffb01000
    588: 87828293  addi         x5, x5, -1928  # x5 = 0xffb00878 · riscv_local_mem + 0x878
    58c: 0042a023  sw           x4, 0(x5)  # riscv_local_mem + 0x878 · 0xffb00878; write runtime value
    590: ffb4e2b7  lui          x5, 0xffb4e  # x5 = 0xffb4e000
    594: 02028293  addi         x5, x5, 32  # x5 = 0xffb4e020
    598: 0042a023  sw           x4, 0(x5)  # 0xffb4e020; write runtime value
    59c: 0ff0000f  fence        0xf, 0xf
    5a0: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5a4: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    5a8: 00042203  lw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874
    5ac: 000012b7  lui          x5, 0x00001  # x5 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5b0: 00520233  add          x4, x4, x5
    5b4: 00099337  lui          x6, 0x00099  # x6 = 0x00099000
    5b8: 00626663  bltu         x4, x6, 0x000005c4  # target 0x000005c4
    5bc: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    5c0: 40720233  sub          x4, x4, x7
loc_5c4:
    5c4: ffb01437  lui          x8, 0xffb01  # x8 = 0xffb01000
    5c8: 87440413  addi         x8, x8, -1932  # x8 = 0xffb00874 · riscv_local_mem + 0x874
    5cc: 00442023  sw           x4, 0(x8)  # riscv_local_mem + 0x874 · 0xffb00874; write runtime value
    5d0: 22c0006f  jal          x0, 0x000007fc  # target 0x000007fc
loc_5d4:
    5d4: 000faa03  lw           x20, 0(x31)  # Address depends on runtime register values
    5d8: 014f2023  sw           x20, 0(x30)  # Address depends on runtime register values
    5dc: 004faa03  lw           x20, 4(x31)  # Address depends on runtime register values
    5e0: 014f2223  sw           x20, 4(x30)  # Address depends on runtime register values
    5e4: 008faa03  lw           x20, 8(x31)  # Address depends on runtime register values
    5e8: 014f2423  sw           x20, 8(x30)  # Address depends on runtime register values
    5ec: 00cfaa03  lw           x20, 12(x31)  # Address depends on runtime register values
    5f0: 014f2623  sw           x20, 12(x30)  # Address depends on runtime register values
    5f4: 010faa03  lw           x20, 16(x31)  # Address depends on runtime register values
    5f8: 014f2823  sw           x20, 16(x30)  # Address depends on runtime register values
    5fc: 014faa03  lw           x20, 20(x31)  # Address depends on runtime register values
    600: 014f2a23  sw           x20, 20(x30)  # Address depends on runtime register values
    604: 018faa03  lw           x20, 24(x31)  # Address depends on runtime register values
    608: 014f2c23  sw           x20, 24(x30)  # Address depends on runtime register values
    60c: 01cfaa03  lw           x20, 28(x31)  # Address depends on runtime register values
    610: 014f2e23  sw           x20, 28(x30)  # Address depends on runtime register values
    614: 020f8f93  addi         x31, x31, 32
    618: 020f0f13  addi         x30, x30, 32
    61c: ff8e8e93  addi         x29, x29, -8
    620: fa0e9ae3  bne          x29, x0, 0x000005d4  # target 0x000005d4
    624: 00008067  jalr         x0, 0(x1)
loc_628:
    628: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    62c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    630: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    634: 000a0463  beq          x20, x0, 0x0000063c  # target 0x0000063c
    638: ff1ff06f  jal          x0, 0x00000628  # target 0x00000628
loc_63c:
    63c: 0ff0000f  fence        0xf, 0xf
    640: 00008067  jalr         x0, 0(x1)
loc_644:
    644: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    648: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    64c: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    650: 000a0463  beq          x20, x0, 0x00000658  # target 0x00000658
    654: ff1ff06f  jal          x0, 0x00000644  # target 0x00000644
loc_658:
    658: 0ff0000f  fence        0xf, 0xf
    65c: 00008067  jalr         x0, 0(x1)
loc_660:
    660: 7c400a93  addi         x21, x0, 1988  # x21 = 0x000007c4
    664: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_key_cache; 0x000007c4
    668: 007a7d13  andi         x26, x20, 7
    66c: ff8a7a13  andi         x20, x20, -8
    670: 01af8ab3  add          x21, x31, x26
    674: 007afb93  andi         x23, x21, 7
    678: 003ada93  srli         x21, x21, 3
    67c: 00ba9a93  slli         x21, x21, 11
    680: 014a8ab3  add          x21, x21, x20
    684: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000684
    688: 018b0b13  addi         x22, x22, 24  # x22 = 0x0000069c
    68c: 001b9b93  slli         x23, x23, 1
    690: 017b0b33  add          x22, x22, x23
    694: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    698: 00008067  jalr         x0, 0(x1)
    69c: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6a0: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    6a4: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    6a8: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_6ac:
    6ac: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6b0: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    6b4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    6b8: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6bc: 015a6463  bltu         x20, x21, 0x000006c4  # target 0x000006c4
    6c0: fedff06f  jal          x0, 0x000006ac  # target 0x000006ac
loc_6c4:
    6c4: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6c8: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    6cc: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    6d0: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    6d4: 015a6463  bltu         x20, x21, 0x000006dc  # target 0x000006dc
    6d8: fedff06f  jal          x0, 0x000006c4  # target 0x000006c4
loc_6dc:
    6dc: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    6e0: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    6e4: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    6e8: 014a1a13  slli         x20, x20, 20
    6ec: 014a5a13  srli         x20, x20, 20
    6f0: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_6f4:
    6f4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    6f8: 000b0463  beq          x22, x0, 0x00000700  # target 0x00000700
    6fc: ff9ff06f  jal          x0, 0x000006f4  # target 0x000006f4
loc_700:
    700: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    704: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    708: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    70c: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    710: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    714: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    718: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    71c: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    720: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    724: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    728: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    72c: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    730: 02000c13  addi         x24, x0, 32  # x24 = 0x00000020
    734: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000020
    738: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    73c: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    740: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    744: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    748: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    74c: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    750: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_754:
    754: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    758: 000b0463  beq          x22, x0, 0x00000760  # target 0x00000760
    75c: ff9ff06f  jal          x0, 0x00000754  # target 0x00000754
loc_760:
    760: 00008067  jalr         x0, 0(x1)
loc_764:
    764: 7c800a93  addi         x21, x0, 1992  # x21 = 0x000007c8
    768: 000aaa03  lw           x20, 0(x21)  # param e2e_l0_value_cache; 0x000007c8
    76c: 007a7d13  andi         x26, x20, 7
    770: ff8a7a13  andi         x20, x20, -8
    774: 01af8ab3  add          x21, x31, x26
    778: 007afb93  andi         x23, x21, 7
    77c: 003ada93  srli         x21, x21, 3
    780: 00ba9a93  slli         x21, x21, 11
    784: 014a8ab3  add          x21, x21, x20
    788: 00000b17  auipc        x22, 0x00000  # x22 = 0x00000788
    78c: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007a0
    790: 001b9b93  slli         x23, x23, 1
    794: 017b0b33  add          x22, x22, x23
    798: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    79c: 00008067  jalr         x0, 0(x1)
    7a0: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7a4: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7a8: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7ac: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_7b0:
    7b0: 7cc00a93  addi         x21, x0, 1996  # x21 = 0x000007cc
    7b4: 000aaa03  lw           x20, 0(x21)  # param e2e_context; 0x000007cc
    7b8: 007a7d13  andi         x26, x20, 7
    7bc: ff8a7a13  andi         x20, x20, -8
    7c0: 01af8ab3  add          x21, x31, x26
    7c4: 007afb93  andi         x23, x21, 7
    7c8: 003ada93  srli         x21, x21, 3
    7cc: 00ba9a93  slli         x21, x21, 11
    7d0: 014a8ab3  add          x21, x21, x20
    7d4: 00000b17  auipc        x22, 0x00000  # x22 = 0x000007d4
    7d8: 018b0b13  addi         x22, x22, 24  # x22 = 0x000007ec
    7dc: 001b9b93  slli         x23, x23, 1
    7e0: 017b0b33  add          x22, x22, x23
    7e4: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    7e8: 00008067  jalr         x0, 0(x1)
    7ec: 04110351  PACR         CfgContext=0, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f0: 059104d1  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=3, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    7f4: 04120352  SFPLZ        imm12_math=72, lreg_c=0, lreg_dest=13, instr_mod1=4  # lreg_c: L0; lreg_dest: L13; Unreachable by statically known control flow
    7f8: 059204d2  SFPLZ        imm12_math=1608, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
    7fc:           j FW_NCRISC+4   # return to firmware, linked at install
