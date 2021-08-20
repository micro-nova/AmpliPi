cmake_minimum_required(VERSION 3.5)

# Set the path to the root of the SAM directory
set(SAM_PATH ${CMAKE_CURRENT_LIST_DIR}/../)

if(NOT DEFINED CMAKE_TOOLCHAIN_FILE AND NOT DEFINED CMAKE_CXX_COMPILER)
  set(CMAKE_TOOLCHAIN_FILE ${SAM_PATH}/cmake/arm-none-eabi-toolchain.cmake)
else()
  set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
endif()

set(SAM_INCLUDE_DIRS
  ${SAM_PATH}/arduinosam/cores/arduino
  ${SAM_PATH}/arduinosam/system/libsam
  ${SAM_PATH}/arduinosam/system/libsam/include
  ${SAM_PATH}/arduinosam/system/CMSIS/CMSIS/Include
  ${SAM_PATH}/arduinosam/system/CMSIS/Device/ATMEL
  ${SAM_PATH}/arduinosam/system/CMSIS/Device/ATMEL/sam3xa/include
  ${SAM_PATH}/arduinosam/variants/arduino_due_x
  ${SAM_PATH}/arduinosam/libraries/HID/src
  ${SAM_PATH}/arduinosam/libraries/SPI/src
  ${SAM_PATH}/arduinosam/libraries/Wire/src
)

set(ARM_FLAGS
  -mcpu=cortex-m3 -mthumb
  -Wno-expansion-to-defined
  #-Wall -Wextra TODO: Fix warnings in ArduinoSam
  -ffunction-sections
  -fdata-sections
  --param max-inline-insns-single=500
)

set(CXX_FLAGS
  -fno-threadsafe-statics
  -fno-rtti
  -fno-exceptions
)

set(BOARD_FLAGS
  -DF_CPU=84000000L
  -D__SAM3X8E__
  -DUSBCON
  -DUSB_VID=0x2341 -DUSB_PID=0x003e
  -DUSB_MANUFACTURER="Arduino LLC"
  -DUSB_PRODUCT="Arduino Due"
)

set(DEBUG_FLAGS -Og -g)
set(RELEASE_FLAGS -O3 -DNDEBUG)
set(RELWITHDEBINFO_FLAGS -O3 -g -DNDEBUG)
set(MINSIZEREL_FLAGS -Os -s -DNDEBUG)

macro(sam_add_executable target)

  # The remaining unparsed arguments should be the source files
  add_executable(${target}.elf
    ${ARGN}

    # Arduino
    ${SAM_PATH}/arduinosam/cores/arduino/abi.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/IPAddress.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/main.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/new.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/Print.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/Reset.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/RingBuffer.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/Stream.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/UARTClass.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/USARTClass.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/watchdog.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/wiring_pulse.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/WMath.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/WString.cpp

    ${SAM_PATH}/arduinosam/cores/arduino/cortex_handlers.c
    ${SAM_PATH}/arduinosam/cores/arduino/hooks.c
    ${SAM_PATH}/arduinosam/cores/arduino/iar_calls_sam3.c
    ${SAM_PATH}/arduinosam/cores/arduino/itoa.c
    ${SAM_PATH}/arduinosam/cores/arduino/syscalls_sam3.c
    ${SAM_PATH}/arduinosam/cores/arduino/WInterrupts.c
    ${SAM_PATH}/arduinosam/cores/arduino/wiring_analog.c
    ${SAM_PATH}/arduinosam/cores/arduino/wiring.c
    ${SAM_PATH}/arduinosam/cores/arduino/wiring_digital.c
    ${SAM_PATH}/arduinosam/cores/arduino/wiring_shift.c

    ${SAM_PATH}/arduinosam/cores/arduino/avr/dtostrf.c

    ${SAM_PATH}/arduinosam/cores/arduino/USB/CDC.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/USB/PluggableUSB.cpp
    ${SAM_PATH}/arduinosam/cores/arduino/USB/USBCore.cpp

    ${SAM_PATH}/arduinosam/variants/arduino_due_x/variant.cpp

    ${SAM_PATH}/arduinosam/system/CMSIS/Device/ATMEL/sam3xa/source/system_sam3xa.c
    ${SAM_PATH}/arduinosam/system/CMSIS/Device/ATMEL/sam3xa/source/gcc/startup_sam3xa.c
    ${SAM_PATH}/arduinosam/system/libsam/source/adc12_sam3u.c
    ${SAM_PATH}/arduinosam/system/libsam/source/adc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/can.c
    ${SAM_PATH}/arduinosam/system/libsam/source/dacc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/efc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/emac.c
    ${SAM_PATH}/arduinosam/system/libsam/source/gpbr.c
    ${SAM_PATH}/arduinosam/system/libsam/source/interrupt_sam_nvic.c
    ${SAM_PATH}/arduinosam/system/libsam/source/pio.c
    ${SAM_PATH}/arduinosam/system/libsam/source/pmc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/pwmc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/rstc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/rtc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/rtt.c
    ${SAM_PATH}/arduinosam/system/libsam/source/spi.c
    ${SAM_PATH}/arduinosam/system/libsam/source/ssc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/tc.c
    ${SAM_PATH}/arduinosam/system/libsam/source/timetick.c
    ${SAM_PATH}/arduinosam/system/libsam/source/trng.c
    ${SAM_PATH}/arduinosam/system/libsam/source/twi.c
    ${SAM_PATH}/arduinosam/system/libsam/source/udp.c
    ${SAM_PATH}/arduinosam/system/libsam/source/udphs.c
    ${SAM_PATH}/arduinosam/system/libsam/source/uotghs.c
    ${SAM_PATH}/arduinosam/system/libsam/source/uotghs_device.c
    ${SAM_PATH}/arduinosam/system/libsam/source/uotghs_host.c
    ${SAM_PATH}/arduinosam/system/libsam/source/usart.c
    ${SAM_PATH}/arduinosam/system/libsam/source/wdt.c
  )

  target_include_directories(${target}.elf PRIVATE ${SAM_INCLUDE_DIRS})

  target_compile_options(${target}.elf PRIVATE ${ARM_FLAGS} ${BOARD_FLAGS})
  target_compile_options(${target}.elf PRIVATE "$<$<COMPILE_LANGUAGE:CXX>:${CXX_FLAGS}>")
  target_compile_options(${target}.elf PRIVATE "$<$<CONFIG:Debug>:${DEBUG_FLAGS}>")
  target_compile_options(${target}.elf PRIVATE "$<$<CONFIG:Release>:${RELEASE_FLAGS}>")
  target_compile_options(${target}.elf PRIVATE "$<$<CONFIG:RelWithDebInfo>:${RELWITHDEBINFO_FLAGS}>")
  target_compile_options(${target}.elf PRIVATE "$<$<CONFIG:MinSizeRel>:${MINSIZEREL_FLAGS}>")
  target_link_libraries(${target}.elf PRIVATE
    -T"${SAM_PATH}/arduinosam/variants/arduino_due_x/linker_scripts/gcc/flash.ld"
    -Wl,-Map,"${target}.map"  # Generate a map file
    -Xlinker --gc-sections    # Remove unused sections
    -Wl,--cref                # Output a cross reference table
    -lm ${ARM_FLAGS}
  )

  # Print firmware size
  add_custom_command(TARGET ${target}.elf POST_BUILD
    COMMAND ${CMAKE_SIZE_UTIL} --format=berkeley "${CMAKE_CURRENT_BINARY_DIR}/${target}.elf"
  )

  # Create bin file
  add_custom_command(TARGET ${target}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary "${CMAKE_CURRENT_BINARY_DIR}/${target}.elf"
            "${CMAKE_CURRENT_BINARY_DIR}/${target}.bin"
  )

  # Generate disassembly
  add_custom_command(TARGET ${target}.elf POST_BUILD
    COMMAND ${CMAKE_OBJDUMP} -CSd "${CMAKE_CURRENT_BINARY_DIR}/${target}.elf" >
            "${CMAKE_CURRENT_BINARY_DIR}/${target}.disasm"
  )

  # Build BOSSA
  add_custom_command(OUTPUT ${SAM_PATH}/bossa/bin/bossac
    COMMAND make -C ${SAM_PATH}/bossa bossac
  )

  # Add program target which programs the microcontroller's flash and runs the program
  add_custom_target(program
    COMMENT "Programming flash"
    DEPENDS ${SAM_PATH}/bossa/bin/bossac
    COMMAND ${SAM_PATH}/bossa/bin/bossac -a -w -v -R -b ${target}.bin
  )
  add_dependencies(program ${target}.elf)
endmacro()

macro(sam_target_include_directories target)
  target_include_directories(${target}.elf PRIVATE ${ARGN})
endmacro()

macro(sam_target_compile_options target)
  target_compile_options(${target}.elf PRIVATE ${ARGN})
endmacro()
