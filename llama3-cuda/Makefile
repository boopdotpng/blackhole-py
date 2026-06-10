NVCC ?= nvcc
BUILD_DIR ?= build
TARGET ?= $(BUILD_DIR)/llama3_cuda

CUDA_ARCH ?= sm_120
NVCCFLAGS ?= -O2 -std=c++17 --use_fast_math -arch=$(CUDA_ARCH)
SRC := src/main.cu src/kernels_token.cu src/kernels_gemv.cu src/kernels_attention.cu src/model_format.cpp

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRC) src/*.h src/*.cuh | $(BUILD_DIR)
	$(NVCC) $(NVCCFLAGS) $(SRC) -o $@

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)
