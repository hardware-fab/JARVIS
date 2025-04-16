################################################
# Authors             : Andrea Galimberti (andrea.galimberti@polimi.it),
#                       Davide Galli (davide.galli@polimi.it),
#                       Davide Zoni (davide.zoni@polimi.it)
#
# Other contributor(s): Andrea Motta
################################################

cd ../RTOS/demo/chaffing
make -j16 DEBUG=1
cd ../../../compile_scripts

RTOS_DIR="../RTOS/"
OUT_BENCH_VMEM="${RTOS_DIR}demo/out/"
BENCH_NAME="RTOSDemo.axf"
BENCH_FOLDER="build/"
CC_STRIP="riscv32-unknown-elf-strip"
CC_OBJCOPY="riscv32-unknown-elf-objcopy"
CC_OBJDUMP="riscv32-unknown-elf-objdump"

# objdump
    ${CC_OBJDUMP} -d ${RTOS_DIR}${BENCH_FOLDER}${BENCH_NAME} > ${OUT_BENCH_VMEM}${BENCH_NAME}.objdump

# Remove debug section
    ${CC_STRIP} --strip-all -o ${OUT_BENCH_VMEM}${BENCH_NAME}_strpd.elf ${RTOS_DIR}${BENCH_FOLDER}${BENCH_NAME}

# Produce temporary vmem file from object file with reversed bytes within the word
    echo "Generating .vmem file ..."
    ${CC_OBJCOPY} ${OUT_BENCH_VMEM}${BENCH_NAME}_strpd.elf ${OUT_BENCH_VMEM}${BENCH_NAME}.vmem.tmp -O verilog \
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