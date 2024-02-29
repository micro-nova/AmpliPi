## Main Controller
### Front Panel

![Controller - Front Panel]( imgs/front_panel_main.png)

- **DISPLAY**: Show IP Address, Hostname, and SSH Password.
- **ON/STANDBY**: Shows the state of the audio controller:
    - Green: The unit is on
    - Red: The unit is on Standby
    - Blinking Red: The unit is updating / booting
- **ZONE**: Shows the power state of each zone
    - Blue: Zone is on (not muted)
    - None: Zone is off (muted)

### Rear Panel

![Controller - Rear Panel]( imgs/back_panel_main.png)

- **POWER**: 115V, or optionally 230V connection. See the installation page for more details.
- **CONTROLLER**: Connections to the embedded Raspberry Pi Controller.
    - **SERVICE**: USB mini connection for re-imaging the Pi's EMMC.
    - **USB**: USB A ports for connecting peripherals such as additional storage devices. Do not power a device plugged into the RCA inputs using the USBs, see the installation page for more details.
    - **AUX IN**: Additional stereo input, planned to be used for announcements.
    - **ETHERNET**: Network connection.
- **INPUTS**: 4 Stereo RCA inputs.
- **PREOUT**: Unamplified zone audio outputs, intended for use with powered speakers/subwoofers.
- **ZONE X**: Amplified stereo outputs for Zone X, using 4-pin euroblock connectors.
- **EXPANSION**:
    - **CHAIN OUT**: Connection to the next expansion unit (if one or more expanders are needed).
