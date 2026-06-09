# abstractions 

## how a kernel reaches the hardware

```mermaid
flowchart TD
    E{"backend?"}
    E -- "fast dispatch" --> V["open PCIe device<br/>(VFIO/IOMMU)"]
    E -- "TT_USB=1: slow dispatch" --> U["open PCIe device<br/>(BAR MMIO only)"]
    E -- "EMU=1: slow dispatch" --> EM["EmuPCIDevice<br/>(software-emulated BARs)"]

    V --> T
    U --> T
    EM --> T["set up TLB windows: write x/y/addr<br/>into TLB config regs in the BAR, mmap window"]

    T --> FW["upload base firmware via TLB windows<br/>all 120 worker cores"]

    FW -- "slow" --> S1["host writes kernels + launch msg<br/>core-by-core via TLB window"]
    S1 --> S2["host mcasts GO_MSG → execution starts;<br/>host polls L1 for done"]

    FW -- "fast" --> CQ["launch CQ kernels on 2 reserved cores<br/>(prefetch + dispatch); 118 program cores remain"]
    CQ --> F1["CQ kernels run; prefetcher polls its prefetch_q"]
    F1 --> F2["host writes kernels as CQ commands into sysmem,<br/>bumps prefetch_q via TLB window"]
    F2 --> F3["prefetcher DMAs commands over PCIe;<br/>dispatcher mcasts kernels + GO → execution starts"]
    F3 --> F4["host polls completion queue in sysmem"]

    S2 --> Z["read results"]
    F4 --> Z
```

slow dispatch is the host doing everything itself through MMIO TLB windows. fast dispatch still uploads base FW to every worker, then launches CQ kernels on two reserved tensix cores (prefetch + dispatch) fed by a host sysmem buffer DMA'd over PCIe — `TT_USB=1` skips VFIO/IOMMU entirely so only BAR MMIO is needed. `EMU=1` swaps in `EmuPCIDevice` (forcing `TT_USB=1`), so kernels run against an emulated device through the exact same slow dispatch path — everything from FW upload onward is identical.

## pcie / dram


## dsl.py 

## asm.py

## fw

## ttk/* 
