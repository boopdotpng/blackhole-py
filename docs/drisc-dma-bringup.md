# DRISC / GDDR DMA Bringup Notes

Blackhole DRAM cores are programmable DRISC cores. On P100a there are seven
enabled GDDR banks/controllers, and each bank exposes three DRAM endpoint cores.
In blackhole-py those endpoint coordinates are in `BoardInfo.dram_tiles` as
`(bank, x, y)`.

The DRISC core shape is simpler than a Tensix worker:

- One RISC processor, treated as BRISC by the reset/debug registers.
- 128 KiB DRISC L1.
- 16 NoC overlay streams on DRAM cores.
- A local GDDR DMA engine, accessed by DRISC-only registers at `0xFC000000` and
  `0xFC001000`.

Important address modes:

- In NOC2AXI mode, normal address `0x0` through a DRAM endpoint routes to GDDR.
- To target DRISC L1 from the host/NoC in NOC2AXI mode, use the high alias
  `0x2000000000 + l1_offset`.
- TT-Metal DRISC firmware forces NOC2AXI mode on boot. Kernels that switch to
  stream mode should restore NOC2AXI before returning.

DRISC memory map constants from TT-Metal:

- `MEM_DRISC_L1_SIZE = 128 KiB`
- `MEM_DRISC_FIRMWARE_BASE = 0x3260`
- `MEM_DRISC_FIRMWARE_SIZE = 24 KiB`
- `DRISC_RESET_PC = 0xFFB14000`

Programming model:

1. Write code/data into DRISC L1 through the `0x2000000000` alias.
2. Use the Blackhole register TLB (`REG_TLB = 191`) for local debug registers.
3. Assert `SOFT_RESET_BRISC = 0x800` in `SOFT_RESET_0`.
4. Write `DRISC_RESET_PC` with the DRISC L1 code address.
5. Deassert `SOFT_RESET_BRISC`.
6. Poll DRISC L1 for completion or timing data.
7. Reassert `SOFT_RESET_BRISC` if the test kernel spins.

`examples/drisc_hello.py` verifies this minimal launch path. It writes a tiny
RISC-V program to DRISC L1, starts the DRISC, polls a magic word in L1, then
reasserts reset.

## GDDR DMA POC

`examples/drisc_gddr_dma_poc.py` verifies the local GDDR DMA engine in both
directions:

- Host writes a pattern to a bank-local GDDR address through the DRAM endpoint.
- DRISC runs a DMA read from that GDDR address into DRISC L1.
- Host reads DRISC L1 through the high alias and checks the pattern.
- Host writes a different pattern to DRISC L1.
- DRISC runs a DMA write from DRISC L1 to another bank-local GDDR address.
- Host reads GDDR through the DRAM endpoint and checks the pattern.

Verified runs:

| size | iterations | total bytes | read | write |
|---:|---:|---:|---:|---:|
| `4096` | `1` | `4096` | ok | ok |
| `32768` | `1` | `32768` | ok | ok |
| `102400` | `1024` | `104857600` | `59.6 GB/s` | `64.0 GB/s` |
| `102400` | `8192` | `838860800` | `59.6 GB/s` | `64.0 GB/s` |

The timed rows use device-side wall clock around repeated DMA commands on one
DRAM endpoint, with one local DMA stream. The default staging region is now
`0x6000..0x1f000`, so each command can transfer up to `102400` bytes while
leaving room for code and result metadata.

Bank 0 endpoint sweep with `102400` bytes x `4096` iterations:

| endpoint | DRAM core | read | write |
|---:|---|---:|---:|
| `0` | `(0, 0)` | `59.6 GB/s` | `64.0 GB/s` |
| `1` | `(0, 1)` | `59.6 GB/s` | `64.0 GB/s` |
| `2` | `(0, 11)` | `59.6 GB/s` | `64.0 GB/s` |

All three endpoints land on the same throughput, so the single-endpoint DMA
path appears controller-limited rather than endpoint-limited.

The DMA trigger is just register programming from the DRISC:

GDDR to DRISC L1:

1. `TX_REG_STREAM_READ_TRANSFER_SOURCE_LOW/HIGH = gddr_addr`
2. `TX_REG_STREAM_READ_TRANSFER_DEST = drisc_l1_addr`
3. `TX_REG_STREAM_TRANSFER_ATTRIBUTES = 0x83000000 | (size_bytes / 16)`
4. Poll `TX_REG_STREAM_STATUS` until `0x0000FF10` clears.

DRISC L1 to GDDR:

1. `TX_REG_STREAM_WRITE_TRANSFER_START_ADDR = drisc_l1_addr`
2. `TX_REG_STREAM_WRITE_DEST_ADDR_LOW/HIGH = gddr_addr`
3. `TX_REG_STREAM_TRANSFER_ATTRIBUTES = 0x10000000 | (size_bytes / 16)`
4. Poll `TX_REG_STREAM_STATUS` until `0xF00F0009` clears.

The global transfer attributes register is set to `0x0003FF01`, matching
`dma_enable=1` with max AXI burst size `255`.

This path does not select worker tiles or worker CBs. The DMA destination for a
read is a byte address in the local DRISC L1 of the DRAM endpoint running the
kernel. The GDDR address is bank-local to that endpoint/controller. To move the
data into worker tile buffers, a second stage is still needed: DRISC L1 to
worker L1 via NoC write, stream overlay, or remote circular buffer.

The practical use case is a DRAM-core staging pipeline, not direct worker tile
placement:

1. DRISC DMA pulls a chunk from local GDDR into DRISC L1.
2. DRISC pushes that chunk to worker L1/CBs over NoC.
3. Workers consume from L1 while DRISC fetches the next chunk.

That only helps if the DRISC-side prefetch/fanout can overlap compute or reduce
worker-side NoC command overhead. It does not remove the GDDR bandwidth limit;
for one bank the measured raw DMA path is still about `60 GB/s`.

The next benchmark step is to port TT-Metal's `experimental/gddr_dma.h`
sequence into a blackhole-py DRISC kernel:

- `dma_set_burst_size(255)`
- `dma_async_read(stream, src_gddr, dst_l1, size_bytes)`
- `dma_async_write(stream, src_l1, dst_gddr, size_bytes)`
- poll `TX_REG_STREAM_STATUS_REG_OFFSET` for read/write completion

That will measure the raw DRISC L1 <-> GDDR path, instead of the current worker
NCRISC NoC path.
