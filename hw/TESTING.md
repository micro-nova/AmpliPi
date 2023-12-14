# AP1-S4Z6 (AmpliPro) Main Unit Tests

- Serial Number ____________
- Date ________ / ________ / ________  Time  ________ : ________ AM / PM
- [ ] Boards Tested (Manual - verify QC Passed sticker on each board.)

|     | Amp Board | Power Board | Preamp Board | Preout Board | LED Board | Controller Board |
|-----|-----------|-------------|--------------|--------------|-----------|------------------|
| rev |           |             |              |              |           |                  |
|  QC |           |             |              |              |           |                  |

Plug in Ethernet, Aux, Expander, RCA Inputs, Service USB, and finally Power.

- [ ] Service USB
- [ ] Config AmpliPro

**Remote Desktop Tests - Click "Test Main Unit" on Desktop - the tests found below should now be available.**

- [ ] USB Ports: ____TOP ____BOTTOM ____INT
- [ ] Ethernet
- [ ] Program Main + Exp Preamp
- [ ] LEDs:

|   | Stdby (Red) | Enabled (Green) | Zone 1 | Zone 2 | Zone 3 | Zone 4 | Zone 5 | Zone 6 |
|---|-------------|-----------------|--------|--------|--------|--------|--------|--------|
| ✓ |             |                 |        |        |        |        |        |        |

- [ ] Aux Input: ____L ____R

- [ ] Preamp:

|  Analog 1 |  Analog 2 |  Analog 3 |  Analog 4 | Zone |
|-----------|-----------|-----------|-----------|-----:|
|____L____R |____L____R |____L____R |____L____R |    1 |

| Digital 1 | Digital 2 | Digital 3 | Digital 4 | Zone |
|-----------|-----------|-----------|-----------|-----:|
|____L____R |____L____R |____L____R |____L____R |    1 |

|  An/Dig 1 |  An/Dig 2 |  An/Dig 3 |  An/Dig 4 |  Zone |
|-----------|-----------|-----------|-----------|------:|
|____L____R |____L____R |____L____R |____L____R |     2 |
|____L____R |____L____R |____L____R |____L____R |     3 |
|____L____R |____L____R |____L____R |____L____R |     4 |
|____L____R |____L____R |____L____R |____L____R |     5 |
|____L____R |____L____R |____L____R |____L____R |     6 |
|____L____R |____L____R |____L____R |____L____R |(exp) 7|

- [ ] Peak Detect (run with Preamp):

|  Input 1  |  Input 2  |  Input 3  |  Input 4  |
|-----------|-----------|-----------|-----------|
|____L____R |____L____R |____L____R |____L____R |

- [ ] Preouts:

| Preout 1 | Preout 2 | Preout 3 | Preout 4 | Preout 5 | Preout 6 |
|----------|----------|----------|----------|----------|----------|
|____L____R|____L____R|____L____R|____L____R|____L____R|____L____R|

- [ ] Display (Manual)
  - [ ] Shows an IP address (when Ethernet connected)
  - [ ] Show Disconnected (when Ethernet disconnected)

- [ ] Fans and Power:

|   | Fans Off | Fans On | PG_12V | 12V Supply | HV1 Temp | AMP1 Temp | AMP2 Temp | Temp Rise |
|---|----------|---------|--------|------------|----------|-----------|-----------|-----------|
| ✓ |          |         |        |            |          |           |           |           |
