# Execution Model and Scheduling

## 1. Overview

The emulator is a cycle-approximate, single-threaded Python program that models the entire Blackhole device. No OS threads are needed — all cores across all tiles are driven by a single round-robin main loop. The goal is correctness (bit-accurate results, faithful synchronization ordering), not performance.

## 2. Main Loop

Each "tick" of the emulator:

```python
class EmulatedDevice:
    def step(self):
        # 1. Step all RISC-V cores (round-robin across tiles)
        for tile in self.tiles.values():
            for core in tile.cores:
                if not core.in_reset and not core.halted:
                    core.step()  # execute one instruction
        
        # 2. Step all Tensix coprocessors
        for tile in self.tiles.values():
            tile.tensix.step()  # process one instruction per thread if available
        
        # 3. Step NOC fabric (deliver pending transactions)
        self.noc.tick()
        
        self.cycle += 1
    
    def run_until_done(self, max_cycles=10_000_000):
        while self.cycle < max_cycles:
            self.step()
            if self.all_done():
                break
```

Each RISC-V core executes exactly one instruction per `step()` call. The Tensix coprocessor processes one instruction from each thread's frontend per `step()`. NOC transactions are delivered at the end of each tick.

## 3. Core Scheduling

All 5 RISC-V cores per tile (BRISC, NCRISC, TRISC0/1/2) are stepped in order within each tile. All tiles are stepped in order within each tick. This round-robin provides deterministic interleaving without threads.

A core is skipped if:
- `in_reset == True` (held by SOFT_RESET_0 register)
- `halted == True` (core has halted)
- The core is stalled on a full Tensix instruction FIFO, a blocking PCBuf read, or similar hardware stall

## 4. "Done" Detection

A kernel dispatch is done when BRISC writes `RUN_MSG_DONE` (0x00) to the `go_messages[go_message_index].signal` byte in L1. The host side of the emulator polls this.

For a multi-tile workload, the emulator runs until ALL tiles have signaled done (all go_message signals are 0x00), or until a cycle timeout.

## 5. Host-Side Driver

The emulator's host interface drives the firmware through its boot and dispatch protocol:

```python
def run_kernel(device, launch_msg):
    # 1. Assert soft reset on all cores
    for tile in device.tiles.values():
        tile.write_mmio(0xFFB121B0, 0x47800)  # SOFT_RESET_ALL
    
    # 2. Upload firmware and kernel to L1
    upload_firmware(device)
    upload_kernel(device, launch_msg)
    
    # 3. Write go_message signal = RUN_MSG_INIT
    for tile in device.tiles.values():
        tile.l1.write32(0x373, 0x40)
    
    # 4. Release BRISC only
    for tile in device.tiles.values():
        tile.write_mmio(0xFFB121B0, 0x47000)
    
    # 5. Run until all tiles boot (go_msg.signal == RUN_MSG_DONE)
    device.run_until(lambda: all(
        tile.l1.read8(0x373) == 0x00 for tile in device.tiles.values()
    ))
    
    # 6. Write go_message signal = RUN_MSG_GO
    for tile in device.tiles.values():
        tile.l1.write8(0x373, 0x80)
    
    # 7. Run until kernel completes
    device.run_until(lambda: all(
        tile.l1.read8(0x373) == 0x00 for tile in device.tiles.values()
    ))
```

## 6. NOC Transaction Timing

For cycle-approximate modeling, NOC transactions complete with configurable latency:
- Same-tile: 1 tick
- Cross-tile: proportional to Manhattan distance (optional, can be 1 tick for simplicity)
- DRAM: 1 tick (no memory controller latency modeling)

For a functional-first emulator, all NOC transactions can complete immediately when `NOC_CMD_CTRL` is written. Status counters are incremented in the same tick. This makes all firmware barriers (`noc_async_read_barrier`, `noc_async_write_barrier`) resolve on the next poll.

## 7. Tensix Coprocessor Scheduling

Each Tensix coprocessor has 3 threads (T0/T1/T2). Per tick, each thread can advance one instruction through its frontend pipeline (FIFO -> MOP Expander -> Replay Expander -> Wait Gate -> Backend). Backend execution units (FPU, SFPU, Pack, Unpack, etc.) operate concurrently across threads.

For a functional emulator, Tensix instructions can execute synchronously — the instruction completes its side effects immediately when it reaches the backend dispatch stage. STALLWAIT/SEMWAIT still need to block the issuing thread until the condition is met.

## 8. Stall Modeling

Sources of stalls that must be modeled:
- **Instruction FIFO full**: RISC-V core stalls when pushing to a full 32-entry FIFO
- **STALLWAIT/SEMWAIT**: Tensix thread blocks at Wait Gate until condition met
- **PCBuf blocking read**: `tensix_sync()` blocks until coprocessor thread drains
- **Semaphore spin**: firmware `noc_semaphore_wait()` spins on L1 load (no special modeling needed — the spin loop is just RISC-V instructions)
- **NOC barriers**: firmware spins on NIU status counter reads (no special modeling needed with immediate completion)
