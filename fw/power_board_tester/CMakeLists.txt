cmake_minimum_required(VERSION 3.1)

# Toolchain must be defined before project so include SAM here
include(${CMAKE_CURRENT_SOURCE_DIR}/../sam/cmake/sam.cmake)

project(power_board_tester)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release")
endif()

sam_add_executable(
  ${PROJECT_NAME}

  # Hardware
  src/main.cpp

  # I2C and SPI libraries
  ${SAM_PATH}/arduinosam/libraries/Wire/src/Wire.cpp
  ${SAM_PATH}/arduinosam/libraries/SPI/src/SPI.cpp

  # Adafruit ILI9341 library and dependencies
  ${SAM_PATH}/libraries/adafruit_ili9341/Adafruit_ILI9341.cpp
  ${SAM_PATH}/libraries/adafruit-gfx-library/Adafruit_GFX.cpp
  ${SAM_PATH}/libraries/adafruit-gfx-library/Adafruit_SPITFT.cpp
  ${SAM_PATH}/libraries/adafruit_busio/Adafruit_SPIDevice.cpp

)

sam_target_include_directories(${PROJECT_NAME}
  ${SAM_PATH}/libraries/adafruit_ili9341
  ${SAM_PATH}/libraries/adafruit-gfx-library
  ${SAM_PATH}/libraries/adafruit_busio
)

sam_target_compile_options(${PROJECT_NAME}
  # Pretend to be the latest Arduino IDE - Adafruit GFX requires this set
  -DARDUINO=10815
)
