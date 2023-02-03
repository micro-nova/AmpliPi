# AmpliPi Software Releases

## 0.1.X Upcoming
* web App
  * Reject scroll events to volume sliders
  * Improve version display
* Streams
  * Simplify stream serialization
  * Switch to Spotifyd Spotify client
  * Add MPRIS metadata/command interface
  * Add LMS Client
  * Make Airplay use MPRIS
  * Add single Airplay2 to Airplay stream
  * Add default icon for internet radio
* API
  * Robustify config loading
  * Make RCA inputs look like streams
  * Make zones removable

## 0.1.9
* Web App
  * Add link for text log
  * Add shutdown and reboot buttons in Settings->Configuration and Reset
  * Add factory reset button in Settings->Configuration and Reset
* API
  * Add `api/shutdown` and `api/reboot` endpoints
  * Add `api/info` endpoint for version, release, and other system information
* Storage
  * Only log to RAM, drastically reducing disk writes
  * Use ram disks for temporary stream configration and metadata storage
* Streams
  * Fix stream creation issue, when no streams exist
* Docs
  * Use latest rapidoc viewer, fixes several api rendering issues
* Updates
  * Upgrade system packages on update
* System Status
  * Detect if internet access is available (check 1.1.1.1 every 5 mins)
  * Check in the background for available updates (once per day)
* Developing
  * Show git hash and branch info for tests deployed by scripts/deploy
* Hardware
  * Updated to Preamp Board firmware 1.6: support high-power AmpliPi units.
* Front-Panel Display
  * Fix bug that caused volumes to not display

## 0.1.8
* Web App
  * Add consistent play/pause/prev/next controls
  * Per zone min and max volume configuration, make it easy to restrict volume levels in a room or not blast the music accidentally
  * Add internet radio search (thanks @kjk2010)
  * Fix misc settings bugs
  * Cache on version to force js/css update on refresh
* API
  * 0.0 to 1.0 volume controls (using vol_f)
  * Sources report the commands currently supported (play/pause/...)
* Streams
  * Add Play/Stop functionality to internet radio
  * Make internet radio retry on failure
  * Fix internet radio lockup condition
* Audio
  * Reduce the chance of audio pops during volume changes
  * Make the preouts mute when a zone is muted
* Security
  * If the password for the `pi` user is still `raspberry`, a new random password will be set
    and stored in ~/.config/amplipi/default_password.txt.
  * Newly shipped AmpliPi units will have a random password set already.
  * If this default password is still in use, it will be shown on the front-panel display.
    Otherwise the display will show "User Set".
  * It is still recommended to change this password using the `passwd` utility since the default
    password is saved in plain-text.

## 0.1.7

* Audio
  * All 4 DACs connected to the Raspberry Pi now output the same volume.
* Web App
  * Improved mDNS/zeroconf service advertisement (will help with mobile apps currently under development).
  * Simplified initial configuration.
  * Renamed the Shairport stream to AirPlay.
  * Added link to community forums.
* Documentation
  * Added better web app documentation and updated examples.
  * Improved high-level hardware diagrams and updated them to match the shipped hardware.
  * Added new hardware schematics and changelogs.
* Updater
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
