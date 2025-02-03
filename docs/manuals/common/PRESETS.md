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

