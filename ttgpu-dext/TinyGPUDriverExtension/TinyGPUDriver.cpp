#include "TinyGPUDriver.h"
#include "TinyGPUDriverUserClient.h"
#include <DriverKit/IOLib.h>
#include <PCIDriverKit/PCIDriverKit.h>

// ---- Blackhole ARC access (tt-kmd blackhole.c / msgqueue.c / tlb.c), through a 2M TLB window only the driver uses ----
#define TLB_2M_SIZE        (1ull << 21)
#define TLB_REGS           0x1FC00000u
#define TLB_REG_SIZE       12u
#define DEXT_TLB           199u          /* 201 = a process's ARC window, 200 = smi.py, 199 = this driver */
#define ARC_X              8u
#define ARC_Y              0u
#define RESET_SCRATCH(n)   (0x80030400u + 4u * (n))
#define ARC_BOOT_STATUS    RESET_SCRATCH(2)
#define ARC_MSG_QCB_PTR    RESET_SCRATCH(11)
#define ARC_MSI_FIFO       0x800B0000u
#define ARC_MSG_QUEUE_HEADER 32u
#define ARC_MSG_POWER_SETTING 0x21u
#define TT_POWER_VALIDITY  15u           /* 15 flags valid, 0 settings: what tt-kmd sends after aggregating */
#define TT_POWER_FLAG_ALL  0x7FFFu
#define MAX_VOTERS         32

struct PowerVoteEntry { void *client; uint16_t flags; };

struct TinyGPUDriver_IVars
{
	IOPCIDevice *pci = nullptr;
	uint8_t bar0Index = 0;
	bool bar0Valid = false;
	uint64_t arcBase = ~0ull;            /* NoC base the driver TLB currently points at */
	IOLock *arcLock = nullptr;
	PowerVoteEntry votes[MAX_VOTERS] = {};
};

bool TinyGPUDriver::init()
{
	os_log(OS_LOG_DEFAULT, "tinygpu: init");

	auto answer = super::init();
	if (!answer) {
		return false;
	}

	ivars = new TinyGPUDriver_IVars();
	if (ivars == nullptr) {
		return false;
	}
	ivars->arcLock = IOLockAlloc();
	if (ivars->arcLock == nullptr) {
		return false;
	}

	return true;
}

void TinyGPUDriver::free()
{
	if (ivars && ivars->arcLock) { IOLockFree(ivars->arcLock); ivars->arcLock = nullptr; }
	IOSafeDeleteNULL(ivars, TinyGPUDriver_IVars, 1);
	super::free();
}

kern_return_t TinyGPUDriver::Start_Impl(IOService* in_provider)
{
	IOServiceName service_name;
	os_log(OS_LOG_DEFAULT, "tinygpu: on gpu detected");

	kern_return_t err = Start(in_provider, SUPERDISPATCH);
	if (err) return err;

	ivars->pci = OSDynamicCast(IOPCIDevice, in_provider);
	if (!ivars->pci) return kIOReturnNoDevice;

	err = ivars->pci->Open(this, 0);
	if (err) {
		os_log(OS_LOG_DEFAULT, "tinygpu: Open() failed 0x%08x", err);
		ivars->pci = nullptr;
		return err;
	}

	uint16_t ven = 0, dev = 0;
	ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetVendorID, &ven);
	ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetDeviceID, &dev);
	os_log(OS_LOG_DEFAULT, "tinygpu: opened device ven=0x%04x dev=0x%04x", ven, dev);

	uint16_t commandRegister;
	ivars->pci->ConfigurationRead16(kIOPCIConfigurationOffsetCommand, &commandRegister);
	commandRegister |= (kIOPCICommandIOSpace | kIOPCICommandBusMaster | kIOPCICommandMemorySpace);
	ivars->pci->ConfigurationWrite16(kIOPCIConfigurationOffsetCommand, commandRegister);

	{
		uint8_t barType; uint64_t barSize;
		ivars->bar0Valid = ivars->pci->GetBARInfo(0, &ivars->bar0Index, &barSize, &barType) == kIOReturnSuccess
		                   && barSize >= TLB_REGS + 0x1000;
		if (!ivars->bar0Valid) os_log(OS_LOG_DEFAULT, "tinygpu: BAR0 too small for ARC access");
	}

	memcpy((void*)service_name, (void*)"ttgpu\0", 6);
	SetName(service_name);

	os_log(OS_LOG_DEFAULT, "tinygpu: will register service %s", service_name);
	RegisterService();

	os_log(OS_LOG_DEFAULT, "tinygpu: service started %s", service_name);
	return 0;
}

kern_return_t TinyGPUDriver::Stop_Impl(IOService* in_provider)
{
	ivars->pci->Close(this, 0);
	return 0;
}

kern_return_t TinyGPUDriver::NewUserClient_Impl(uint32_t in_type, IOUserClient** out_user_client)
{
	kern_return_t err = 0;

	IOService* user_client_service = nullptr;
	err = Create(this, "TinyGPUDriverUserClientProperties", &user_client_service);
	if (err) {
		os_log(OS_LOG_DEFAULT, "tinygpu: failed to create NewUserClient");
		goto error;
	}
	*out_user_client = OSDynamicCast(IOUserClient, user_client_service);
	os_log(OS_LOG_DEFAULT, "tinygpu: NewUserClient created");

error:
	return err;
}

kern_return_t TinyGPUDriver::MapBar(uint32_t bar, IOMemoryDescriptor** memory)
{
	uint8_t barMemoryIndex, barMemoryType;
	uint64_t barMemorySize;
	kern_return_t err = ivars->pci->GetBARInfo(bar, &barMemoryIndex, &barMemorySize, &barMemoryType);
	if (err) return err;
	os_log(OS_LOG_DEFAULT, "tinygpu: bar mapping %d idx=%d", bar, barMemoryIndex);
	return ivars->pci->_CopyDeviceMemoryWithIndex(barMemoryIndex, memory, this);
}

static kern_return_t WriteDMASegments(IOMemoryDescriptor* mem, IOAddressSegment* segments, uint32_t segCount,
                                      uint64_t mapOffset = 0, uint64_t mapSize = 0)
{
	// write dma segments to mapped memory as [addr0, len0, addr1, len1, ..., 0, 0]

	IOMemoryMap* map = nullptr;
	kern_return_t err = mem->CreateMapping(0, 0, 0, mapOffset, mapSize, &map);
	if (err || !map) return err ?: kIOReturnError;

	uint64_t* out = (uint64_t*)map->GetAddress();
	for (uint32_t i = 0; i < segCount; i++) { out[i * 2] = segments[i].address; out[i * 2 + 1] = segments[i].length; }
	out[segCount * 2] = 0; out[segCount * 2 + 1] = 0;
	map->release();
	return 0;
}

kern_return_t TinyGPUDriver::SetupDMA(IOMemoryDescriptor* memory, uint64_t size, IODMACommand** outCmd,
                                       IOAddressSegment* segments, uint32_t* segCount)
{
	IODMACommandSpecification dmaSpec = {.options = 0, .maxAddressBits = 40};
	IODMACommand* dmaCmd = nullptr;

	kern_return_t err = IODMACommand::Create(ivars->pci, kIODMACommandCreateNoOptions, &dmaSpec, &dmaCmd);
	if (err) { os_log(OS_LOG_DEFAULT, "tinygpu: DMA create failed err=%d", err); return err; }

	uint64_t flags = kIOMemoryDirectionInOut;
	err = dmaCmd->PrepareForDMA(kIODMACommandPrepareForDMANoOptions, memory, 0, size, &flags, segCount, segments);
	if (err) { os_log(OS_LOG_DEFAULT, "tinygpu: PrepareForDMA failed err=%d", err); dmaCmd->release(); return err; }

	*outCmd = dmaCmd;
	return 0;
}

kern_return_t TinyGPUDriver::CreateDMA(size_t size, TinyGPUCreateDMAResp* dmaDesc)
{
	IOBufferMemoryDescriptor* sharedBuf = nullptr;
	kern_return_t err = IOBufferMemoryDescriptor::Create(kIOMemoryDirectionInOut, size, IOVMPageSize, &sharedBuf);
	if (err) { os_log(OS_LOG_DEFAULT, "tinygpu: alloc failed err=%d", err); return err; }

	IODMACommand* dmaCmd = nullptr;
	IOAddressSegment segments[32];
	uint32_t segCount = 32;
	err = SetupDMA(sharedBuf, size, &dmaCmd, segments, &segCount);
	if (err) { sharedBuf->release(); return err; }

	err = WriteDMASegments(sharedBuf, segments, segCount, IOVMPageSize, IOVMPageSize);
	if (err) { dmaCmd->CompleteDMA(kIODMACommandCompleteDMANoOptions); dmaCmd->release(); sharedBuf->release(); return err; }

	dmaDesc->sharedBuf = sharedBuf;
	dmaDesc->dmaCmd = dmaCmd;
	os_log(OS_LOG_DEFAULT, "tinygpu: CreateDMA size=0x%zx segs=%u", size, segCount);
	return 0;
}

kern_return_t TinyGPUDriver::CfgRead(uint32_t off, uint32_t size, uint32_t* outVal)
{
  if (!ivars->pci || !outVal) return kIOReturnNotReady;

  if (size == 1) {
	uint8_t v8 = 0;
	ivars->pci->ConfigurationRead8(off, &v8);
	*outVal = v8;
  } else if (size == 2) {
	uint16_t v16 = 0;
	ivars->pci->ConfigurationRead16(off, &v16);
	*outVal = v16;
  } else if (size == 4) {
	uint32_t v32 = 0;
	ivars->pci->ConfigurationRead32(off, &v32);
	*outVal = v32;
  }
  return 0;
}

kern_return_t TinyGPUDriver::CfgWrite(uint32_t off, uint32_t size, uint32_t val)
{
  if (!ivars->pci) return kIOReturnNotReady;
  if (size == 1) ivars->pci->ConfigurationWrite8 (off, (uint8_t)val);
  else if (size == 2) ivars->pci->ConfigurationWrite16(off, (uint16_t)val);
  else if (size == 4) ivars->pci->ConfigurationWrite32(off, (uint32_t)val);
  return 0;
}

kern_return_t TinyGPUDriver::ResetDevice()
{
	if (!ivars->pci) return kIOReturnNotReady;
	kern_return_t ret = ivars->pci->Reset(kIOPCIDeviceResetTypeFunctionReset);
	return ret == kIOReturnSuccess ? ret : ivars->pci->Reset(kIOPCIDeviceResetTypeHotReset);
}

IOPCIDevice* TinyGPUDriver::GetPCI()
{
	return ivars->pci;
}

// ---- ARC ----

static uint32_t TlbWord(unsigned __int128 v, int i) { return (uint32_t)(v >> (32 * i)); }

void TinyGPUDriver::ArcWrite32(uint32_t addr, uint32_t value)
{
	uint64_t base = addr & ~(TLB_2M_SIZE - 1);
	if (ivars->arcBase != base) {
		/* TLB_2M_REG: local offset, x_end, y_end, x_start, y_start, noc, multicast, ordering (strict) */
		unsigned __int128 v = (unsigned __int128)(base >> 21) | (unsigned __int128)ARC_X << 43 | (unsigned __int128)ARC_Y << 49
		                    | (unsigned __int128)ARC_X << 55 | (unsigned __int128)ARC_Y << 61 | (unsigned __int128)1 << 70;
		uint64_t reg = TLB_REGS + DEXT_TLB * TLB_REG_SIZE;
		for (int i = 0; i < 3; i++) ivars->pci->MemoryWrite32(ivars->bar0Index, reg + 4 * i, TlbWord(v, i));
		ivars->arcBase = base;
	}
	ivars->pci->MemoryWrite32(ivars->bar0Index, DEXT_TLB * TLB_2M_SIZE + (addr - base), value);
}

kern_return_t TinyGPUDriver::ArcRead32(uint32_t addr, uint32_t* value)
{
	uint64_t base = addr & ~(TLB_2M_SIZE - 1);
	if (ivars->arcBase != base) {
		unsigned __int128 v = (unsigned __int128)(base >> 21) | (unsigned __int128)ARC_X << 43 | (unsigned __int128)ARC_Y << 49
		                    | (unsigned __int128)ARC_X << 55 | (unsigned __int128)ARC_Y << 61 | (unsigned __int128)1 << 70;
		uint64_t reg = TLB_REGS + DEXT_TLB * TLB_REG_SIZE;
		for (int i = 0; i < 3; i++) ivars->pci->MemoryWrite32(ivars->bar0Index, reg + 4 * i, TlbWord(v, i));
		ivars->arcBase = base;
	}
	ivars->pci->MemoryRead32(ivars->bar0Index, DEXT_TLB * TLB_2M_SIZE + (addr - base), value);
	return *value == 0xFFFFFFFFu ? kIOReturnNotResponding : kIOReturnSuccess;  /* NoC hung or device gone */
}

/* tt-kmd arc_msg_send_sync: drain stale responses, push one 8-word request, trigger, pop the response. Caller holds arcLock. */
kern_return_t TinyGPUDriver::ArcMsgLocked(const uint32_t* request, uint32_t* response)
{
	if (!ivars->pci || !ivars->bar0Valid) return kIOReturnNotReady;
	ivars->arcBase = ~0ull;  /* the card may have been reset since: always rewrite the TLB once */
	kern_return_t err;
	uint32_t v = 0;
	for (int ms = 0;; ms++) {  /* ARC_BOOT_STATUS_READY_FOR_MSG */
		if ((err = ArcRead32(ARC_BOOT_STATUS, &v))) return err;
		if (v & 1) break;
		if (ms >= 500) return kIOReturnNotReady;
		IOSleep(1);
	}
	uint32_t qcb, q, entries;
	if ((err = ArcRead32(ARC_MSG_QCB_PTR, &qcb)) || (err = ArcRead32(qcb, &q)) || (err = ArcRead32(qcb + 4, &entries))) return err;
	entries &= 0xFF;
	if (entries == 0) return kIOReturnError;
	uint32_t wrap = 2 * entries, responses = q + ARC_MSG_QUEUE_HEADER + entries * 32;

	auto pop = [&](uint32_t* out) -> int {  /* 1 = popped, 0 = empty, <0 = read error */
		uint32_t rptr, wptr;
		if (ArcRead32(q + 0x04, &rptr) || ArcRead32(q + 0x14, &wptr)) return -1;
		if ((wptr + wrap - rptr) % wrap == 0) return 0;
		uint32_t slot = responses + (rptr % entries) * 32;
		for (int i = 0; i < 8; i++) if (ArcRead32(slot + 4 * i, &out[i])) return -1;
		ArcWrite32(q + 0x04, (rptr + 1) % wrap);
		return 1;
	};
	uint32_t stale[8];
	for (uint32_t i = 0; i < entries; i++) { int r = pop(stale); if (r < 0) return kIOReturnNotResponding; if (r == 0) break; }

	uint32_t wptr, rptr;
	if ((err = ArcRead32(q + 0x00, &wptr)) || (err = ArcRead32(q + 0x10, &rptr))) return err;
	if ((wptr + wrap - rptr) % wrap >= entries) return kIOReturnBusy;  /* request queue full */
	uint32_t slot = q + ARC_MSG_QUEUE_HEADER + (wptr % entries) * 32;
	for (int i = 0; i < 8; i++) ArcWrite32(slot + 4 * i, request[i]);
	ArcWrite32(q + 0x00, (wptr + 1) % wrap);
	ArcWrite32(ARC_MSI_FIFO, 0);  /* blackhole_arc_msg_trigger */

	for (int us = 0;; us += 100) {
		int r = pop(response);
		if (r < 0) return kIOReturnNotResponding;
		if (r > 0) break;
		if (us >= 1000000) {
			os_log(OS_LOG_DEFAULT, "tinygpu: ARC message 0x%x timed out", request[0] & 0xFF);
			return kIOReturnTimeout;
		}
		IODelay(100);
	}
	return kIOReturnSuccess;
}

kern_return_t TinyGPUDriver::ArcMsg(const uint32_t* request, uint32_t* response)
{
	IOLockLock(ivars->arcLock);
	kern_return_t err = ArcMsgLocked(request, response);
	IOLockUnlock(ivars->arcLock);
	return err;
}

kern_return_t TinyGPUDriver::PowerVote(void* client, int32_t flags, uint32_t* response)
{
	IOLockLock(ivars->arcLock);
	int slot = -1;
	for (int i = 0; i < MAX_VOTERS; i++) if (ivars->votes[i].client == client) { slot = i; break; }
	if (flags < 0) {
		if (slot >= 0) ivars->votes[slot] = {};
	} else {
		if (slot < 0) for (int i = 0; i < MAX_VOTERS; i++) if (!ivars->votes[i].client) { slot = i; break; }
		if (slot < 0) { IOLockUnlock(ivars->arcLock); return kIOReturnNoResources; }
		ivars->votes[slot] = { client, (uint16_t)(flags & TT_POWER_FLAG_ALL) };
	}
	uint32_t aggregate = 0, voters = 0;
	for (int i = 0; i < MAX_VOTERS; i++) if (ivars->votes[i].client) { aggregate |= ivars->votes[i].flags; voters++; }
	uint32_t request[8] = { ARC_MSG_POWER_SETTING | TT_POWER_VALIDITY << 8 | aggregate << 16 }, scratch[8];
	kern_return_t err = ArcMsgLocked(request, response ? response : scratch);
	IOLockUnlock(ivars->arcLock);
	os_log(OS_LOG_DEFAULT, "tinygpu: power vote %d -> aggregate 0x%x over %u client(s): 0x%x", flags, aggregate, voters, err);
	return err;
}
