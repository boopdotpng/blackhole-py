CC = riscv64-linux-gnu-gcc
CFLAGS = -march=rv32im_zicsr -mabi=ilp32 -O2 -ffreestanding -fno-builtin -Wall -Wextra -Werror
BUILD ?= /tmp/bhp-erisc-build
all: $(BUILD)/bhp.o $(BUILD)/raw_tx.o
$(BUILD)/%.o: %.c bhp.h
	mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
.PHONY: all
