/*
 * Authors              :   Andrea Galimberti (andrea.galimberti@polimi.it),
 *                          Davide Galli (davide.galli@polimi.it),
 *                          Davide Zoni (davide.zoni@polimi.it)
 *
 * Other contributor(s) :   Andrea Motta
 * 
 * Simple linker script for the jarvis RISC-V core implementation
 * 
 * SUPPORTS:
 * -> bare metal applications 
 * -> single stack pointer
 */


OUTPUT_FORMAT("elf32-littleriscv", "elf32-littleriscv", "elf32-littleriscv")
OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY
{
    /* Memory section to accommodate the vector table */
    VECTORS (rwx) : ORIGIN = 0,     LENGTH = 0x100
    /* Memory section to store program and data */
    MEM     (rwx) : ORIGIN = 0x100, LENGTH = (64K - 0x100)
}

__stack_pointer$ = 64*1024;
__min_stack      = 0x800;   /* 2K minimum stack */

SECTIONS
{
	
	.init		: { *(.init) } > MEM

	.text		:
    {
        *(.text)
        *(.text.*)
    } > MEM
	__etext = .;

	.fini		: { KEEP (*(SORT_NONE(.fini))) } > MEM

  	. = . + ALIGN(32 / 8);

	__global_pointer$ = . + 0x800;

	/* data: Initialized data segment */
    .data :
    {
        . = ALIGN(4);
        __data_start = .;
        *(.rodata)
        *(.rodata.*)
        *(.data)
        *(.data.*)
		*(.sdata)
        *(.sdata.*)
        . = ALIGN(4);
        __data_end = .;
    } > MEM

    .bss :
    {
        . = ALIGN(4);
        __bss_start = .;
        *(.bss)
        *(.bss.*)
        *(.sbss)
        *(.sbss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > MEM


    /* Make sure there is enough room for the stack */
    .stack (NOLOAD): {
        . = ALIGN(4);
        . = . + __min_stack;
        . = ALIGN(4);
    } > MEM

}
