# AmpliPi Hardware Diagrams
This directory contains hardware documents for AmpliPi as well as testing
software used to verify hardware functionality.

## Schematics
Schematic diagrams for all the boards in an AmpliPi Main Unit or Exander
are available in the [sch](sch) directory.
See [hw_releases.md](sch/hw_releases.md) for the configuration of board
revisions in each hardware release.

## Diagrams
Hardware diagrams documenting AmpliPi hardware and signal flow at a
higher-level are available in the [diagrams](diagrams) directory.

The AmpliPi Controller's boards are outlined in the following diagram:
![Controller Board Diagram](diagrams/controller_boards_diagram.drawio.svg)

The AmpliPi Zone Expander's boards are outlined in the following diagram:
![Zone Expander Board Diagram](diagrams/expander_boards_diagram.drawio.svg)

## Tests
The tests in the [tests](tests) directory are used by MicroNova to
perform hardware verification of units.
Many of the tests can be run without extra test equipment.
