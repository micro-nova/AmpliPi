# Installation
## Overview
It's time to power on your AmpliPro and try it out. To avoid damaging the unit, please read through this guide before installing and powering your AmpliPro unit!
\
\
 **WARNING!! VERIFY THAT THE VOLTAGE OF YOUR WALL OUTLET MATCHES THE VOLTAGE LISTED NEAR THE POWER INLET BEFORE PLUGGING IN. IF THE VOLTAGE IS NOT MATCHED, PLEASE CONTACT US AT support@micro-nova.com**

## Mounting and Placement

Main Controllers and Zone Expanders both ship with built-in 19" rackmount ears, so that they can be easily installed into a server rack.
Both the main and expansion units are approximately 15 pounds (6.8 kilograms)

Some things to keep in mind to avoid overheating the unit:
- Don't block the vent holes on the side
- Don't allow dust to build up inside the unit. See cleaning instructions on the safety page for more details.


## Speakers
Each of AmpliPro's zones has two speaker outputs that drive a 4-8 Ohm speaker, using the provided Euroblock connectors. Here is what the basic wiring diagram for a zone looks like:

![Speaker wiring](imgs/zone_speaker_wiring.png)

AmpliPro's amplifiers are capable of driving 4-8 Ohm speaker loads. Here is what a typical stereo speaker connection, using CL2-rated 14-AWG speaker wire and the Euroblock connectors, looks like:

![Euroblock connector connection](imgs/euroblock_example.jpg)

To connect a stereo speaker pair using speaker wire:

1. Strip 3-4 inches of the cable jacket, then strip 1/4 inch of insulation from the end of each wire.
2. Twist the frayed end of each wire.
3. Please note that the wiring diagram (the image with four green squares wired to two speakers) shows polarity, not necessarily the colors of the wires. Make sure you connect positive to positive and negative to negative while also keeping the left and right channels separated into their own speakers.
4. Unscrew each set screw to open the contacts, then insert and tighten down each wire one by one. Note that set screws loosen, but should not come out.
5. To avoid any shorts, make sure that there aren't any stray wire strands.
6. The speaker set can now be connected to one of the 6 zones.

### Connections
- Improper connection of speakers can damage the unit
- Never connect multiple speakers in parallel such that it brings the total impedance below 4 ohms (max 2x 8ohm speakers in parallel).
- Amplified speaker outputs **CAN NOT** be bridged, attempting to do so will damage the amplifier and void the warranty

### Running wire in walls and ceilings
- Most electric codes require the use of CL2-rated speaker wires for in-wall installations. Please refer to local building codes for more details.
- Avoid running speaker wires next to AC power wires as much as possible to reduce noise.
- When necessary, cross AC wires at 90-degree angles to avoid introducing any noise into the speakers.

### More Info

More information on speaker selection and installation can be found in AmpliPro’s community forums that can be reached from the system settings, simply click on "About", then the "Community" link and see the "Installation and Getting Started" topic on our discourse group, also accessible at amplipi.discourse.group.

## Preamp Outputs
Each of AmpliPro's zone outputs has a corresponding line-level RCA output pair. These outputs can be used to connect powered subwoofers and other active/powered speakers.

The volume output of a preout is controlled by the corresponding speaker output. This allows a connected subwoofer to be controlled proportionally to the speaker's output in the same zone.

## Audio Inputs
Each of the stereo RCA inputs can be connected to a different audio source, such as the output of a TV or other compatible device. See device specifications page for further information.

## Expansion Units
To increase the number of zones you can add expansion units to your system. You can add up to 5 additional zone expander units to a single AmpliPro main unit. Each expansion unit adds 6 zones or pairs of speakers. Zones attach to main units using the CHAIN IN/OUT connectors on the rear panel.

## Network connection
Connect an RJ45 cable to the Ethernet port on the main unit. Connect the other end to a port on your main network (likely on your router). The unit's IP address is configured by DHCP.

## Power
**WARNING!! VERIFY THAT THE VOLTAGE OF YOUR WALL OUTLET MATCHES THE VOLTAGE LISTED NEAR THE POWER INLET.**

AmpliPro ships preconfigured for the typical mains voltage in your region, either 120V mains power or 230V mains; to see what mode it was set to before shipment, check which hole near the power inlet has a plastic peg/screw. If your unit is preconfigured incorrectly for your region, please contact us at **support@micro-nova.com**
\
Once you've ensured that the unit has the correct input voltage configured, plug the AmpliPro into a wall outlet. The ON/STANDBY will start off blinking red and then transition to solid red once the unit is fully powered on. Continue below to enjoy your unit!

## Startup and Configuration
Now that the AmpliPro unit is powered on, it's time to use the software. To access the app, there are two options:

### Mobile App

1. We offer mobile apps available on Android and iOS, simply search for "Amplipi" on the Google Play Store or Apple's App Store or go to the Links page at the start of this manual for QR codes for each version
2. Once you have the app downloaded, permit the app to access devices on your local network. The app will automatically search your network for active AmpliPro units.
3. If you have multiple controllers, it will ask which unit you wish to connect to. We suggest giving different hostnames to each unit if you have multiple controllers on the same network for this reason.

### Webapp

1. Simply enter "amplipi.local" into a web browser, on any device that both has a web browser and is connected to the same network. Android and Windows 7 users will need to type the IP address found on the unit's display into their web browser instead.


### From the app:

1. Click the plus (+) icon and select a stream
    - The Groove Salad - InternetRadio stream comes preconfigured (needs an internet connection).
2. Change the volume on the zone you would like to output music on. Zones may be hidden inside a group. Click on the different groups to see which zones belong to them.
3. If you wish to change the default zone names or add different streams, click on the gear icon on the bottom right to reach the settings page where you can configure zones and streams.
