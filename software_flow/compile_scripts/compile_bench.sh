################################################
# Authors  :   Andrea Galimberti (andrea.galimberti@polimi.it),
#              Davide Galli (davide.galli@polimi.it),
#              Davide Zoni (davide.zoni@polimi.it)
################################################

#!/bin/bash

BENCH_NAME=$1
BENCH_DIR="../bench"
SRCS="${BENCH_DIR}/${BENCH_NAME}.c"
LOW_LEVEL_DIR="../low_level/"
HDRS_DRIVER_DIR="../drivers"
SRCS_DRIVER_C="./${HDRS_DRIVER_DIR}/*.c"
SRCS_DRIVER_S="./${HDRS_DRIVER_DIR}/*.S"
OUT_BENCH_VMEM="./${BENCH_DIR}/out/"
HARD_FLOAT_NO_FMA="-march=rv32imf -mabi=ilp32f -ffp-contract=off"
SOFT_FLOAT="-march=rv32im -mabi=ilp32 -lm -lgcc"

CC=riscv32-unknown-elf-gcc
CC_STRIP=riscv32-unknown-elf-strip
CC_OBJDUMP=riscv32-unknown-elf-objdump
CC_OBJCOPY=riscv32-unknown-elf-objcopy
# Default optimization level
OPTIMIZATION_LEVEL=-Os
# Remove any optimization
#OPTIMIZATION_LEVEL=-O0

# Check $1
if [ $# = 1 ]; then

    # Compile C source file
    echo "Compiling bench: $BENCH_NedAME (source files $SRCS) ..."

    # Compile with custom startup files (crt0.S)
    ${CC} ${HARD_FLOAT_NO_FMA} -Waggressive-loop-optimizations $OPTIMIZATION_LEVEL \
        -fdata-sections -ffunction-sections \
        -I $HDRS_DRIVER_DIR \
        -I ${BENCH_DIR} \
        -o ${OUT_BENCH_VMEM}${BENCH_NAME}.elf \
        $SRCS $SRCS_DRIVER_S $SRCS_DRIVER_C \
        -Wl,--gc-sections \
        -T ./$LOW_LEVEL_DIR/riscv32_mod.ld \
        -nostartfiles ./$LOW_LEVEL_DIR/crt0.S

    # Remove debug section
    ${CC_STRIP} --strip-all -o ${OUT_BENCH_VMEM}${BENCH_NAME}_strpd.elf ${OUT_BENCH_VMEM}${BENCH_NAME}.elf

    # objdump
    ${CC_OBJDUMP} -D ${OUT_BENCH_VMEM}${BENCH_NAME}.elf > ${OUT_BENCH_VMEM}${BENCH_NAME}.objdump

    # Produce temporary vmem file from object file with reversed bytes within the word
    echo "Generating .vmem file ..."
    ${CC_OBJCOPY} ${OUT_BENCH_VMEM}${BENCH_NAME}_strpd.elf ${OUT_BENCH_VMEM}${BENCH_NAME}.vmem.tmp -O verilog\
        --remove-section=.comment \
        --remove-section=.sdata \
        --remove-section=.riscv.attributes \
        --reverse-bytes=4
    
    # Format .vmem file to be compliant with polimi riscv core requirements
    echo "Formatting .vmem file ..."
    if [ -f vmem_formatter ]; then
        ./vmem_formatter ${OUT_BENCH_VMEM}${BENCH_NAME}.vmem.tmp ${OUT_BENCH_VMEM}${BENCH_NAME}.vmem
    else
        echo "[ERROR] vmem_formatter not found. Place it in the current working directory."
        exit 1;
    fi

    echo "Removing temporary files ..."
    rm ${OUT_BENCH_VMEM}${BENCH_NAME}.vmem.tmp

    echo "Done."

else
    echo "Insufficient arguments!"
    echo "Usage: $0 <src_file>"
fi
