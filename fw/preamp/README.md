# Preamp Board Firmware

This directory contains the firmware for AmpliPi's preamp board.
CMake and gcc-arm-none-eabi are used to build the firmware.

## Dependency Setup

The gcc-arm-none-eabi compiler is used along with a CMake build system
to compile the Preamp Board's firmware directly on the Raspberry Pi.

### Install CMake

On Raspbian Buster or Ubuntu 20.04:

```sh
sudo apt update
sudo apt install cmake
```

### Install gcc-arm-none-eabi

From <https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads>
download the appropriate arm-none-eabi for your host machine.

#### Linux Install

libncursesw5 is only required for GDB.

```sh
wget https://developer.arm.com/-/media/Files/downloads/gnu/13.2.rel1/binrel/arm-gnu-toolchain-13.2.rel1-$(arch)-arm-none-eabi.tar.xz
sudo tar -xf arm-gnu-toolchain-13.2.rel1-$(arch)-arm-none-eabi.tar.xz -C /usr/share
sudo ln -s /usr/share/arm-gnu-toolchain-13.2.Rel1-$(arch)-arm-none-eabi/bin/arm-none-eabi-* /usr/bin
sudo apt install libncursesw5
```

### Install stm32flash

To program from AmpliPi's Raspberry Pi
[stm32flash](https://sourceforge.net/p/stm32flash) is used.
It should be pre-installed on AmpliPi but if not it can be installed with:

```sh
sudo apt install stm32flash
```

## Quick Program (and Compile)
The `program_firmware` script in the `scripts` directory of AmpliPi
includes the most common use-cases for compiling and programming the Preamp.
Try
```
scripts/program_firmware -h
```
to get all the options available.
Alternatively see below for the full compile and program steps.

## Compile
From the `fw/preamp` directory:
```sh
mkdir build
cd build
cmake ..
make
```

This defaults to a Release build.

### Debug Build
To set debug build (and enable printf):
```sh
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

## Program
After running the Compile steps above on the Pi,
program the preamp's firmware by running
```sh
make program
```

The programming is done by the `stm32flash` utility, but uses
`amplipi/hw.py`'s logic to program any expanders found.
```sh
venv/bin/python -m amplipi.hw --flash preamp.bin
```

If for whatever reason an expander is not responding properly to I2C messages,
then it won't be auto-detected and programmed.
The number of units to attempt programming of can be overriden with `-n`.
```sh
venv/bin/python -m amplipi.hw -n 3 --flash preamp.bin
```
`-n 3` will attempt to program the main AmpliPi unit, plus two expanders.
