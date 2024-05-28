# AmpliPi Hardware Info

This directory contains hardware documents for AmpliPi as well as testing
software used to verify hardware functionality.

## Diagrams

Hardware diagrams documenting AmpliPi hardware and signal flow at a
higher-level are available in the [diagrams](diagrams) directory.

The AmpliPi Controller's boards are outlined in the following diagram:
![Controller Board Diagram](diagrams/controller_boards_diagram.drawio.svg)

The AmpliPi Zone Expander's boards are outlined in the following diagram:
![Zone Expander Board Diagram](diagrams/expander_boards_diagram.drawio.svg)

## Schematics

Schematic diagrams for all the boards in an AmpliPro Main Unit, Expanders,
and Streamers are available in the [sch](sch) directory.
See [hw_releases.md](sch/hw_releases.md) for the configuration of board
revisions in each hardware release.

## Tests

The tests in the [tests](tests) directory are used by MicroNova to
perform hardware verification of units.
Many of the tests can be run without extra test equipment.

The set of tests run during checkout are documented with test sheets.
Each unit type has its own set of tests:

* [Main Units (AP1_S4Z6)](test_ap1_s4z6.tex)
* [Zone Expanders (AP1_Z6)](test_ap1_z6.tex)
* [Streamers (AP1_S4)](TESTING_STREAMER.md)

And individual boards have their own set of tests
before being put into a final assembly:

* [BOARD_TESTS.md](BOARD_TESTS.md)

To generate a PDF from the LaTeX files, first install `texlive` with

```sh
sudo apt install texlive-latex-base texlive-latex-extra
```

then from the same directory as the `.tex` file run

```sh
pdflatex FILE.tex
```

replacing FILE.tex with the LaTeX file you want to build.
