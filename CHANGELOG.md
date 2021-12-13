# AmpliPi Software Releases

## 0.1.7

* Audio
  * All 4 DACs connected to the Raspberry Pi now output the same volume.
* Web App
  * Improved mDNS/zeroconf service advertisement (will help with mobile apps currently under development).
  * Simplified initial configuration.
  * Renamed the Shairport stream to AirPlay.
  * Added link to community forums.
* Documentation:
  * Added better web app documentation and updated examples.
  * Improved high-level hardware diagrams and updated them to match the shipped hardware.
  * Added new hardware schematics and changelogs.
* Updater:
  * Show up-to-date status.
  * Update directly from releases on Github.
  * Programs latest firmware.
* Hardware
  * Updated to Preamp Board firmware 1.4: support linear voltage fan control on new hardware.
  * Auto-add new zones if a new Expansion Unit is detected.

## 0.1.6

* Web App
  * Added stream/input, zone, and group configuration interface.
  * Added load/save configuration (and hw reset).
  * Automated Plex account connection/authorization.
  * Added mDNS/zeroconf advertisement for amplipi-api service.
* Streams
  * Added Spotify Metadata using Vollibrespot.
  * Added FMRadio stream (requires USB Receiver).
* API
  * Added album art endpoint for rendering custom album art sizes (/api/sources/{sid}/image/{height}).
  * Moved stream.info to source.info so analog inputs have info as well.
  * Added endpoint for PA Style Announcements (api/announce).
* Hardware
  * Updated schematics and hardware info for developer units.
  * Added production and built in tests.
  * Updated to Preamp Board firmware 1.3: added PWM fan control for new hardware.
