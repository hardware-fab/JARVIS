################################################
# Authors              :   Andrea Galimberti (andrea.galimberti@polimi.it),
#                          Davide Galli (davide.galli@polimi.it),
#                          Davide Zoni (davide.zoni@polimi.it)
#              
# Other contributor(s) :   Andrea Motta
################################################

OUT =	RTOSDemo

CROSS   = riscv32-unknown-elf-
CC      = $(CROSS)gcc
OBJCOPY = $(CROSS)objcopy
ARCH    = $(CROSS)ar

BUILD_DIR       = $(abspath ../../build)
RTOS_SOURCE_DIR = $(abspath ../../FreeRTOS-Kernel)
BENCH_SOURCE_DIR = $(abspath ../../../bench)
DRIVERS_DIR = $(abspath ../../../drivers)
LOWLEVEL_DIR = $(abspath ../../../low_level)

MACHINEFLAGS = -march=rv32imf -mabi=ilp32f -ffp-contract=off

CPPFLAGS = \
	-I . \
	-I $(RTOS_SOURCE_DIR)/include \
	-I $(BENCH_SOURCE_DIR) \
	-I $(DRIVERS_DIR) \
	-I $(RTOS_SOURCE_DIR)/portable/GCC/RISC-V \
	-I $(RTOS_SOURCE_DIR)/portable/GCC/RISC-V/chip_specific_extensions/RISCV_MTIME_CLINT_no_extensions \

CFLAGS = $(MACHINEFLAGS)\
	-Wall \
	-fmessage-length=0 \
	-Os \
	-ffunction-sections \
	-fdata-sections \
	-fno-builtin-printf

ASFLAGS = $(MACHINEFLAGS)
LDFLAGS = -nostartfiles -Wl,--gc-sections -T $(LOWLEVEL_DIR)/riscv32_mod_pre.ld\
	-Xlinker --defsym=__stack_size=4096

ifeq ($(DEBUG), 1)
    CFLAGS += -g3 -ggdb3
endif

CFLAGS += -D CPU_ID=$(CPU_ID)
OUT = RTOSDemo

SRCS = main.c chaff_masked.c riscv-virt.c \
	$(RTOS_SOURCE_DIR)/event_groups.c \
	$(RTOS_SOURCE_DIR)/list.c \
	$(RTOS_SOURCE_DIR)/queue.c \
	$(RTOS_SOURCE_DIR)/stream_buffer.c \
	$(RTOS_SOURCE_DIR)/tasks.c \
	$(RTOS_SOURCE_DIR)/timers.c \
	$(RTOS_SOURCE_DIR)/portable/MemMang/heap_4.c \
	$(RTOS_SOURCE_DIR)/portable/GCC/RISC-V/port.c \
	$(BENCH_SOURCE_DIR)/aes_masked_RTOS.c \
	$(DRIVERS_DIR)/trng.c \
	$(DRIVERS_DIR)/uart.c 

ASMS = start.S vector.S \
	$(RTOS_SOURCE_DIR)/portable/GCC/RISC-V/portASM.S

OBJS = $(SRCS:%.c=$(BUILD_DIR)/%.o) $(ASMS:%.S=$(BUILD_DIR)/%.o)
DEPS = $(SRCS:%.c=$(BUILD_DIR)/%.d) $(ASMS:%.S=$(BUILD_DIR)/%.d)

$(BUILD_DIR)/$(OUT).axf: $(OBJS) $(LOWLEVEL_DIR)/riscv32_mod_pre.ld Makefile
	rm $(LOWLEVEL_DIR)/riscv32_mod_pre.ld
	$(CC) -E -P -x c $(CPPFLAGS) $(CFLAGS) $(LOWLEVEL_DIR)/riscv32_mod_RTOS.ld >> $(LOWLEVEL_DIR)/riscv32_mod_pre.ld
	$(CC) $(LDFLAGS) $(OBJS) -o $@

$(BUILD_DIR)/%.o: %.c Makefile
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

$(BUILD_DIR)/%.o: %.S Makefile
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(ASFLAGS) -MMD -MP -c $< -o $@

clean:
	rm -rf $(BUILD_DIR)

-include $(DEPS)
