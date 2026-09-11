CC = riscv64-linux-gnu-gcc
OBJCOPY = riscv64-linux-gnu-objcopy
CFLAGS = -march=rv32im_zicsr -mabi=ilp32 -O2 -ffreestanding -fno-builtin -fno-stack-protector -fno-pic -msmall-data-limit=0 -Wall -Wextra -Werror
BUILD = build
all: $(BUILD)/transfer.bin $(BUILD)/collective.bin
$(BUILD)/%.elf: %.c start.S link.ld
	mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -nostdlib -Wl,--no-relax,-T,link.ld start.S $< -o $@
$(BUILD)/%.bin: $(BUILD)/%.elf
	$(OBJCOPY) -O binary $< $@
.PHONY: all
