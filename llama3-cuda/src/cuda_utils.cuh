#pragma once

#include <cuda_runtime.h>

#include <stdexcept>
#include <string>

#define CUDA_CHECK(call)                                                      \
    do {                                                                      \
        cudaError_t err__ = (call);                                           \
        if (err__ != cudaSuccess) {                                           \
            throw std::runtime_error(std::string("CUDA error: ") +           \
                                     cudaGetErrorString(err__));              \
        }                                                                     \
    } while (0)

