# Presets
To allow for memorized configurations of sources and zones that can be repeated, potentially automatically, the idea of preset configurations are being discussed. The idea is a that a partial system configuration can be stored and loaded. The configuration can span across all or none of the sources, streams, zones, and groups. The configuration can be anything from a complete setup to just a configuration of a single source. During the loading any zones that are being configured will be temporarily muted before all of the changes are made.

## Loading sequence for a preset
To avoid any issues with audio coming out of the wrong speakers, we will need to carefully load a preset configuration. Below is an idea of how a preset configuration could be loaded to avoid any weirdness. We are also considering adding a "Last config" preset that allows us to easily revert the configuration changes.

1. Grab system modification mutex to avoid accidental changes (requests during this time return some error)
1. Save current configuration as "Last config" preset
1. Mute any effected zones
1. Execute any stream changes (configuration then commands)
1. Execute changes source by source in increasing order
1. Execute change zone by zone in increasing order
1. Execute changes group by group in increasing order
1. Unmute effected zones that were not muted
1. Force web client refresh to fixup website
1. Release system mutex, future requests are successful after this

## REST API additions
- POST load/# - Loads a preset, returns state after preset load completes
- GET presets - Get the list of available presets
- POST preset - Add a preset. Preset syntax is same as config file. To accomodate streams that can be connected to any available source, id-less sources are allowed. The rest of the configuration parts (zones, streams, groups) needs an associated id. Potential error state if all sources are in use (in use means that atleast one zone is unmuted and the source's input is not None). App should detect this condition and ask user which source to take over.
- PATCH presets/# - Update a preset (likely changes whole contents of the preset since partial changes will be ambiguous)

## Webapp - Preset Page view
View is a list of buttons, to load a preset user presses and holds the preset to load for X seconds until button state shows loading.
