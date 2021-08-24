# Install dependencies
On Ubuntu 20.04 or Raspbian Buster:
```sh
sudo apt install cmake gcc-arm-none-eabi
```

# Compile
From the `fw/preamp` directory:
```sh
mkdir build
cd build
cmake ..
make
```

## Debug Build
To set debug build:
```sh
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

# Program
After running the Compile steps above on the Pi,
program the master unit's preamp by running
```sh
make program
```

or program an expansion unit by running
```sh
make program-expander
```
