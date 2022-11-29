## Main Controller
### Front Panel

![Controller - Front Panel](imgs/manual/front_panel_main.png)

- **DISPLAY**: Show IP Address, Hostname, and SSH Password.
- **ON/STANDBY**: Show state of the audio controller:
    - Green: Unit is on
    - Red: Unit is in Standby
    - Blinking Red: Unit is waiting to be configured
- **ZONE**: Show powered state of each zone
    - Blue: Zone is on (not muted)
    - None: Zone is off (muted)

### Rear Panel

![Controller - Rear Panel](imgs/manual/back_panel_main.png)

- **POWER**: 115V, or optionally 230V connection. See installation page for more detail.
- **CONTROLLER**: Connections to the embedded Raspberry Pi Controller.
- **SERVICE**: USB mini connection for re-imaging the Pi's EMMC.
- **USB**: USB A ports for connecting peripherals such as additional storage devices. Do not power an input using the USBs, see installation page for more info.
- **AUX IN**: Additional stereo input, planned to be used for announcements.
- **ETHERNET**: Network connection.
- **INPUTS**: 4 Stereo RCA inputs.
- **PREOUT**: Unamplified zone audio outputs, intended for powered speakers/subwoofers.
- **ZONE X**: Amplified stereo outputs for Zone X, using 4-pin Phoenix connectors.
- **EXPANSION**:
    - **CHAIN OUT**: Connection to the next expansion unit (if one or more expanders are needed).
