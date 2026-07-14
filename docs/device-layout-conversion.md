# Host layout conversion

All buffers exposed through `Device.write()` and `Device.read()` contain
row-major bytes. There is no public layout flag.

The device compute path continues to use the native four-face tile layout. A
`32 x 32` tile is split into four `16 x 16` faces in this order:

```text
top-left, top-right, bottom-left, bottom-right
```

`Device.write()` converts each row-major tile to that layout, stages it in its
own pending slice, and queues the DRAM transfer program. A later `Device.run()`
runs that program immediately before subsequently queued compute. `Device.read()`
runs an ordinary DRAM-read program and applies the inverse conversion afterward.
The conversion is a NumPy reshape, transpose, and byte copy; it does not
interpret or numerically convert the elements.

For tensors larger than one tile, the last two dimensions are divided into
`32 x 32` tiles. Leading dimensions are preserved. Each physical DRAM page is
one complete tile, so pages remain interleaved across the seven DRAM banks at
tile granularity.

The resulting path is:

```text
host row-major bytes
  -> NumPy tilize
  -> tiled DRAM pages
  -> tiled input CB
  -> ordinary unpack, math, and pack
  -> tiled output CB
  -> tiled DRAM pages
  -> NumPy untilize
  -> host row-major bytes
```

This keeps host indexing conventional and leaves kernel indexing and Tensix
configuration conventional. It also avoids the specialized Blackhole
unpack-tilize and pack-untilize modes, including their MOP, DEST remap, and
row-unswizzle requirements.

The padded tensor height and width must both be multiples of 32. Reads and
writes still transfer exactly `buffer.size` bytes.
