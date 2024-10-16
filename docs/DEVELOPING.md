
# Developing for the AmpliPi Project

Thank you for your interest in contributing to AmpliPi! This guide will help you set up your environment and start developing.

---

## Table of Contents

1. [Development Options](#development-options)
   - [Developing on a Separate Computer](#developing-on-a-separate-computer)
   - [Developing on an AmpliPi Controller](#developing-on-an-amplipi-controller)
   - [Mocked Development Setups](#mocked-development-setups)
2. [Developing the Frontend](#developing-the-frontend)
   - [Setting Up Node.js](#setting-up-nodejs)
   - [With an Amplipi](#with-an-amplipi)
   - [Without an Amplipi](#without-an-amplipi)
3. [Windows-Specific Setup](#windows-specific-setup)
   - [Using WSL for Development](#using-wsl-for-development)
4. [Installing AmpliPi on a Pi Compute Module](#installing-amplipi-on-a-pi-compute-module)

---

## Development Options

### Developing on a Separate Computer

To develop for AmpliPi on a separate system and remotely test on your AmpliPi controller:

1. Clone the [AmpliPi repository](https://github.com/micro-nova) on a Linux-based system. If you're using Windows, WSL (Windows Subsystem for Linux) is strongly recommended.
2. Use your favorite text/code editor to make changes. We at MicroNova use VSCode, for example.
3. Deploy your changes with the `scripts/deploy` script. a typical deployment command looks like `scripts/deploy pi@{IP}`. You may also need the SSH password, which can be found along with the system's IP on the front display of your unit.

After deployment:
- SSH into AmpliPi (`ssh pi@{IP}`).
- Navigate to the development root: `cd ~/amplipi-dev`.
- Run the server in debug mode: `./scripts/run_debug_webserver`, which will start a webserver at [amplipi.local:5000](http://amplipi.local:5000).
- Restart the AmpliPi service when done with `systemctl --user restart amplipi`.

### Developing on an AmpliPi Controller

To directly develop on an AmpliPi controller over SSH:

1. Clone the repository on the AmpliPi at `~/amplipi-dev`
2. Make your changes using your preferred editor.
3. Run the server in debug mode: `./scripts/run_debug_webserver`
4. When ready, run `./scripts/configure.py --python-deps --os-deps --display --web` to install necessary dependencies and reconfigure services.

---

## Mocked Development Setups

If you don’t have an AmpliPi system, you can use a mocked setup for development and testing.

### Mocked Audio & Controller (Debian-Based System)

This method allows development on systems like a Raspberry Pi or Ubuntu.

Supports:
- Web interface development
- API testing
- Basic stream testing

To set it up:
1. Clone the repository.
2. Install streaming dependencies using `./scripts/configure.py --os-deps`.
3. Install Python dependencies with `./scripts/configure.py --python-deps`.
4. Run the mock server with `./scripts/run_debug_webserver` (add the `--mock-streams` flag if you didn’t install the streaming dependencies).

### Mocked Controller with 4 Stereo Audio Channels (Raspberry Pi OS)

This method requires a Raspberry Pi with a compatible USB audio device.

Supports:
- Web interface development
- API testing
- Streams integration and testing

Setup:
1. Install a 32-bit version of Raspberry Pi OS (older than December 2020).
2. Connect a compatible 7.1 channel USB audio device.
3. Clone the repository and modify the `asound.conf` to configure the audio device.
4. Deploy using `scripts/deploy USER@HOSTNAME --mock-ctrl`.
5. Run the mock controller with `./scripts/run_debug_webserver --mock-ctrl`.

---
## Developing the Frontend
Our frontend is a React webapp, to develop it you must first download and install a few dependencies:
- [React](https://react.dev/learn/installation)
- [Node.js](#setting-up-nodejs)

### Setting Up Node.js

AmpliPi is built with Node.js 18. Use `scripts/deploy` to install dependencies, but you’ll need to install Node.js manually:

#### For Ubuntu <=20.04
The apt version of Node.js is outdated. Use Node Version Manager (NVM) to install a newer version:

```sh
NVM_DIR="${HOME}/.nvm"
git clone --branch v0.39.7 https://github.com/nvm-sh/nvm.git "$NVM_DIR"
cat >> "${HOME}/.bashrc" << EOF

[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
EOF
source "$NVM_DIR/nvm.sh"
nvm install 18
```

#### Memory Limitation for AmpliPi
When building directly on the AmpliPi, limit memory usage during the build step:

```sh
NODE_OPTIONS=--max_old_space_size=768 npm run build
```



To develop the frontend, your strategy will bifurcate depending on your access to an Amplipi:

### With an Amplipi
You will need to edit the `scripts/run_debug_frontend` file with the IP of an Amplipi and then run said file, making sure to revert the file when you're done as to not push your local IP to the repo. This will use that Amplipi's backend so you can live develop the React app on a localhost that dynamically regenerates the app as you save your files. This is the better option, as you can have the localhost app and the `amplipi.local` app in separate tabs to see the differences between what you make and what is already there, particularly if you run a fresh `scripts/deploy` when based on the `main` branch to ensure the system is at its most up-to-date first.
Please note that live Frontend development has the risk of getting your system into a bad state if you aren't careful with how you handle endpoint interactions or global state saving.

### Without an Amplipi
Without an Amplipi to use for development, you'll find yourself running everything on the local machine. Follow the above guide on [how to set up `scripts/run_debug_webserver`](#mocked-controller-with-4-stereo-audio-channels-raspberry-pi-os) and then run `scripts/run_debug_frontend` in a separate terminal to run the frontend locally using a simulated backend.

---

## Windows-Specific Setup

### Requirements
For development on Windows, you’ll need the following tools:
- Git Bash - This can be achieved in multiple ways, from running inside of WSL or downloading some form of client.
- [VSCode](https://code.visualstudio.com/) (only recommended, any text editor or IDE will do)
- [Python 3](https://phoenixnap.com/kb/how-to-install-python-3-windows) (ensure it’s set up in your PATH)

### Notes
- Windows 10+ supports mDNS for easy SSH access to AmpliPi, but Ethernet is recommended for reliability.

### Using WSL for Development
For the best development experience on Windows, we recommend using [WSL (Windows Subsystem for Linux)](https://www.microsoft.com/store/productId/9PDXGNCFSCZV?ocid=pdpshare) with mirrored networking mode. This allows WSL to share the same network interface as your host machine, making it easy to connect to AmpliPi and deploy directly from the WSL environment. Here’s how to get started:

1. Install WSL and set up a Linux distribution (Ubuntu recommended).
2. Ensure networking mode is set to mirrored by checking your WSL configuration in `.wslconfig`.
3. From WSL, follow the Linux development steps, including cloning the repository and using `scripts/deploy`.

---

## Installing AmpliPi on a Pi Compute Module

All AmpliPro units ship with AmpliPi preflashed onto their Pi controllers. For a fresh installation on a Pi Compute Module, use the following steps:

1. Run the `scripts/bootstrap-pi` script to configure the Pi.
2. Once complete, SSH should be enabled, and you can access the system at [amplipi.local](amplipi.local).

---
