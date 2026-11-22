#include "TinyGPUDriverUserClient.h"
#include "TinyGPUDriver.h"
#include <DriverKit/DriverKit.h>
#include <DriverKit/OSSharedPtr.h>
#include <PCIDriverKit/PCIDriverKit.h>

#define MAX_SEGMENTS 32
#define MAX_DMAS 256

struct TinyGPUDriverUserClient_IVars
{
	OSSharedPtr<TinyGPUDriver> provider;
	IODMACommand *dmas[MAX_DMAS];
	uint32_t dmaCount;
};

bool TinyGPUDriverUserClient::init()
{
	if (!super::init()) return false;
	ivars = IONewZero(TinyGPUDriverUserClient_IVars, 1);
	return ivars != nullptr;
}

void TinyGPUDriverUserClient::free()
{
	if (ivars) ivars->provider.reset();
	IOSafeDeleteNULL(ivars, TinyGPUDriverUserClient_IVars, 1);
	super::free();
}

kern_return_t TinyGPUDriverUserClient::Start_Impl(IOService* in_provider)
{
	TinyGPUDriver *provider = OSDynamicCast(TinyGPUDriver, in_provider);
	if (!provider) return kIOReturnBadArgument;
	kern_return_t err = Start(in_provider, SUPERDISPATCH);
	if (err) return err;
	ivars->provider = OSSharedPtr(provider, OSRetain);
	return kIOReturnSuccess;
}

kern_return_t TinyGPUDriverUserClient::Stop_Impl(IOService* in_provider)
{
	for (uint32_t i = 0; i < ivars->dmaCount; i++) {
		ivars->dmas[i]->CompleteDMA(kIODMACommandCompleteDMANoOptions);
		ivars->dmas[i]->release();
		ivars->dmas[i] = nullptr;
	}
	ivars->dmaCount = 0;
	ivars->provider.reset();
	return Stop(in_provider, SUPERDISPATCH);
}

static kern_return_t DoPrepareDMA(TinyGPUDriver *provider, TinyGPUDriverUserClient_IVars *ivars, IOUserClientMethodArguments *args)
{
	if (!args->structureInputDescriptor || !args->structureOutputDescriptor) return kIOReturnBadArgument;
	if (ivars->dmaCount >= MAX_DMAS) return kIOReturnNoResources;

	uint64_t size = 0, outSize = 0;
	args->structureInputDescriptor->GetLength(&size);
	args->structureOutputDescriptor->GetLength(&outSize);
	if (outSize < (MAX_SEGMENTS + 1) * 16) return kIOReturnBadArgument;

	IODMACommand *dmaCmd = nullptr;
	IOAddressSegment segments[MAX_SEGMENTS];
	uint32_t segCount = MAX_SEGMENTS;
	kern_return_t err = provider->SetupDMA(args->structureInputDescriptor, size, &dmaCmd, segments, &segCount);
	if (err) return err;

	IOMemoryMap *map = nullptr;
	err = args->structureOutputDescriptor->CreateMapping(0, 0, 0, 0, 0, &map);
	if (err || !map) {
		dmaCmd->CompleteDMA(kIODMACommandCompleteDMANoOptions);
		dmaCmd->release();
		return err ?: kIOReturnNoMemory;
	}
	uint64_t *out = (uint64_t *)map->GetAddress();
	for (uint32_t i = 0; i < segCount; i++) { out[2 * i] = segments[i].address; out[2 * i + 1] = segments[i].length; }
	out[2 * segCount] = out[2 * segCount + 1] = 0;
	map->release();

	ivars->dmas[ivars->dmaCount++] = dmaCmd;
	return kIOReturnSuccess;
}

kern_return_t TinyGPUDriverUserClient::ExternalMethod(uint64_t selector, IOUserClientMethodArguments* args, const IOUserClientMethodDispatch* in_dispatch, OSObject* in_target, void* in_reference)
{
	TinyGPUDriver *provider = ivars->provider.get();
	if (!provider) return kIOReturnNotAttached;

	switch (selector) {
	case TinyGPURPC::ReadCfg: {
		if (args->scalarInputCount != 2 || args->scalarOutputCount < 1) return kIOReturnBadArgument;
		uint32_t val = 0;
		kern_return_t err = provider->CfgRead(uint32_t(args->scalarInput[0]), uint32_t(args->scalarInput[1]), &val);
		if (err) return err;
		args->scalarOutput[0] = val;
		args->scalarOutputCount = 1;
		return kIOReturnSuccess;
	}
	case TinyGPURPC::WriteCfg:
		if (args->scalarInputCount != 3) return kIOReturnBadArgument;
		return provider->CfgWrite(uint32_t(args->scalarInput[0]), uint32_t(args->scalarInput[1]), uint32_t(args->scalarInput[2]));
	case TinyGPURPC::Reset:
		os_log(OS_LOG_DEFAULT, "tinygpu: reset");
		return provider->ResetDevice();
	case TinyGPURPC::PrepareDMA:
		return DoPrepareDMA(provider, ivars, args);
	}
	return kIOReturnUnsupported;
}

kern_return_t IMPL(TinyGPUDriverUserClient, CopyClientMemoryForType)
{
	TinyGPUDriver *provider = ivars->provider.get();
	if (!memory) return kIOReturnBadArgument;
	if (!provider) return kIOReturnNotAttached;
	if (type >= 6) return kIOReturnUnsupported;
	return provider->MapBar(uint32_t(type), memory);
}
