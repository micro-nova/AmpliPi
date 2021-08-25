cmake_minimum_required(VERSION 3.13)

# Toolchain must be defined before project
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE AND NOT DEFINED CMAKE_CXX_COMPILER)
  set(CMAKE_TOOLCHAIN_FILE arm-none-eabi-toolchain.cmake)
else()
  set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
endif()

project(preamp_bd C ASM)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release")
endif()

add_executable(${PROJECT_NAME}.elf
  src/channel.c
  src/front_panel.c
  src/main.c
  src/port_defs.c
  src/ports.c
  src/power_board.c
  src/system_stm32f0xx.c
  src/systick.c

  startup/startup_stm32.s

  StdPeriph_Driver/src/stm32f0xx_cec.c
  StdPeriph_Driver/src/stm32f0xx_gpio.c
  StdPeriph_Driver/src/stm32f0xx_i2c.c
  StdPeriph_Driver/src/stm32f0xx_pwr.c
  StdPeriph_Driver/src/stm32f0xx_rcc.c
  StdPeriph_Driver/src/stm32f0xx_usart.c
)

target_include_directories(${PROJECT_NAME}.elf PRIVATE
  inc
  CMSIS/core
  CMSIS/device
  StdPeriph_Driver/inc
)

target_compile_definitions(${PROJECT_NAME}.elf PRIVATE
  STM32F0
  STM32F030R8Tx
  STM32
  USE_STDPERIPH_DRIVER
  STM32F030
)

# -fno-exceptions reduces C++ code size but exceptions must not be thrown
set(ARM_FLAGS
  -mcpu=cortex-m0 -mthumb -mfloat-abi=soft
)

target_compile_options(${PROJECT_NAME}.elf PRIVATE
  ${ARM_FLAGS}
  -std=c11
  -fmessage-length=0
  -ffunction-sections
  #-fdata-sections
  #-fno-exceptions
  -Wall
  -Wextra
  -Werror
)

set(DEBUG_FLAGS -Og -g)
set(RELEASE_FLAGS -O3)
set(RELWITHDEBINFO_FLAGS -O3 -g)
set(MINSIZEREL_FLAGS -Os)
target_compile_options(${PROJECT_NAME}.elf PRIVATE "$<$<CONFIG:Debug>:${DEBUG_FLAGS}>")
target_compile_options(${PROJECT_NAME}.elf PRIVATE "$<$<CONFIG:Release>:${RELEASE_FLAGS}>")
target_compile_options(${PROJECT_NAME}.elf PRIVATE "$<$<CONFIG:RelWithDebInfo>:${RELWITHDEBINFO_FLAGS}>")
target_compile_options(${PROJECT_NAME}.elf PRIVATE "$<$<CONFIG:MinSizeRel>:${MINSIZEREL_FLAGS}>")

#target_link_libraries(${PROJECT_NAME}.elf PRIVATE
#  m
#)
target_link_options(${PROJECT_NAME}.elf PRIVATE
  ${ARM_FLAGS}
  -T${CMAKE_CURRENT_LIST_DIR}/LinkerScript.ld
  -Wl,--gc-sections
  -Wl,-Map,${PROJECT_NAME}.map
)

# Print firmware size
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
  COMMAND ${CMAKE_SIZE_UTIL} -B "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.elf"
)

# Generate bin file and disassembly
set_property(DIRECTORY APPEND PROPERTY ADDITIONAL_MAKE_CLEAN_FILES
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.bin
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.disasm
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.map
)
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
  COMMAND ${CMAKE_OBJCOPY} -O binary "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.elf"
          "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.bin"
)
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
  COMMAND ${CMAKE_OBJDUMP} -CSd "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.elf" >
          "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.disasm"
)

add_custom_target(program
  COMMAND sudo stm32flash -vRb 115200 -i 5,-4,4 -w ${PROJECT_NAME}.bin /dev/serial0 &&
          printf 'A\\x10\\r\\n' > /dev/serial0 # Set i2c address
  COMMENT "Programming preamp"
  DEPENDS ${PROJECT_NAME}.elf
)