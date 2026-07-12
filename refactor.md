# refactor notes for blackhole-py-rewrite

## goals
lower line count (sz.py)
decrease complexity
make ttk/ do more stuff in a better abstracted way to avoid kernels failing to launch

also remove all docstrings and comments, i will add them back later 

## pcie.py 
we should maybe rename bumpallocator to something else? there are three allocators used throughout this project and i think we should make an attempt to unify them all. 
1. sysmem allocator (this keeps track of the three sysmem regions: timestamps / cq data, dram transfer arena, and the cq ring where progams and dispatch commands are read from) -- i think this should stay in class Sysmem
2. the allocator inside the dram arena that keeps track of where buffers are in the arena currently, how much space is left, where new buffers can be written, and buffer lifetime. when you make a buffer() it gets a spot here before being sent to the device. 
3. the actual dram allocator. keeps track of where tensors are in dram. we only need to store (name, addr, size) for this, its interleaved across 7 banks, but the host does not need to know this. we just need to bump next. 
4. the local memory allocator inside every asm kernel. i'm not even sure if this is used or necessary beyond a certain hardcoded cases, maybe we can delete this? we can keep track of a few hardcoded regions where config or the ret address to the fw kernel will live, beyond that all of our math is in registers, and we don't do register spilling or anything

## program.py
1. can we remove this __post_init__ stuff? too many lines and extra validation. do this throughout the repo please
2. in general i think we do too much checking throughout the repo. we should keep bare minimum alignment and size checks, but that's about it. just assign default values to stuff
3. we only use some of the @property decorators more than once, we can just inline the computation there, in cb config and buffer (and other places). if you see them more than once and they're useful, keep them. 
4. validate in class Param will eventually be handled by tinygrad's TinyJit, you can remove this for now. we trust our runtime 
5.
def param(self, name: str):
    """Return a declared parameter by name."""
    matches = [param for param in self.params if param.name == name]
    if not matches: raise KeyError(name)
    return matches[0]
this should probably be a dictionary right? why do an O(N) lookup every time
6. reduce amount of validation in kernelbundle

## asm.py 
KernelRole = Literal["brisc", "ncrisc", "trisc0", "trisc1", "trisc2"]
KERNEL_ROLES: tuple[KernelRole, ...] = ("brisc", "ncrisc", "trisc0", "trisc1", "trisc2")
i think this is duplicated in another file? program.py, i think
can we consolidate them

_BRANCHES = {"beq", "bne", "blt", "bge", "bltu", "bgeu"}
_INVERT = {"beq": "bne", "bne": "beq", "blt": "bge", "bge": "blt", "bltu": "bgeu", "bgeu": "bltu"}
_CONDS = {"==": ("beq", False), "!=": ("bne", False), "<": ("blt", False), ">=": ("bge", False),
          "<u": ("bltu", False), ">=u": ("bgeu", False), ">": ("blt", True), "<=": ("bge", True),
          ">u": ("bltu", True), "<=u": ("bgeu", True)}
this is weird imo, can we merge this into class Cond and have it figure this out instead of having it as global constants? 

i also dont like how standalone is done, feels like it should just take "role, Asm" and then build a kernel based on that. maybe it should be KernelBuilder.standalone() (staticmethod, not what it is now?) and we skip the ret jumps and etc? this is only used for the firmware, by the way, so maybe we can rename it to something else and make the path more straightforward. 

more validation removal in KernelBuilder.__init__

## cq.py
can we pack constants multiple per line to save lines? 

can class Packet be a dataclass? 

runresult is confusing, can we just have this be called Timestamp? 
this is the time the last core finishes the program, i.e. total kernel time, divided by the active clock (always 1350mhz) 

why do we have class Fence? do we use it / can it be removed? this is just a fancy wait between events, which the CQ firmware is already doing? Timestamp is the implicit wait, if you get this, the kernel is for sure done

## device.py
I think reset_cores only needs to reset the prefetch and dispatch cores, not all the cores. firmware will do that when we boot the next time or launch the next kernel. 

the firmware upload methods need to be cleaned up. we can make this two methods, run in this order: 

- upload_core_fw, which uploads the base firmware to all the cores (including the cq cores).
- upload_cq_firmware, which just uploads the prefetch and dispatch firmware. 

the cq firmware is just a regular program that runs on 14,2 and 14,3 (prefetch/dispatch) 

the upload_resident_firmware is doing too much work, and we're validating the upload result which is not required. i'm not even sure if we need to wait after the firmware upload. can we trim this down and follow the bare minimum that ~/tenstorrent/blackhole-py does? 

win.write(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC - reset_base,
                  Firmware.TEXT_BASE["ncrisc"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC0_RESET_PC - reset_base,
                  Firmware.TEXT_BASE["trisc0"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC1_RESET_PC - reset_base,
                  Firmware.TEXT_BASE["trisc1"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC2_RESET_PC - reset_base,
                  Firmware.TEXT_BASE["trisc2"])
        win.write(TensixMMIO.RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE - reset_base, 0b111)
        win.write(TensixMMIO.RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE - reset_base, 1)
i think these are unneccessary too, brisc does when it boots up. we boot brisc, and then it boots the other cores. we can save a lot of lines/complexity here. 