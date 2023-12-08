/* AmpliPi Preamp STM32F030R8 linker script. */

min_stack_size = 4K; /* Bytes of stack to reserve. */

MEMORY
{
  rom (rx)  : ORIGIN = 0x08000000, LENGTH = 64k
  ram (rwx) : ORIGIN = 0x20000000, LENGTH = 8K
}

__stack_start__ = ORIGIN(ram) + LENGTH(ram); /* Stack is descending, start at the end of ram */

SECTIONS
{
  .isr_vector :
  { /* The vector table in ROM */
    . = ALIGN(4);
    KEEP(*(.isr_vector))
    . = ALIGN(4);
  } >rom

  .text :
  { /* The program code and other data in ROM */
    . = ALIGN(4);
    *(.text) *(.text.*)
    KEEP(*(.init))
    KEEP(*(.fini))
    . = ALIGN(4);
  } >rom

  .rodata :
  { /* Constant data in ROM */
    . = ALIGN(4);
    *(.rodata) *(.rodata.*)
    . = ALIGN(4);
  } >rom

  .preinit_array :
  {
    . = ALIGN(4);
    PROVIDE_HIDDEN (__preinit_array_start = .);
    KEEP(*(.preinit_array*))
    PROVIDE_HIDDEN (__preinit_array_end = .);
    . = ALIGN(4);
  } >rom

  .init_array :
  {
    . = ALIGN(4);
    PROVIDE_HIDDEN (__init_array_start = .);
    KEEP(*(SORT(.init_array.*)))
    KEEP(*(.init_array*))
    PROVIDE_HIDDEN (__init_array_end = .);
    . = ALIGN(4);
  } >rom

  .fini_array :
  {
    . = ALIGN(4);
    PROVIDE_HIDDEN (__fini_array_start = .);
    KEEP(*(SORT(.fini_array.*)))
    KEEP(*(.fini_array*))
    PROVIDE_HIDDEN (__fini_array_end = .);
    . = ALIGN(4);
  } >rom

  __data_init_start__ = LOADADDR(.data); /* Start address of initial data in ROM. */

  .data :
  { /* Initialized data in RAM (moved from ROM) */
    . = ALIGN(4);
    __data_start__ = .; /* Start address of data in RAM. */
    *(.data) *(.data.*)
    . = ALIGN(4);
    __data_end__ = .;
  } >ram AT>rom         /* Space allocated in RAM, but loaded from ROM. */


  .bss :
  { /* Uninitialized data in RAM */
    . = ALIGN(4);
    __bss_start__ = .; /* Used by startup to zero out the bss section */
    *(.bss) *(.bss.*)
    *(COMMON)
    . = ALIGN(4);
    __bss_end__ = .;
  } >ram

  .stack :
  { /* Nothing is placed here, but an error is produced if not enough RAM is left for the stack. */
    . = ALIGN(8);
    PROVIDE ( end = . ); /* Start of heap. Unused. TODO: redefine _sbrk to not need this. */
    . = . + min_stack_size;
    . = ALIGN(8);
  } >ram
}
