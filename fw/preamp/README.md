This directory contains the firmware for AmpliPi's preamp board.
Either System Workbench for STM32 or a CMake-based build can be used
to compile the firmware.
The System Workbench for STM32 setup instructions can be found at
[docs/preamp_dev.md](../../docs/preamp_dev.md).
The CMake build process is documented here.

# CMake Build
The gcc-arm-none-eabi compiler is used along with a CMake build system
to compile the Preamp Board's firmware directly on the Raspberry Pi.

## Install dependencies
On Raspbian Buster or Ubuntu 20.04:
```sh
sudo apt install cmake gcc-arm-none-eabi
```
Note: if installing on the AmpliPi's Raspberry Pi, DO NOT run an
`apt upgrade` at any point.

To program from AmpliPi's Raspberry Pi
[stm32flash](https://sourceforge.net/p/stm32flash) is used.
It is pre-installed on recent AmpliPis but if not it can be installed with:
```
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
To set debug build:
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
