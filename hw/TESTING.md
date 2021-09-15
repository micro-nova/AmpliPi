# Built-in Tests
## LED Board
- All on/scroll
## Preout or Amplifier Board
- 6 Zone 50% volume/mute toggle
## Preamp
- Program preamp and connected expansion board
- 4x2 sources on zone 1 (also zone 7 on expansion)
- 4 sources on all zones, toggle volume between 45 and 60%
- Poll/display 24V ADC + thermistors
## Controller
- Aux/SPDIF
- Enet (ping micro-nova.com)
### Manual (but will have instructions on screen)
- Desktop
- USB Power load
- Bootload

# AmpliPi Test Check List
## Individual Boards Tested?
Verify that each of the following boards in the assembled unit has a tested sticker.
- [ ] Led:
  - run `./scripts/built_in_test led`
  - verify each led works
    - [ ] Stdby (Red)
    - [ ] Enabled (Green)
    - [ ] Zone 1
    - [ ] Zone 2
    - [ ] Zone 3
    - [ ] Zone 4
    - [ ] Zone 5
    - [ ] Zone 6
- [ ] Power (standalone tester)
- [ ] Preamp
  - [ ] Program with latest firmware
  - run `./scripts/built_in_test preamp`
  - verify all digital/analog left and rights are played out zone 1
    - [ ] Zone 1
  - verify all digital or analog left and rights are played out the rest of the zones
    - [ ] Zone 2
    - [ ] Zone 3
    - [ ] Zone 4
    - [ ] Zone 5
    - [ ] Zone 6
- [ ] Preout
  - run `./scripts/built_in_test zones`
  - verify audio is played out each preout (left and right channels)
    - [ ] Preout 1
    - [ ] Preout 2
    - [ ] Preout 3
    - [ ] Preout 4
    - [ ] Preout 5
    - [ ] Preout 6
- [ ] Amplifier
  - run `./scripts/built_in_test zones`
  - verify audio is played out each zone (left and right channels)
    - [ ] Zone 1
    - [ ] Zone 2
    - [ ] Zone 3
    - [ ] Zone 4
    - [ ] Zone 5
    - [ ] Zone 6
- [x] Controller (this will be tested in the next step)
### Assembled Unit
- [ ] Service USB: verify filesystem is accessible through service USB.
- [ ] Desktop: Plug in mouse, keyboard, and monitor (1080p@60hz). Verify they all work.
  - [ ] Monitor
  - [ ] Top external USB
  - [ ] Bottom external USB
  - [ ] Internal USB
- [ ] Expansion connector: Run **TODO** to program an expansion unit
- [ ] Ethernet: Run `./hw/tests/ethernet.bash` and verify test passes
- [ ] Aux inputs
  - Optical In
    - run `./scripts/built_in_test zones`
    - verify audio is played out each zone (left and right channels)
  - Aux In
  - run `./scripts/built_in_test zones`
  - verify audio is played out each zone (left and right channels)
- [ ] Audio:
  - run `./scripts/built_in_test preamp`
  - verify all digital/analog left and rights are played out zone 1
    - [ ] Zone 1
  - verify all digital or analog left and rights are played out the rest of the zones
    - [ ] Zone 2
    - [ ] Zone 3
    - [ ] Zone 4
    - [ ] Zone 5
    - [ ] Zone 6
  - verify left and rights are played out each preout
    - [ ] Preout 1
    - [ ] Preout 2
    - [ ] Preout 3
    - [ ] Preout 4
    - [ ] Preout 5
    - [ ] Preout 6
- [ ] TFT Display
    - [ ] Verify AmpliPi state is shown
    - [ ] Run `./hw/tests/display.bash` and verify test passes
- [ ] Fans
  - [ ] 12V OK?
  - [ ] Verify fans spin at 100% when forced on
  - [ ] Verify room temp measurements are in the range [25, 30] degrees Celsius
  - [ ] Verify fans turn on when the amplifiers are hot by heating up a heatsink
