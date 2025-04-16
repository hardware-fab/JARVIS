/*
 * Authors              :   Andrea Galimberti (andrea.galimberti@polimi.it),
 *                          Davide Galli (davide.galli@polimi.it),
 *                          Davide Zoni (davide.zoni@polimi.it)
 *
 * Other contributor(s) :   Andrea Motta
 * 
 * Simple linker script for the jarvis RISC-V core implementation
 */

OUTPUT_FORMAT("elf32-littleriscv", "elf32-littleriscv", "elf32-littleriscv")
OUTPUT_ARCH(riscv)
ENTRY(_start)

total_mem 		= 256K;
vector_lenght  	= 0x100;
mem_lenght		= total_mem - vector_lenght;
vector_base 	= 0x0;
mem_base 		= vector_base + vector_lenght;

MEMORY
{
    /* Memory section to accommodate the vector table */
    VECTORS (rwx) : ORIGIN = vector_base, LENGTH = vector_lenght
    /* Memory section to store program and data */
    mem (awx) : ORIGIN = mem_base, LENGTH = mem_lenght
}

__min_stack      = 0x800;   /* 2K minimum stack */

SECTIONS
{
	.init :
	{
		_text = .;
		KEEP (*(SORT_NONE(.init)))
	} >mem AT>mem
	
	.text :
	{
        . = ALIGN(4);
		*(.text.unlikely .text.unlikely.*)
		*(.text.startup .text.startup.*)
		*(.text .text.*)
		*(.gnu.linkonce.t.*)
        . = ALIGN(4);
	} >mem AT>mem

	.fini :
	{
		KEEP (*(SORT_NONE(.fini)))
		_etext = .;
	} >mem AT>mem

	.rodata.align :
	{
		. = ALIGN(4);
		_rodata = .;
	} >mem AT>mem

	.rodata.start :
	{
		_rodata_lma = LOADADDR(.rodata.start);
	} >mem AT>mem

	.rodata :
	{
		*(.rdata)
		*(.rodata .rodata.*)
		*(.gnu.linkonce.r.*)

		. = ALIGN(4);
		_erodata = .;
	} >mem AT>mem

	.data.align :
	{
		. = ALIGN(4);
		_data = .;
	} >mem AT>mem

	.data.start :
	{
		_data_lma = LOADADDR(.data.start);
	} >mem AT>mem

	.data :
	{
		*(.data .data.*)
		*(.gnu.linkonce.d.*)
		. = ALIGN(8);
		PROVIDE( __global_pointer$ = . + 0x800 );
		*(.sdata .sdata.*)
		*(.sdata2 .sdata2.*)
		*(.gnu.linkonce.s.*)
		. = ALIGN(8);
		*(.srodata.cst16)
		*(.srodata.cst8)
		*(.srodata.cst4)
		*(.srodata.cst2)
		*(.srodata .srodata.*)

		. = ALIGN(4);
		_edata = .;
	} >mem AT>mem

	.bss.align :
	{
		. = ALIGN(4);
		_bss = .;
	} >mem AT>mem

	.bss.start :
	{
		_bss_lma = LOADADDR(.bss.start);
	} >mem AT>mem

	.bss :
	{
		*(.sbss*)
		*(.gnu.linkonce.sb.*)
		*(.bss .bss.*)
		*(.gnu.linkonce.b.*)
		*(COMMON)

		. = ALIGN(4);
		_ebss = .;
	} >mem AT>mem

	. = ALIGN(8);
	_end = .;

	.stack(NOLOAD) :
	{
		. = ALIGN(16);
		. += __stack_size;
		_stack_top = .;
	} >mem AT>mem
}

