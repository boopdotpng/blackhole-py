when we write the ptx compiler, the compiler needs to do the following: 

risc-v register allocations 
sfpu scheduler and allocations
noc batching (batch many noc requests together and track wait / commits groups) 
cb allocations, reserve_back, push, add the counter,
core placement is important when dram reading and writing is a high % of the kernel. you need to place cores to 1) optimize mcast rectangles during launch and 2) be close to dram tiles
