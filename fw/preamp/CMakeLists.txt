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

# Generate version.c, which contains version info from the git repo
set(version_c_file "${CMAKE_CURRENT_BINARY_DIR}/generated/version.c")
add_custom_target(gitversion COMMAND ${CMAKE_COMMAND}
  -Dinfile="${CMAKE_CURRENT_SOURCE_DIR}/src/version.c.in"
  -Doutfile=${version_c_file}
  -P ${CMAKE_CURRENT_LIST_DIR}/GitVersion.cmake
  BYPRODUCTS ${version_c_file}
)

macro(add_hardware_version HW_VERSION)
  set(TARGET_NAME ${PROJECT_NAME}_v${HW_VERSION})

  add_executable(${TARGET_NAME}.elf
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

  target_include_directories(${TARGET_NAME}.elf PRIVATE
    CMSIS/core
    CMSIS/device
    StdPeriph_Driver/inc
  )

  target_compile_definitions(${TARGET_NAME}.elf PRIVATE
    STM32F0
    STM32F030R8Tx
    STM32
    USE_STDPERIPH_DRIVER
    STM32F030
    HW_VERSION=${HW_VERSION}
  )

  # -fno-exceptions reduces C++ code size but exceptions must not be thrown
  set(ARM_FLAGS
    -mcpu=cortex-m0 -mthumb -mfloat-abi=soft
  )

  target_compile_options(${TARGET_NAME}.elf PRIVATE
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
  target_compile_options(${TARGET_NAME}.elf PRIVATE "$<$<CONFIG:Debug>:${DEBUG_FLAGS}>")
  target_compile_options(${TARGET_NAME}.elf PRIVATE "$<$<CONFIG:Release>:${RELEASE_FLAGS}>")
  target_compile_options(${TARGET_NAME}.elf PRIVATE "$<$<CONFIG:RelWithDebInfo>:${RELWITHDEBINFO_FLAGS}>")
  target_compile_options(${TARGET_NAME}.elf PRIVATE "$<$<CONFIG:MinSizeRel>:${MINSIZEREL_FLAGS}>")

  target_link_options(${TARGET_NAME}.elf PRIVATE
    ${ARM_FLAGS}
    -T${CMAKE_CURRENT_LIST_DIR}/LinkerScript.ld
    -Wl,--gc-sections           # Garbage-collect unused sections to remove dead code.
    -Wl,-Map,${TARGET_NAME}.map # Generate a map file along with the elf.
    -Wl,--print-memory-usage    # Print RAM/ROM memory usage.
    -Wl,--no-warn-rwx-segments  # Ignore warnings about RWX segments introduced in binutils 2.39.

    # nosys adds _sbrk() for sprintf(), nano reduces the code size
    # Needed if DEBUG_PRINT is defined
    -specs=nosys.specs
    -specs=nano.specs # Reduces RAM ~1.7kB, ROM ~5.8kB, but restricts printf() to C89.
  )

  add_dependencies(${TARGET_NAME}.elf gitversion)
  target_sources(${TARGET_NAME}.elf PRIVATE ${version_c_file})
  target_include_directories(${TARGET_NAME}.elf PRIVATE src)

  add_custom_target(program_v${HW_VERSION}
    COMMAND cd ${CMAKE_CURRENT_SOURCE_DIR}../../.. &&
            python3 -m amplipi.hw --flash ${CMAKE_CURRENT_BINARY_DIR}/${TARGET_NAME}.bin
    COMMENT "Programming preamp hw v${HW_VERSION}"
    DEPENDS ${TARGET_NAME}.elf
  )

endmacro()

add_hardware_version(0)
add_hardware_version(4)
