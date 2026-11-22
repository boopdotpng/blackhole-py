#include "TinyGPUDriver.h"
#include "TinyGPUDriverUserClient.h"
#include <DriverKit/IOLib.h>
#include <DriverKit/IODispatchQueue.h>
#include <PCIDriverKit/PCIDriverKit.h>


struct TinyGPUDriver_IVars
{
	IOPCIDevice *pci = nullptr;
	bool asleep = false;
	IOLock *lock = nullptr;
	bool mapped = false;
	uint8_t bar0 = 0;
	IODispatchQueue *parkQueue = nullptr;
};

#define TLB_2M_SIZE        (1ull << 21)
#define TLB_REGS           0x1FC00000u
#define TLB_REG_SIZE       12u
#define DEXT_TLB           199u
#define ARC_X              8u
#define ARC_Y              0u
#define ARC_BOOT_STATUS    0x80030408u
#define ARC_MSG_QCB_PTR    0x8003042Cu
#define ARC_MSI_FIFO       0x800B0000u
#define ARC_MSG_QUEUE_HEADER 32u
#define ARC_MSG_POWER_IDLE (0x21u | 15u << 8)

static bool ParkMmio(TinyGPUDriver_IVars *iv, bool write, uint64_t off, uint32_t *val)
{
	IOLockLock(iv->lock);
	IOPCIDevice *pci = (iv->asleep || iv->mapped) ? nullptr : iv->pci;
	if (pci) {
		if (write) pci->MemoryWrite32(iv->bar0, off, *val);
		else pci->MemoryRead32(iv->bar0, off, val);
	}
	IOLockUnlock(iv->lock);
	return pci != nullptr && (write || *val != 0xFFFFFFFFu);
}

struct ArcWindow
{
	TinyGPUDriver_IVars *iv;
	uint64_t base = ~0ull;
	bool ok = true;

	uint64_t Target(uint32_t addr)
	{
		uint64_t b = addr & ~(TLB_2M_SIZE - 1);
		if (ok && b != base) {
			unsigned __int128 v = (unsigned __int128)(b >> 21) | (unsigned __int128)ARC_X << 43 | (unsigned __int128)ARC_Y << 49
			                    | (unsigned __int128)ARC_X << 55 | (unsigned __int128)ARC_Y << 61 | (unsigned __int128)1 << 70;
			for (int i = 0; i < 3 && ok; i++) {
				uint32_t w = (uint32_t)(v >> (32 * i));
				ok = ParkMmio(iv, true, TLB_REGS + DEXT_TLB * TLB_REG_SIZE + 4 * i, &w);
			}
			base = b;
		}
		return DEXT_TLB * TLB_2M_SIZE + (addr - b);
	}
	uint32_t Read(uint32_t addr) { uint32_t v = 0xFFFFFFFFu; uint64_t off = Target(addr); if (ok) ok = ParkMmio(iv, false, off, &v); return v; }
	void Write(uint32_t addr, uint32_t v) { uint64_t off = Target(addr); if (ok) ok = ParkMmio(iv, true, off, &v); }
};

static void ParkCard(TinyGPUDriver_IVars *iv)
{
	ArcWindow arc{iv};
	for (int i = 0;; i++) {
		uint32_t status = arc.Read(ARC_BOOT_STATUS);
		if (arc.ok && (status & 1)) break;
		if (i >= 300) { os_log(OS_LOG_DEFAULT, "tinygpu: park: ARC not ready"); return; }
		arc.ok = true;
		arc.base = ~0ull;
		IOSleep(100);
		IOLockLock(iv->lock);
		bool gone = !iv->pci || iv->asleep || iv->mapped;
		IOLockUnlock(iv->lock);
		if (gone) return;
	}
	uint32_t qcb = arc.Read(ARC_MSG_QCB_PTR), q = arc.Read(qcb), entries = arc.Read(qcb + 4) & 0xFF;
	if (!arc.ok || !entries) return;
	uint32_t wrap = 2 * entries, responses = q + ARC_MSG_QUEUE_HEADER + entries * 32;
	auto pop = [&]() -> bool {
		uint32_t rptr = arc.Read(q + 0x04), wptr = arc.Read(q + 0x14);
		if (!arc.ok || (wptr + wrap - rptr) % wrap == 0) return false;
		uint32_t status = arc.Read(responses + (rptr % entries) * 32);
		arc.Write(q + 0x04, (rptr + 1) % wrap);
		if (arc.ok) os_log(OS_LOG_DEFAULT, "tinygpu: park: ARC response 0x%x", status);
		return arc.ok;
	};
	for (uint32_t i = 0; i < entries && pop(); i++) {}
	uint32_t wptr = arc.Read(q), rptr = arc.Read(q + 0x10);
	if (!arc.ok || (wptr + wrap - rptr) % wrap >= entries) return;
	uint32_t slot = q + ARC_MSG_QUEUE_HEADER + (wptr % entries) * 32;
	for (uint32_t i = 0; i < 8; i++) arc.Write(slot + 4 * i, i ? 0 : ARC_MSG_POWER_IDLE);
	arc.Write(q, (wptr + 1) % wrap);
	arc.Write(ARC_MSI_FIFO, 0);
	for (int ms = 0; ms < 1000 && arc.ok && !pop(); ms++) IOSleep(1);
	os_log(OS_LOG_DEFAULT, "tinygpu: park: idle vote %s", arc.ok ? "sent" : "abandoned");
}

bool TinyGPUDriver::init()
{
	if (!super::init()) return false;
	ivars = IONewZero(TinyGPUDriver_IVars, 1);
	if (!ivars) return false;
	ivars->lock = IOLockAlloc();
	return ivars->lock != nullptr;
}

void TinyGPUDriver::free()
{
	if (ivars && ivars->parkQueue) ivars->parkQueue->release();
	if (ivars && ivars->lock) IOLockFree(ivars->lock);
	IOSafeDeleteNULL(ivars, TinyGPUDriver_IVars, 1);
	super::free();
}

kern_return_t TinyGPUDriver::Start_Impl(IOService* in_provider)
{
	kern_return_t err = Start(in_provider, SUPERDISPATCH);
	if (err) return err;

	IOPCIDevice *pci = OSDynamicCast(IOPCIDevice, in_provider);
	if (!pci) return kIOReturnNoDevice;
	if ((err = pci->Open(this, 0))) {
		os_log(OS_LOG_DEFAULT, "tinygpu: Open() failed 0x%08x", err);
		return err;
	}

	uint16_t ven = 0, dev = 0, cmd = 0;
	pci->ConfigurationRead16(kIOPCIConfigurationOffsetVendorID, &ven);
	pci->ConfigurationRead16(kIOPCIConfigurationOffsetDeviceID, &dev);
	pci->ConfigurationRead16(kIOPCIConfigurationOffsetCommand, &cmd);
	pci->ConfigurationWrite16(kIOPCIConfigurationOffsetCommand, cmd | kIOPCICommandMemorySpace);
	os_log(OS_LOG_DEFAULT, "tinygpu: opened device ven=0x%04x dev=0x%04x", ven, dev);

	uint8_t barType; uint64_t barSize;
	bool bar0ok = pci->GetBARInfo(0, &ivars->bar0, &barSize, &barType) == kIOReturnSuccess && barSize >= TLB_REGS + 0x1000;

	IOLockLock(ivars->lock);
	ivars->pci = pci;
	ivars->asleep = false;
	IOLockUnlock(ivars->lock);

	if (bar0ok && IODispatchQueue::Create("park", 0, 0, &ivars->parkQueue) == kIOReturnSuccess) {
		retain();
		TinyGPUDriver_IVars *iv = ivars;
		ivars->parkQueue->DispatchAsync(^{ ParkCard(iv); release(); });
	}

	IOServiceName name;
	strlcpy(name, "ttgpu", sizeof(name));
	SetName(name);
	RegisterService();
	return kIOReturnSuccess;
}

kern_return_t TinyGPUDriver::Stop_Impl(IOService* in_provider)
{
	IOLockLock(ivars->lock);
	IOPCIDevice *pci = ivars->pci;
	ivars->pci = nullptr;
	IOLockUnlock(ivars->lock);
	os_log(OS_LOG_DEFAULT, "tinygpu: stop");
	if (pci) pci->Close(this, 0);
	return Stop(in_provider, SUPERDISPATCH);
}

kern_return_t TinyGPUDriver::SetPowerState_Impl(uint32_t powerFlags)
{
	IOLockLock(ivars->lock);
	bool on = powerFlags & kIOServicePowerCapabilityOn;
	if (ivars->pci && !on && !ivars->asleep) {
		uint16_t cmd = 0;
		ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetCommand, &cmd);
		ivars->pci->ConfigurationWrite16(kIOPCIConfigurationOffsetCommand, cmd & ~kIOPCICommandBusMaster);
	}
	if (ivars->pci && on && ivars->asleep) {
		uint16_t cmd = 0;
		ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetCommand, &cmd);
		ivars->pci->ConfigurationWrite16(kIOPCIConfigurationOffsetCommand, cmd | kIOPCICommandMemorySpace);
	}
	ivars->asleep = !on;
	IOLockUnlock(ivars->lock);
	os_log(OS_LOG_DEFAULT, "tinygpu: power state 0x%x", powerFlags);
	return SetPowerState(powerFlags, SUPERDISPATCH);
}

kern_return_t TinyGPUDriver::NewUserClient_Impl(uint32_t in_type, IOUserClient** out_user_client)
{
	IOService* service = nullptr;
	kern_return_t err = Create(this, "TinyGPUDriverUserClientProperties", &service);
	if (err) { os_log(OS_LOG_DEFAULT, "tinygpu: failed to create user client 0x%x", err); return err; }
	*out_user_client = OSDynamicCast(IOUserClient, service);
	return kIOReturnSuccess;
}

template <typename F> static kern_return_t WithPCI(TinyGPUDriver_IVars *iv, F f)
{
	IOLockLock(iv->lock);
	IOPCIDevice *pci = iv->asleep ? nullptr : iv->pci;
	kern_return_t ret = pci ? f(pci) : kIOReturnNotReady;
	IOLockUnlock(iv->lock);
	return ret;
}

static bool CfgArgsOK(uint32_t off, uint32_t size) { return (size == 1 || size == 2 || size == 4) && off < 4096 && off % size == 0; }

kern_return_t TinyGPUDriver::MapBar(uint32_t bar, IOMemoryDescriptor** memory)
{
	return WithPCI(ivars, [&](IOPCIDevice *pci) {
		ivars->mapped = true;
		uint8_t idx, type; uint64_t size;
		kern_return_t err = pci->GetBARInfo(bar, &idx, &size, &type);
		return err ? err : pci->_CopyDeviceMemoryWithIndex(idx, memory, this);
	});
}

kern_return_t TinyGPUDriver::SetupDMA(IOMemoryDescriptor* memory, uint64_t size, IODMACommand** outCmd,
                                      IOAddressSegment* segments, uint32_t* segCount)
{
	return WithPCI(ivars, [&](IOPCIDevice *pci) {
		ivars->mapped = true;
		IODMACommandSpecification spec = {.options = 0, .maxAddressBits = 40};
		IODMACommand* dmaCmd = nullptr;
		kern_return_t err = IODMACommand::Create(pci, kIODMACommandCreateNoOptions, &spec, &dmaCmd);
		if (err) return err;
		uint64_t flags = kIOMemoryDirectionInOut;
		err = dmaCmd->PrepareForDMA(kIODMACommandPrepareForDMANoOptions, memory, 0, size, &flags, segCount, segments);
		if (err) { os_log(OS_LOG_DEFAULT, "tinygpu: PrepareForDMA failed 0x%x", err); dmaCmd->release(); return err; }
		*outCmd = dmaCmd;
		return kIOReturnSuccess;
	});
}

kern_return_t TinyGPUDriver::CfgRead(uint32_t off, uint32_t size, uint32_t* val)
{
	if (!CfgArgsOK(off, size)) return kIOReturnBadArgument;
	return WithPCI(ivars, [&](IOPCIDevice *pci) {
		if (size == 1) { uint8_t v = 0; pci->ConfigurationRead8(off, &v); *val = v; }
		else if (size == 2) { uint16_t v = 0; pci->ConfigurationRead16(off, &v); *val = v; }
		else pci->ConfigurationRead32(off, val);
		return kIOReturnSuccess;
	});
}

kern_return_t TinyGPUDriver::CfgWrite(uint32_t off, uint32_t size, uint32_t val)
{
	if (!CfgArgsOK(off, size)) return kIOReturnBadArgument;
	return WithPCI(ivars, [&](IOPCIDevice *pci) {
		if (size == 1) pci->ConfigurationWrite8(off, (uint8_t)val);
		else if (size == 2) pci->ConfigurationWrite16(off, (uint16_t)val);
		else pci->ConfigurationWrite32(off, val);
		return kIOReturnSuccess;
	});
}

kern_return_t TinyGPUDriver::ResetDevice()
{
	return WithPCI(ivars, [&](IOPCIDevice *pci) {
		kern_return_t err = pci->Reset(kIOPCIDeviceResetTypeFunctionReset);
		return err ? pci->Reset(kIOPCIDeviceResetTypeHotReset) : err;
	});
}
