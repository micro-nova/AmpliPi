# Presets
To allow for memorized configurations of sources and zones that can be repeated, potentially automatically. There are two presets that ship with the box, one to mute all zones, and a dynamic preset that just returns your unit to whatever state it was in prior to the most resent preset activation.
The idea is a that a partial system configuration can be stored and loaded. The configuration can span across all or none of the sources, streams, zones, and groups. The configuration can be anything from a complete setup to just a configuration of a single source. During the loading any zones that are being configured will be temporarily muted before all of the changes are made.

## Loading sequence for a preset
To avoid any issues with audio coming out of the wrong speakers, we will need to carefully load a preset configuration. Below is an idea of how a preset configuration could be loaded to avoid any weirdness. We are also considering adding a "Last config" preset that allows us to easily revert the configuration changes.

1. Grab system modification mutex to avoid accidental changes (requests during this time return some error)
2. Save current configuration as "Restore Last Config" preset
3. Mute any effected zones
4. Execute any stream changes (configuration then commands)
5. Execute changes source by source in increasing order
6. Execute change zone by zone in increasing order
7. Execute changes group by group in increasing order
8. Unmute effected zones that were not muted
9. Force web client refresh to fixup website
10. Release system mutex, future requests are successful after this

## REST API additions
**EDIT EDIT EDIT** (I think this belongs on its own page as an "API guide", or just to leave out of the manual entirely and have the API guide just be the browsable api internal to the unit)
- POST load/# - Loads a preset, returns state after preset load completes
- GET presets - Get the list of available presets
- POST preset - Add a preset. Preset syntax is same as config file. To accomodate streams that can be connected to any available source, id-less sources are allowed. The rest of the configuration parts (zones, streams, groups) needs an associated id. Potential error state if all sources are in use (in use means that atleast one zone is unmuted and the source's input is not None). App should detect this condition and ask user which source to take over.
- PATCH presets/# - Update a preset (likely changes whole contents of the preset since partial changes will be ambiguous)
