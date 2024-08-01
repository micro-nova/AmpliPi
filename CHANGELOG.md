# AmpliPi Software Releases

## Upcoming Release
* Streams
  * Internet radio can now play playlists from the `pls`, `m3u8`, and `m3u` formats.
  * Fixed bug where internet radio process would not completely stop when the stream was stopped.
  * Fixed bug where internet radio process would permenantly fail during transient network errors
  * Fixed a bug where a missing logo prevents saving & showing streams
* Web App
  * Fix a bug that caused re-renders on settings modals
* Display
  * Status now displays number of playing, paused, stopped, and muted zones.
* System
  * Fixed bug where the logs would be filled with errors when startign Spotify.

## 0.4.1
* Web App
  * Migrate more inputs to MUI
  * Fix internet radio searching during stream creation
  * Download appliance config when toggling LMS mode off
  * Add hoverover effects on unselected player cards
  * Handle missing source selection
  * Autoselect newly created sources
  * Add marquee support to stream names in player view
* System
  * Reduce noisy logging from lms_metadata.py
  * Fix install of FM radio software `redsea`
  * Fix latest version checking after an update
  * Move system state out of running software directory
  * Fix updates on systems with an API password set
  * Fix the display service on systems with an API password set
* Streams
  * File Players can be temporary. A temporary File Player will remove itself from the list of available streams once disconnected from all sources.
  * File Players run their own Python container process similar to Internet Radio Stations, rather than running a cvlc command.
  * File Players can now be paused, and restarted by pressing the play button when the track ends.
* API
  * Added a play endpoint which supports playing music to a File Player remotely.

## 0.4.0
* System
  * Fix broken API generation
  * Permit continuous integration runs in the installer for automated disk image builds
  * Make udisks2-listener.service stop spamming logs on startup
* Web App
  * Enforce breakpoint styling to ensure that the UI looks the same between mobile, desktop, tablet viewports
  * Groups containing disabled zones now behave as though those zones don't exist
  * Groups containing only disabled zones no longer selectable
  * Only show not-playing streams in the new stream modal
  * Ensure that Pandora credentials are valid when adding a Pandora stream
  * Increase responsiveness of Config page
* Streams
  * Remove stop command (only accessable through API) from Pandora
  * Disconnect zones from sources when they are disabled
  * Updated Pianobar to fork of 2022.04.01
  * Reset buggy LMS clients on a regular basis
  * Improved Spotify metadata and status handling
  * Updated Spotifyd to 357e1476fd4e987b82d00ac7b70891d1730509e8
  * Rewrote MPRIS interface to no longer poll (used by spotify and airplay)
  * Fixed bug in spotify with metadata file location
  * Fixed Spotify stream field validation to permit spaces

## 0.3.6
* Web App
  * Add initial support for song browser (only Pandora stations for now)
  * Add streams to the stream list on the homepage in the order they were added
  * Add firmware version for main and expansion units on About page
  * Limit length of displayed stream names with ellipsis
  * Minor security increase to Pandora passwords
  * Add restart stream button to stream modal
  * Add dynamic scaling to controls on Player page
  * Make update available badge show up on both Settings page and the menu bar
  * Fix stream icons
  * Make it clearer when a stream needs a zone added on the home screen
* System
  * Add serial number to eink display
  * Add ability to display status on eink display
  * Better logging around failed upgrades
  * Make upgrades more stable
  * Implement opt-in remote support capabilities from the updater
  * Upgrade LMS (Lyrion Media Server, formerly Logitech Media Server)
* Display
  * Add serial number
  * Add status code field
  * Display number of expanders connected
  * Reorganize layout to accomodate more text
  * Add start-up screen to E-Ink Display
* Streams
  * Add DLNA metadata and control support
  * Add support for browsing Pandora stations
  * Make Pandora like work and pass tests without metadata race condition
  * Validate stream fields when creating or reconfiguring stream
  * Handle LMS client cleanup better
  * Upgrade LMS client, squeezelite
* API
  * Fix: Zones playing audio on source used for announcement are not muted while announcement is playing
  * Log firmware version for main and expansion units
  * Add serial number to API
  * Add list of Expanders' serial numbers to API
* Manufacturing
  * Display a QR code to the quickstart guide for initial unboxing

## 0.3.5
* Web App
  * Reverse order available sources are used in
* System
  * Add version number to config
  * Load arbitrary extra fields into /info from file
  * Fix a firmware programming bug for extenders
* LMS
  * Add metadata support
  * Add support for non-9000 ports
  * Upgrade LMS to 8.5.1
  * Automatically mount usb storage devices as media drives in LMS
* Streams
  * Revert recent Pandora changes for stability reasons

## 0.3.4
* Web App
  * Improve static asset deployment
  * Add support for mobile app only functionality
  * Fix bug where fields in stream configuration had empty descriptions
  * Better form validation on the stream addition and editing modal
  * Generate sourcemaps with every deployment
  * Replace Pandora controls (like, dislike songs)
  * Add "liked state" metadata to Pandora controls
* System
  * Add ability to display a special message for shipping on the eink display
  * Make eink display clear when the display process is stopped
  * Add support for python's logging module for better debugging
* Streams
  * Hide FM Radio if hardware is not available
  * Make pandora stream album art use HTTPS urls to make sure it is rendered in the ios app
  * Make Pandora streams a bit more robust against failure
  * Fix internet radio startup bug that caused echo
  * Fix AirPlay album art
  * Ensure Pandora streams stop when deactivated

## 0.3.3
* Web App
  * Improve functionality of configuration page
* Streams
  * Fix Spotify stream creation

## 0.3.2
* Web App
  * Fixed bug that allows disabled streams to be shown & selected
  * Close the preset modal when the preset has been executed
  * Remove Elastic APM RUM client
  * Make zeroconf advertisement more robust to ip address changes
  * Remove deprecated old zeroconf advertisement
* System
  * Manage the /boot/config.txt Raspberry Pi firmware configuration file for bugfixes
* Streams
  * Added aux input stream, a special stream that is always available and is used to select the 3.5mm input.
* Developing
  * Make `image_pi` script bail when the imaging is unsuccessful

## 0.3.1
* System
  * Fix bug between various hardware versions
* Developing
  * Fix software and hardware tests

## 0.3.0
* Streams
  * Add Bluetooth stream
  * Updates to spotifyd
* API
  * Add support for units without zones
* Testing
  * Shorten audio clips used in preamp tests
* Hardware
  * Add support for EEPROMS on boards to identify board type and revision
  * Add support for E-Ink display
* Web App
  * Completely rewritten web app using React
* System
  * Add Logitech Media Server as an optional backend

## 0.2.1
* System
  * Fix python dependencies to specific versions
* Streams
  * Fix LMS Server parameter
* Docs
  * Update 9/12V supply register descriptions

## 0.2.0
* Web App
  * Reject scroll events to volume sliders
  * Improve version display
* Streams
  * Switch to Spotifyd Spotify client
  * Add MPRIS metadata/command interface
  * Add LMS Client (no metadata yet)
  * Make Airplay use MPRIS
  * Add single Airplay2 to Airplay stream
  * Add default icon for internet radio
  * Simplify stream serialization
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
