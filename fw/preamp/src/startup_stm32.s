/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
/* Modified from the example at
 * https://github.com/lab11/stm32f0-hal-base/blob/master/sdk/STM32Cube_FW_F0_V1.5.0/Drivers/CMSIS/Device/ST/STM32F0xx/Source/Templates/gcc/startup_stm32f030x8.s
 *
 * Also see the STM32F030 reference manual 'Table 32. Vector table'
 */

  .syntax unified
  .cpu cortex-m0
  .fpu softvfp
  .thumb

.global  g_pfnVectors
.global  default_irq_handler

// Start address for the initialization values of the .data section. Defined in linker script.
.word  _sidata
// Start address for the .data section. Defined in linker script.
.word  _sdata
// End address for the .data section. Defined in linker script.
.word  _edata
// Start address for the .bss section. Defined in linker script.
.word  _sbss
// End address for the .bss section. Defined in linker script.
.word  _ebss


  .section  .text.reset_irq_handler
  .weak  reset_irq_handler
  .type  reset_irq_handler, %function

reset_irq_handler:
  movs  r1, #0
  b     LoopCopyDataInit  // Copy the data segment initializers from flash to SRAM.

CopyDataInit:
  ldr   r3, =_sidata
  ldr   r3, [r3, r1]
  str   r3, [r0, r1]
  adds  r1, r1, #4

LoopCopyDataInit:
  ldr   r0, =_sdata
  ldr   r3, =_edata
  adds  r2, r0, r1
  cmp   r2, r3
  bcc   CopyDataInit
  ldr   r2, =_sbss
  b     LoopFillZerobss   // Zero fill the bss segment.


FillZerobss:
  movs  r3, #0
  str   r3, [r2]
  adds  r2, r2, #4

LoopFillZerobss:
  ldr  r3, = _ebss
  cmp  r2, r3
  bcc  FillZerobss

  bl  __libc_init_array   // Call static constructors
  bl  main                // Call the application's entry point

  .size  reset_irq_handler, . - reset_irq_handler

// This is the code that gets called when the processor receives an unexpected interrupt.
// This simply enters an infinite loop, preserving the system state for examination by a debugger.
  .section  .text.default_irq_handler,"ax",%progbits
default_irq_handler:
infinite_loop:
  b  infinite_loop
  .size  default_irq_handler, . - default_irq_handler

// The minimal vector table for a Cortex-M. Note that the proper constructs must be
// placed on this to ensure that it ends up at physical address 0x0000_0000.
  .section  .isr_vector,"a",%progbits
  .type     g_pfnVectors, %object
  .size     g_pfnVectors, . - g_pfnVectors

g_pfnVectors:
  .word  _estack                        // 0x00 Stack Pointer
  .word  reset_irq_handler              // 0x04 Reset
  .word  default_irq_handler            // 0x08 Non maskable interrupt
  .word  default_irq_handler            // 0x0C All class of fault
  .word  0                              // 0x10 Reserved
  .word  0                              // 0x14 Reserved
  .word  0                              // 0x18 Reserved
  .word  0                              // 0x1C Reserved
  .word  0                              // 0x20 Reserved
  .word  0                              // 0x24 Reserved
  .word  0                              // 0x28 Reserved
  .word  default_irq_handler            // 0x2C System service call via SWI
  .word  0                              // 0x30 Reserved
  .word  0                              // 0x34 Reserved
  .word  default_irq_handler            // 0x38 Pendable request for service
  .word  systick_irq_handler            // 0x3C System tick timer
// ^ Above are the 16 M0 exceptions ^...v Below are the 32 STM32 IRQ lines v
  .word  default_irq_handler            // 0x40 Window WatchDog Early Wakeup Interrupt
  .word  0                              // 0x44 Reserved
  .word  default_irq_handler            // 0x48 RTC through the EXTI line
  .word  default_irq_handler            // 0x4C Flash
  .word  default_irq_handler            // 0x50 RCC
  .word  default_irq_handler            // 0x54 EXTI Line[1:0]
  .word  default_irq_handler            // 0x58 EXTI Line[3:2]
  .word  default_irq_handler            // 0x5C EXTI Line[15:4]
  .word  0                              // 0x60 Reserved
  .word  default_irq_handler            // 0x64 DMA1 channel 1
  .word  default_irq_handler            // 0x68 DMA1 channel 2 and channel 3
  .word  default_irq_handler            // 0x6C DMA1 channel 4 and channel 5
  .word  default_irq_handler            // 0x70 ADC
  .word  default_irq_handler            // 0x74 TIM1 Break, Update, Trigger and Commutation
  .word  default_irq_handler            // 0x78 TIM1 Capture Compare
  .word  0                              // 0x7C Reserved
  .word  default_irq_handler            // 0x80 TIM3
  .word  default_irq_handler            // 0x84 TIM6
  .word  0                              // 0x88 Reserved
  .word  default_irq_handler            // 0x8C TIM14
  .word  default_irq_handler            // 0x90 TIM15
  .word  default_irq_handler            // 0x94 TIM16
  .word  default_irq_handler            // 0x98 TIM17
  .word  default_irq_handler            // 0x9C I2C1
  .word  default_irq_handler            // 0xA0 I2C2
  .word  default_irq_handler            // 0xA4 SPI1
  .word  default_irq_handler            // 0xA8 SPI2
  .word  usart1_irq_handler             // 0xAC USART1
  .word  usart2_irq_handler             // 0xB0 USART2
  .word  0                              // 0xB4 USART 3, 4, 5, and 6
  .word  0                              // 0xB8 Reserved
  .word  0                              // 0xBC USB

// Provide weak aliases for each Exception handler to the default_irq_handler.
// As they are weak aliases, any function with the same name will override this definition.
  .weak       systick_irq_handler
  .thumb_set  systick_irq_handler, default_irq_handler

  .weak       usart1_irq_handler
  .thumb_set  usart1_irq_handler, default_irq_handler

  .weak       usart2_irq_handler
  .thumb_set  usart2_irq_handler, default_irq_handler
