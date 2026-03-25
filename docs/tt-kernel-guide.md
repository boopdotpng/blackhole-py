# describes how to write kernels for tenstorrent cards and includes the entire API space 

glossary: 

tiles: 32x32 elements of data (any dtype). these are weird, its 4 16x16 faces arranged in a strange manner. you have to tilize the data before the compute and untilize it afterwards so its readable on the host. see current code for how the tilize works in software, but this is a simple bit flip on the packer config of the first compute kernel if you want to enable it. more info about this in the packer/unpacker api section

the hardware requires this arrangement because the compute engine iterates over faces (z dimension), then rows/cols within each face, not over a flat row major array. this can be done very fast in hardware, on the trisc0,2 cores. you should only tilize once when the tensor is uploaded (during the first compute kernel) so that all future kernels can skip the tilize step. then, you can untilize when reading the data back to host when you need to access the tensor from dram. 

cb:  circular buffers (queues) in the L1 buffer of each tile that contain tiles. you can set the size of each "spot" in the cb and how deep the cb is. the entire architecture revolves around filling CBs through the dataflow kernels and then having your compute triscs blaze through tiles (elements in the CB) as fast as possible. every kernel on this device is limited by DRAM read/write speed, not the speed of the compute. you set the size and shape of these CBs in the compiler options while compiling the kernel. 
you should never set the CB depth to 1, because that removes all parallelism. the idea is to have multiple tiles in flight at the same time, so that you can read tiles from dram and compute them at the same time. 
you also have to balance the size of the CBs. you only have ~1.3MB of space in each core's L1, and CBs take up that space. so you can't over-allocate CBs. this is only really an issue when doing fp32 matmuls, but it's important to note. cranking CB depth won't really help up to a certain point. a good default i've seen is 2-3. 

semaphores: 

## basic kernel flow 
5 cores: 

ncrisc (reader)
Reads data from dram into CBs

trisc0 
packs the cb for consumption by the next core. 

trisc1
pushes tt_* instructions into the fifo queue for the tensix coprocessor to execute. there are a lot of fancy tricks going on here, especially with the MOP and replay buffer. 

tensix coprocessor
does the actual compute. the instruction space here is quite small; there are two main subsystems here: 

SFPU 

Lregs, basic SIMD machine. 

Instructions: 

FPU
srcA and srcB, two of each. final answer accumulates into `dst`. 
both are `uint19_t rows[64][16]`. 

trisc2
packs the data back into an output CB 

brisc (writer)
writes the output CB back to DRAM when they become available. 

In practice, you don't write 5 individual kernels. its three. you write a ncrisc, brisc, and trisc. there is a very intricate macro/define system in tt-metal that wraps certain functions like "pack" in a `TRISC0` macro so that it only gets compiled if you specify -DTRISC1 (or some option like this) to the compiler. 

## pre-kernel compiler configs


## dataflow (reader)


## compute 


## dataflow (writer)

## debugging 
