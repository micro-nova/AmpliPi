cmake_minimum_required(VERSION 3.13)

# Toolchain must be defined before project
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE AND (NOT DEFINED CMAKE_C_COMPILER OR NOT DEFINED CMAKE_ASM_COMPILER))
  set(CMAKE_TOOLCHAIN_FILE arm-none-eabi-toolchain.cmake)
else()
  set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
endif()

project(preamp_bd C ASM)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release")
endif()

add_executable(${PROJECT_NAME}.elf
  src/adc.c
  src/audio.c
  src/ctrl_i2c.c
  src/fans.c
  src/i2c.c
  src/int_i2c.c
  src/leds.c
  src/main.c
  src/pins.c
  src/pwr_gpio.c
  src/rcc.c
  src/serial.c
  src/systick.c
  src/watchdog.c

  src/startup_stm32.s

  StdPeriph_Driver/src/stm32f0xx_gpio.c
  StdPeriph_Driver/src/stm32f0xx_i2c.c
  StdPeriph_Driver/src/stm32f0xx_rcc.c
  StdPeriph_Driver/src/stm32f0xx_usart.c
)

target_include_directories(${PROJECT_NAME}.elf PRIVATE
  CMSIS/core
  CMSIS/device
  StdPeriph_Driver/inc
)

target_compile_definitions(${PROJECT_NAME}.elf PRIVATE
  STM32
  STM32F0
  STM32F030
  STM32F030R8Tx
)

# -fno-exceptions reduces C++ code size but exceptions must not be thrown
set(ARM_FLAGS
  -mcpu=cortex-m0 -mthumb -mfloat-abi=soft
)

target_compile_options(${PROJECT_NAME}.elf PRIVATE
  ${ARM_FLAGS}
  -std=c2x
  -ffunction-sections # Generate a section for each function so the linker can remove unused functions.
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

# Allow printf via UART in debug mode.
# Note: UART messages can mess with an up-chain preamp in bootloader mode.
target_compile_definitions(${PROJECT_NAME}.elf PRIVATE "$<$<CONFIG:Debug>:DEBUG_PRINTS>")

target_link_options(${PROJECT_NAME}.elf PRIVATE
  ${ARM_FLAGS}
  -T${CMAKE_CURRENT_LIST_DIR}/preamp.ld
  -Wl,--gc-sections           # Garbage-collect unused sections to remove dead code.
  -Wl,-Map,${PROJECT_NAME}.map # Generate a map file along with the elf.
  -Wl,--print-memory-usage    # Print RAM/ROM memory usage.
  -Wl,--no-warn-rwx-segments  # Ignore warnings about RWX segments introduced in binutils 2.39.

  -specs=nosys.specs # Running on bare metal, system calls will be implemented manually.
  -specs=nano.specs  # Reduces RAM ~1.7kB, ROM ~5.8kB, but restricts printf() to C89.
)

# Generate version.c, which contains version info from the git repo
set(version_c_file "${CMAKE_CURRENT_BINARY_DIR}/generated/version.c")
add_custom_target(gitversion COMMAND ${CMAKE_COMMAND}
  -Dinfile="${CMAKE_CURRENT_SOURCE_DIR}/src/version.c.in"
  -Doutfile=${version_c_file}
  -P ${CMAKE_CURRENT_LIST_DIR}/GitVersion.cmake
  BYPRODUCTS ${version_c_file}
)

add_dependencies(${PROJECT_NAME}.elf gitversion)
target_sources(${PROJECT_NAME}.elf PRIVATE ${version_c_file})
target_include_directories(${PROJECT_NAME}.elf PRIVATE src)

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
  COMMAND cd ${CMAKE_CURRENT_SOURCE_DIR}../../.. &&
          python3 -m amplipi.hw --flash ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.bin
  COMMENT "Programming preamp"
  DEPENDS ${PROJECT_NAME}.elf
)
