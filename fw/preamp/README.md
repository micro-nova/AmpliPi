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
program the master unit's preamp by running
```sh
make program
```

or program an expansion unit by running
```sh
make program-expander
```
