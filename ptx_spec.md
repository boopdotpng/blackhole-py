# ptx for blackhole spec

## header
```ptx
.version 1.0 // always
.target tt_30 // grayskull wormhole blackhole
`` `

runtime differences in dram bank counts and core counts are hidden from the ptx entirely. if you request 140 cores and the card only has 120, throw.

## topology, core count, etc:
```ptx

```
