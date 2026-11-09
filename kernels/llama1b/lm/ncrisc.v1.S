# llama3 1B decode: lm, ncrisc. Exported from blackhole-py/examples/llama3/kernels.py by tools/export_llama1b.py.
# cores (13): 2,2 5,2 10,2 13,2 3,3 6,3 11,3 1,4 4,4 7,4 12,4 2,5 5,5
# params: 0x7c0=e2e_x_a_decode_token, 0x7c4=e2e_lm_weight, 0x7c8=e2e_final_norm, 0x8180=e2e_logits, 0x8184=e2e_lm_weight_row_start
#   0x7c0.. uniform, sent with every EXEC; 0x8000.. this core's resident per-core table
# pcs are offsets from the image start; llama1b.py installs it resident in L1 at 0x12000+ per core.

      0: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
      4: 86430313  addi         x6, x6, -1948  # x6 = 0xffb00864 · riscv_local_mem + 0x864
      8: 000923b7  lui          x7, 0x00092  # x7 = 0x00092000
      c: 00732023  sw           x7, 0(x6)  # riscv_local_mem + 0x864 · 0xffb00864; write 0x00092000
     10: ffb01337  lui          x6, 0xffb01  # x6 = 0xffb01000
     14: 86830313  addi         x6, x6, -1944  # x6 = 0xffb00868 · riscv_local_mem + 0x868
     18: 00032023  sw           x0, 0(x6)  # riscv_local_mem + 0x868 · 0xffb00868; write 0x00000000
     1c: 00094237  lui          x4, 0x00094  # x4 = 0x00094000
     20: 40000293  addi         x5, x0, 1024  # x5 = 0x00000400
loc_24:
     24: 00022023  sw           x0, 0(x4)  # Address depends on runtime register values
     28: 00022223  sw           x0, 4(x4)  # Address depends on runtime register values
     2c: 00022423  sw           x0, 8(x4)  # Address depends on runtime register values
     30: 00022623  sw           x0, 12(x4)  # Address depends on runtime register values
     34: 00022823  sw           x0, 16(x4)  # Address depends on runtime register values
     38: 00022a23  sw           x0, 20(x4)  # Address depends on runtime register values
     3c: 00022c23  sw           x0, 24(x4)  # Address depends on runtime register values
     40: 00022e23  sw           x0, 28(x4)  # Address depends on runtime register values
     44: 02020213  addi         x4, x4, 32
     48: ff828293  addi         x5, x5, -8
     4c: fc029ce3  bne          x5, x0, 0x00000024  # target 0x00000024
     50: 00000213  addi         x4, x0, 0  # x4 = 0x00000000
     54: 5b200293  addi         x5, x0, 1458  # x5 = 0x000005b2
loc_58:
     58: 0e527863  bgeu         x4, x5, 0x00000148  # target 0x00000148
     5c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     60: 86850513  addi         x10, x10, -1944  # x10 = 0xffb00868 · riscv_local_mem + 0x868
     64: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x868 · 0xffb00868
     68: 00100493  addi         x9, x0, 1  # x9 = 0x00000001
loc_6c:
     6c: ffb49537  lui          x10, 0xffb49  # x10 = 0xffb49000
     70: 02850513  addi         x10, x10, 40  # x10 = 0xffb49028
     74: 00055383  lhu          x7, 0(x10)  # 0xffb49028
     78: 40638433  sub          x8, x7, x6
     7c: 01041413  slli         x8, x8, 16
     80: 01045413  srli         x8, x8, 16
     84: 00947663  bgeu         x8, x9, 0x00000090  # target 0x00000090
     88: 0ff0000f  fence        0xf, 0xf
     8c: fe1ff06f  jal          x0, 0x0000006c  # target 0x0000006c
loc_90:
     90: 0ff0000f  fence        0xf, 0xf
     94: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
     98: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
     9c: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
     a0: 00035383  lhu          x7, 0(x6)  # Address depends on runtime register values
     a4: 00f27413  andi         x8, x4, 15
     a8: 00141413  slli         x8, x8, 1
     ac: 01027513  andi         x10, x4, 16
     b0: 00551513  slli         x10, x10, 5
     b4: 00a46433  or           x8, x8, x10
     b8: 1e027513  andi         x10, x4, 480
     bc: 00a46433  or           x8, x8, x10
     c0: 00925513  srli         x10, x4, 9
     c4: 00a51513  slli         x10, x10, 10
     c8: 00a46433  or           x8, x8, x10
     cc: 000944b7  lui          x9, 0x00094  # x9 = 0x00094000
     d0: 008484b3  add          x9, x9, x8
     d4: 00749023  sh           x7, 0(x9)  # Address depends on runtime register values
     d8: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     dc: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     e0: 0003a303  lw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868
     e4: 00130313  addi         x6, x6, 1
     e8: 01031313  slli         x6, x6, 16
     ec: 01035313  srli         x6, x6, 16
     f0: ffb013b7  lui          x7, 0xffb01  # x7 = 0xffb01000
     f4: 86838393  addi         x7, x7, -1944  # x7 = 0xffb00868 · riscv_local_mem + 0x868
     f8: 0063a023  sw           x6, 0(x7)  # riscv_local_mem + 0x868 · 0xffb00868; write runtime value
     fc: ffb493b7  lui          x7, 0xffb49  # x7 = 0xffb49000
    100: 02038393  addi         x7, x7, 32  # x7 = 0xffb49020
    104: 0063a023  sw           x6, 0(x7)  # 0xffb49020; write runtime value
    108: 0ff0000f  fence        0xf, 0xf
    10c: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    110: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    114: 00052303  lw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864
    118: 000013b7  lui          x7, 0x00001  # x7 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    11c: 80038393  addi         x7, x7, -2048  # x7 = 0x00000800
    120: 00730333  add          x6, x6, x7
    124: 00093437  lui          x8, 0x00093  # x8 = 0x00093000
    128: 00836663  bltu         x6, x8, 0x00000134  # target 0x00000134
    12c: 000014b7  lui          x9, 0x00001  # x9 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    130: 40930333  sub          x6, x6, x9
loc_134:
    134: ffb01537  lui          x10, 0xffb01  # x10 = 0xffb01000
    138: 86450513  addi         x10, x10, -1948  # x10 = 0xffb00864 · riscv_local_mem + 0x864
    13c: 00652023  sw           x6, 0(x10)  # riscv_local_mem + 0x864 · 0xffb00864; write runtime value
    140: 00120213  addi         x4, x4, 1
    144: f15ff06f  jal          x0, 0x00000058  # target 0x00000058
loc_148:
    148: 00000f93  addi         x31, x0, 0  # x31 = 0x00000000
    14c: 064000ef  jal          x1, 0x000001b0  # target 0x000001b0; x1 = 0x00000150
    150: 000a8213  addi         x4, x21, 0
    154: 000b0293  addi         x5, x22, 0
    158: 0a8000ef  jal          x1, 0x00000200  # target 0x00000200; x1 = 0x0000015c
    15c: 0c0000ef  jal          x1, 0x0000021c  # target 0x0000021c; x1 = 0x00000160
    160: 00094fb7  lui          x31, 0x00094  # x31 = 0x00094000
    164: 00020f13  addi         x30, x4, 0
    168: 00028e93  addi         x29, x5, 0
    16c: 0cc000ef  jal          x1, 0x00000238  # target 0x00000238; x1 = 0x00000170
    170: 090000ef  jal          x1, 0x00000200  # target 0x00000200; x1 = 0x00000174
    174: 0a8000ef  jal          x1, 0x0000021c  # target 0x0000021c; x1 = 0x00000178
    178: 00100f93  addi         x31, x0, 1  # x31 = 0x00000001
    17c: 034000ef  jal          x1, 0x000001b0  # target 0x000001b0; x1 = 0x00000180
    180: 000a8213  addi         x4, x21, 0
    184: 000b0293  addi         x5, x22, 0
    188: 078000ef  jal          x1, 0x00000200  # target 0x00000200; x1 = 0x0000018c
    18c: 090000ef  jal          x1, 0x0000021c  # target 0x0000021c; x1 = 0x00000190
    190: 00095fb7  lui          x31, 0x00095  # x31 = 0x00095000
    194: 800f8f93  addi         x31, x31, -2048  # x31 = 0x00094800
    198: 00020f13  addi         x30, x4, 0
    19c: 00028e93  addi         x29, x5, 0
    1a0: 098000ef  jal          x1, 0x00000238  # target 0x00000238; x1 = 0x000001a4
    1a4: 05c000ef  jal          x1, 0x00000200  # target 0x00000200; x1 = 0x000001a8
    1a8: 074000ef  jal          x1, 0x0000021c  # target 0x0000021c; x1 = 0x000001ac
    1ac: 1480006f  jal          x0, 0x000002f4  # target 0x000002f4
loc_1b0:
    1b0: 00008ab7  lui          x21, 0x00008  # x21 = 0x00008000
    1b4: 180a8a93  addi         x21, x21, 384  # x21 = 0x00008180
    1b8: 000aaa03  lw           x20, 0(x21)  # param e2e_logits; 0x00008180
    1bc: 007a7d13  andi         x26, x20, 7
    1c0: ff8a7a13  andi         x20, x20, -8
    1c4: 01af8ab3  add          x21, x31, x26
    1c8: 007afb93  andi         x23, x21, 7
    1cc: 003ada93  srli         x21, x21, 3
    1d0: 00ba9a93  slli         x21, x21, 11
    1d4: 014a8ab3  add          x21, x21, x20
    1d8: 00000b17  auipc        x22, 0x00000  # x22 = 0x000001d8
    1dc: 018b0b13  addi         x22, x22, 24  # x22 = 0x000001f0
    1e0: 001b9b93  slli         x23, x23, 1
    1e4: 017b0b33  add          x22, x22, x23
    1e8: 000b5b03  lhu          x22, 0(x22)  # Address depends on runtime register values
    1ec: 00008067  jalr         x0, 0(x1)
    1f0: 04510351  PACR         CfgContext=0, RowPadZero=5, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=0, OvrdThreadId=1, Concat=5, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    1f4: 05910491  PACR         CfgContext=3, RowPadZero=1, DstAccessMode=0, AddrMode=0, AddrCntContext=2, ZeroWrite=0, ReadIntfSel=1, OvrdThreadId=0, Concat=2, CtxtCtrl=1, Flush=0, Last=0  # Unreachable by statically known control flow
    1f8: 04520312  SFPLZ        imm12_math=328, lreg_c=0, lreg_dest=12, instr_mod1=4  # lreg_c: L0; lreg_dest: L12; Unreachable by statically known control flow
    1fc: 055204d2  SFPLZ        imm12_math=1352, lreg_c=1, lreg_dest=3, instr_mod1=4  # lreg_c: L1; lreg_dest: L3; Unreachable by statically known control flow
loc_200:
    200: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    204: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    208: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    20c: 000a0463  beq          x20, x0, 0x00000214  # target 0x00000214
    210: ff1ff06f  jal          x0, 0x00000200  # target 0x00000200
loc_214:
    214: 0ff0000f  fence        0xf, 0xf
    218: 00008067  jalr         x0, 0(x1)
loc_21c:
    21c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    220: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    224: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    228: 000a0463  beq          x20, x0, 0x00000230  # target 0x00000230
    22c: ff1ff06f  jal          x0, 0x0000021c  # target 0x0000021c
loc_230:
    230: 0ff0000f  fence        0xf, 0xf
    234: 00008067  jalr         x0, 0(x1)
loc_238:
    238: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    23c: 284a8a93  addi         x21, x21, 644  # x21 = 0xffb30284 · noc1_regs + 0x284
    240: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x284 · 0xffb30284
    244: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    248: 015a6463  bltu         x20, x21, 0x00000250  # target 0x00000250
    24c: fedff06f  jal          x0, 0x00000238  # target 0x00000238
loc_250:
    250: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    254: 244a8a93  addi         x21, x21, 580  # x21 = 0xffb30244 · noc1_regs + 0x244
    258: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x244 · 0xffb30244
    25c: 08100a93  addi         x21, x0, 129  # x21 = 0x00000081
    260: 015a6463  bltu         x20, x21, 0x00000268  # target 0x00000268
    264: fedff06f  jal          x0, 0x00000250  # target 0x00000250
loc_268:
    268: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
    26c: 148a8a93  addi         x21, x21, 328  # x21 = 0xffb30148 · noc1_regs + 0x148
    270: 000aaa03  lw           x20, 0(x21)  # noc1_regs + 0x148 · 0xffb30148
    274: 014a1a13  slli         x20, x20, 20
    278: 014a5a13  srli         x20, x20, 20
    27c: ffb30ab7  lui          x21, 0xffb30  # x21 = 0xffb30000 · noc1_regs + 0x0
loc_280:
    280: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    284: 000b0463  beq          x22, x0, 0x0000028c  # target 0x0000028c
    288: ff9ff06f  jal          x0, 0x00000280  # target 0x00000280
loc_28c:
    28c: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    290: 01fba023  sw           x31, 0(x23)  # noc1_regs + 0x0 · 0xffb30000; write runtime value
    294: 000ba223  sw           x0, 4(x23)  # noc1_regs + 0x4 · 0xffb30004; write 0x00000000
    298: 014ba423  sw           x20, 8(x23)  # noc1_regs + 0x8 · 0xffb30008; write runtime value
    29c: 01eba623  sw           x30, 12(x23)  # noc1_regs + 0xc · 0xffb3000c; write runtime value
    2a0: 000ba823  sw           x0, 16(x23)  # noc1_regs + 0x10 · 0xffb30010; write 0x00000000
    2a4: 01dbaa23  sw           x29, 20(x23)  # noc1_regs + 0x14 · 0xffb30014; write runtime value
    2a8: 40000c13  addi         x24, x0, 1024  # x24 = 0x00000400
    2ac: 018bac23  sw           x24, 24(x23)  # noc1_regs + 0x18 · 0xffb30018; write 0x00000400
    2b0: 00002c37  lui          x24, 0x00002  # x24 = 0x00002000
    2b4: 092c0c13  addi         x24, x24, 146  # x24 = 0x00002092
    2b8: 018bae23  sw           x24, 28(x23)  # noc1_regs + 0x1c · 0xffb3001c; write 0x00002092
    2bc: 00001c37  lui          x24, 0x00001  # x24 = 0x00001000 · F32_TILE_BYTES · Wait.CFGEXU
    2c0: 800c0c13  addi         x24, x24, -2048  # x24 = 0x00000800
    2c4: 038ba023  sw           x24, 32(x23)  # noc1_regs + 0x20 · 0xffb30020; write 0x00000800
    2c8: 020ba223  sw           x0, 36(x23)  # noc1_regs + 0x24 · 0xffb30024; write 0x00000000
    2cc: 020ba423  sw           x0, 40(x23)  # noc1_regs + 0x28 · 0xffb30028; write 0x00000000
    2d0: 020ba623  sw           x0, 44(x23)  # noc1_regs + 0x2c · 0xffb3002c; write 0x00000000
    2d4: ffb30bb7  lui          x23, 0xffb30  # x23 = 0xffb30000 · noc1_regs + 0x0
    2d8: 040b8b93  addi         x23, x23, 64  # x23 = 0xffb30040 · noc1_regs + 0x40
    2dc: 00100c13  addi         x24, x0, 1  # x24 = 0x00000001
    2e0: 018ba023  sw           x24, 0(x23)  # noc1_regs + 0x40 · 0xffb30040; write 0x00000001
loc_2e4:
    2e4: 040aab03  lw           x22, 64(x21)  # noc1_regs + 0x40 · 0xffb30040
    2e8: 000b0463  beq          x22, x0, 0x000002f0  # target 0x000002f0
    2ec: ff9ff06f  jal          x0, 0x000002e4  # target 0x000002e4
loc_2f0:
    2f0: 00008067  jalr         x0, 0(x1)
    2f4:           j FW_NCRISC+4   # return to firmware, linked at install
