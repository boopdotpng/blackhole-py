# cq_dispatch_s_ncrisc

## Summary

| field | value |
| --- | ---: |
| kind | `ncrisc` |
| base | `0x0` |
| instructions | 3 |
| text bytes | 12 (`0xc`) |

## Segments

| label | address | size | flags |
| --- | ---: | ---: | --- |
| `text` | `0x0` | 12 (`0xc`) | `RX` |

## Disassembly

```python
; cq_dispatch_s_ncrisc: blackhole-py firmware

  00000000:  ffb02137  lui(sp, 0xFFB02000)  # sp=LOCAL_RAM_END+1 (RISC_LOCAL_RAM_END+1)
  00000004:  ff010113  addi(sp, sp, -16)  # sp=NCRISC_STACK_TOP (RISC_LOCAL_RAM+0x1ff0)
idle:
  00000008:  0000006f  jal(zero, idle)  # jal(zero, 0)
```
