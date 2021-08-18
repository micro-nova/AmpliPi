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

  # I2C Library
  ${SAM_PATH}/arduinosam/libraries/Wire/src/Wire.cpp
)

#sam_target_include_directories(${PROJECT_NAME}
#  include
#)
