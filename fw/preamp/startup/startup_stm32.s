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
.global  Default_Handler

/* start address for the initialization values of the .data section.
defined in linker script */
.word  _sidata
/* start address for the .data section. defined in linker script */
.word  _sdata
/* end address for the .data section. defined in linker script */
.word  _edata
/* start address for the .bss section. defined in linker script */
.word  _sbss
/* end address for the .bss section. defined in linker script */
.word  _ebss


  .section  .text.Reset_Handler
  .weak  Reset_Handler
  .type  Reset_Handler, %function

Reset_Handler:
  movs  r1, #0
  b     LoopCopyDataInit /* Copy the data segment initializers from flash to SRAM */

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
  b     LoopFillZerobss

/* Zero fill the bss segment. */
FillZerobss:
  movs  r3, #0
  str   r3, [r2]
  adds  r2, r2, #4

LoopFillZerobss:
  ldr  r3, = _ebss
  cmp  r2, r3
  bcc  FillZerobss

  bl  SystemInit        /* Call the clock system init function */
  bl  __libc_init_array /* Call static constructors */
  bl  main              /* Call the application's entry point */

.size  Reset_Handler, .-Reset_Handler

/* This is the code that gets called when the processor receives an unexpected
 * interrupt. This simply enters an infinite loop, preserving the system state
 * for examination by a debugger.
 */
  .section  .text.Default_Handler,"ax",%progbits
Default_Handler:
Infinite_Loop:
  b  Infinite_Loop
  .size  Default_Handler, .-Default_Handler

/* The minimal vector table for a Cortex-M.  Note that the proper constructs
 * must be placed on this to ensure that it ends up at physical address
 * 0x0000.0000.
 */
  .section  .isr_vector,"a",%progbits
  .type     g_pfnVectors, %object
  .size     g_pfnVectors, .-g_pfnVectors

g_pfnVectors:
  .word  _estack                        /* 0x00 Stack Pointer                */
  .word  Reset_Handler                  /* 0x04 Reset                        */
  .word  NMI_Handler                    /* 0x08 Non maskable interrupt       */
  .word  HardFault_Handler              /* 0x0C All class of fault           */
  .word  0                              /* 0x10 Reserved                     */
  .word  0                              /* 0x14 Reserved                     */
  .word  0                              /* 0x18 Reserved                     */
  .word  0                              /* 0x1C Reserved                     */
  .word  0                              /* 0x20 Reserved                     */
  .word  0                              /* 0x24 Reserved                     */
  .word  0                              /* 0x28 Reserved                     */
  .word  SVC_Handler                    /* 0x2C System service call via SWI  */
  .word  0                              /* 0x30 Reserved                     */
  .word  0                              /* 0x34 Reserved                     */
  .word  PendSV_Handler                 /* 0x38 Pendable request for service */
  .word  SysTick_Handler                /* 0x3C System tick timer            */
/* ^ Above are the 16 M0 exceptions ^...v Below are the 32 STM32 IRQ lines v */
  .word  WWDG_IRQHandler                /* 0x40 Window WatchDog              */
  .word  0                              /* 0x44 Reserved                     */
  .word  RTC_IRQHandler                 /* 0x48 RTC through the EXTI line    */
  .word  FLASH_IRQHandler               /* 0x4C Flash                        */
  .word  RCC_IRQHandler                 /* 0x50 RCC                          */
  .word  EXTI0_1_IRQHandler             /* 0x54 EXTI Line[1:0]               */
  .word  EXTI2_3_IRQHandler             /* 0x58 EXTI Line[3:2]               */
  .word  EXTI4_15_IRQHandler            /* 0x5C EXTI Line[15:4]              */
  .word  0                              /* 0x60 Reserved                     */
  .word  DMA1_Channel1_IRQHandler       /* 0x64 DMA1 channel 1               */
  .word  DMA1_Channel2_3_IRQHandler     /* 0x68 DMA1 channel 2 and channel 3 */
  .word  DMA1_Channel4_5_IRQHandler     /* 0x6C DMA1 channel 4 and channel 5 */
  .word  ADC1_IRQHandler                /* 0x70 ADC                          */
  .word  TIM1_BRK_UP_TRG_COM_IRQHandler /* 0x74 TIM1 Break, Update, Trigger and Commutation */
  .word  TIM1_CC_IRQHandler             /* 0x78 TIM1 Capture Compare         */
  .word  0                              /* 0x7C Reserved                     */
  .word  TIM3_IRQHandler                /* 0x80 TIM3                         */
  .word  TIM6_IRQHandler                /* 0x84 TIM6                         */
  .word  0                              /* 0x88 Reserved                     */
  .word  TIM14_IRQHandler               /* 0x8C TIM14                        */
  .word  TIM15_IRQHandler               /* 0x90 TIM15                        */
  .word  TIM16_IRQHandler               /* 0x94 TIM16                        */
  .word  TIM17_IRQHandler               /* 0x98 TIM17                        */
  .word  I2C1_IRQHandler                /* 0x9C I2C1                         */
  .word  I2C2_IRQHandler                /* 0xA0 I2C2                         */
  .word  SPI1_IRQHandler                /* 0xA4 SPI1                         */
  .word  SPI2_IRQHandler                /* 0xA8 SPI2                         */
  .word  USART1_IRQHandler              /* 0xAC USART1                       */
  .word  USART2_IRQHandler              /* 0xB0 USART2                       */
  .word  USART3_4_5_6_IRQHandler        /* 0xB4 USART 3, 4, 5, and 6         */
  .word  0                              /* 0xB8 Reserved                     */
  .word  USB_IRQHandler                 /* 0xBC USB                          */

/*******************************************************************************
*
* Provide weak aliases for each Exception handler to the Default_Handler.
* As they are weak aliases, any function with the same name will override
* this definition.
*
*******************************************************************************/

  .weak       NMI_Handler
  .thumb_set  NMI_Handler, Default_Handler

  .weak       HardFault_Handler
  .thumb_set  HardFault_Handler, Default_Handler

  .weak       SVC_Handler
  .thumb_set  SVC_Handler, Default_Handler

  .weak       PendSV_Handler
  .thumb_set  PendSV_Handler, Default_Handler

  .weak       SysTick_Handler
  .thumb_set  SysTick_Handler, Default_Handler

  .weak       WWDG_IRQHandler
  .thumb_set  WWDG_IRQHandler, Default_Handler

  .weak       RTC_IRQHandler
  .thumb_set  RTC_IRQHandler, Default_Handler

  .weak       FLASH_IRQHandler
  .thumb_set  FLASH_IRQHandler, Default_Handler

  .weak       RCC_IRQHandler
  .thumb_set  RCC_IRQHandler, Default_Handler

  .weak       EXTI0_1_IRQHandler
  .thumb_set  EXTI0_1_IRQHandler, Default_Handler

  .weak       EXTI2_3_IRQHandler
  .thumb_set  EXTI2_3_IRQHandler, Default_Handler

  .weak       EXTI4_15_IRQHandler
  .thumb_set  EXTI4_15_IRQHandler, Default_Handler

  .weak       DMA1_Channel1_IRQHandler
  .thumb_set  DMA1_Channel1_IRQHandler, Default_Handler

  .weak       DMA1_Channel2_3_IRQHandler
  .thumb_set  DMA1_Channel2_3_IRQHandler, Default_Handler

  .weak       DMA1_Channel4_5_IRQHandler
  .thumb_set  DMA1_Channel4_5_IRQHandler, Default_Handler

  .weak       ADC1_IRQHandler
  .thumb_set  ADC1_IRQHandler, Default_Handler

  .weak       TIM1_BRK_UP_TRG_COM_IRQHandler
  .thumb_set  TIM1_BRK_UP_TRG_COM_IRQHandler, Default_Handler

  .weak       TIM1_CC_IRQHandler
  .thumb_set  TIM1_CC_IRQHandler, Default_Handler

  .weak       TIM3_IRQHandler
  .thumb_set  TIM3_IRQHandler, Default_Handler

  .weak       TIM6_IRQHandler
  .thumb_set  TIM6_IRQHandler, Default_Handler

  .weak       TIM14_IRQHandler
  .thumb_set  TIM14_IRQHandler, Default_Handler

  .weak       TIM15_IRQHandler
  .thumb_set  TIM15_IRQHandler, Default_Handler

  .weak       TIM16_IRQHandler
  .thumb_set  TIM16_IRQHandler, Default_Handler

  .weak       TIM17_IRQHandler
  .thumb_set  TIM17_IRQHandler, Default_Handler

  .weak       I2C1_IRQHandler
  .thumb_set  I2C1_IRQHandler, Default_Handler

  .weak       I2C2_IRQHandler
  .thumb_set  I2C2_IRQHandler, Default_Handler

  .weak       SPI1_IRQHandler
  .thumb_set  SPI1_IRQHandler, Default_Handler

  .weak       SPI2_IRQHandler
  .thumb_set  SPI2_IRQHandler, Default_Handler

  .weak       USART1_IRQHandler
  .thumb_set  USART1_IRQHandler, Default_Handler

  .weak       USART2_IRQHandler
  .thumb_set  USART2_IRQHandler, Default_Handler

  .weak       USART3_4_5_6_IRQHandler
  .thumb_set  USART3_4_5_6_IRQHandler, Default_Handler

  .weak       USB_IRQHandler
  .thumb_set  USB_IRQHandler, Default_Handler

  .weak       SystemInit
