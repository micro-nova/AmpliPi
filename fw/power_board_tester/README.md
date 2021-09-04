# Power Board Tester
This project is implemented using an Arduino Due on a custom test rig.

## Software Setup
Just like the Preamp Board's STM32 project, here CMake is used to configure
and build the project. First, ensure all submodules have been initialized
and are up-to-date in this repo.
```sh
git submodule update --init --recursive
```

## Building
Then use CMake to build:
```sh
cd fw/power_board_tester
mkdir build
cd build
cmake ..
make
```

## Programing
A custom CMake target `program` allows programming using make:
```sh
make program
```

The programming utility, [BOSSA](https://github.com/shumatech/BOSSA) programs
the Due using either USB connector, but here we use the Native USB connector
for debugging so it's best to use that.
