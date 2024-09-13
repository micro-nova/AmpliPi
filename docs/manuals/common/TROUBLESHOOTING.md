# Troubleshooting

If you are having problems with your AmpliPro device, start here.

## Audio

### Noise
Audio noise can have a lot of causes, below are some common reasons:
* **Mixing grounds**: AmpliPro has two different grounded lines, analog and digital. The most common way to mix them is by plugging in an audio device and attempting to power it with the USB on the rear of the unit, all USB-powered devices must be powered from a wall outlet
* **Speaker setup**: Some speaker configurations can lead to excess noise being inducted into the output. This is unrelated to the system and has everything to do with how the speakers are wired and installed.
* **Hardware issues**: See the support page for more info.

### No Audio
Lack of audio typically has one of a few causes:
* **No Source / Bad Source**: The source itself isn't outputting audio properly, try changing to a different source to confirm
* **Bad Output / Bad Zone**: Either the speaker, the speaker wires, or one of the ports on the back of the AmpliPro might be broken or hooked up incorrectly. Try a different speaker, length of wire, or port on the back of the AmpliPro to test each case

## Updating

From the app:
1. Click the gear icon in the bottom right corner to go to the configuration page
2. Select **Updates** and click the **Check for Updates** button

Without the app:
1. Collecting the IP from the front display of your AmpliPro unit
2. Navigating to `http://{Device_IP}:5001/update`

### New Release
To update your AmpliPi software to the latest version:

3. Click the **Update** button

### Prereleases and using previous versions
Had an issue with an update? Want to try a beta release? Follow these steps:

3. Click the **Older Releases** tab
4. Select the release you would like to use from the dropdown menu
5. Click the **Start Update** button

## Taking and restoring configuration backups

There are two ways configuration backups are made - manually through the frontend, and nightly within the backend via a scheduled job.

### Manual backups and restores

Manual backups are taken by navigating to ⚙ -> Config -> Download Config. This configuration includes all configured streams. These backups can be restored using ⚙ -> Config -> Upload Config. It is a good idea to take a manual backup before upgrading your appliance.

### Automated system backups and restores

Automated backups are also taken nightly at 2AM and stored for 90 days, and also whenever you upgrade to a newer version of software. These are raw system backups, accessible only by an advanced user via the backend. These backups help either support, or a technical user, to restore prior system configuration from a particular point in time. If the below instructions do not make sense to you, you should feel free to email [support@micro-nova.com](mailto:support@micro-nova.com) and we can help restore a backup from your appliance.

These backups are dated tarballs stored at `/home/pi/backups`. This tarball contains the entire `/home/pi/.config/amplipi` directory. To restore this backup:
1. Stop the AmpliPi service (`systemctl stop --user amplipi` as the `pi` user).
1. Unpack a backup tarball and overwrite the contents of `.config/amplipi` (something like `tar --force-local -xvzf backups/config_2024-08-22T12:42:31-04:00_pre-fw-upgrade.tgz -C /`).  Here we use `config_2024-08-22T12:42:31-04:00_pre-fw-upgrade.tgz` as an example backup file.
1. Start AmpliPi again (`systemctl start --user amplipi`).`

## Reimaging AmpliPro
For directions on how to bring AmpliPro system back to a previous version, scan the QR labeled "Reimaging Instructions" on the links page at the start of this manual, or [click this link](https://github.com/micro-nova/AmpliPi/blob/main/docs/imaging_etcher.md). It is a good idea to take a system backup before running this process; see the above section labelled "Taking and restoring configuration backups".

## Still need help?

You can contact our support. We can be reached via email at [support@micro.nova.com](mailto:support@micro-nova.com).

We may ask you to open a support tunnel so we can connect to your running appliance. When you request a tunnel, the web interface will generate and provide you with two pieces of information - the tunnel ID and a preshared key. Without these pieces of information, we are _incapable_ of connecting to your appliance. Additionally, a support tunnel can be stopped at any time and has an expiration date of 2 weeks after it was created. This is for your privacy and security.

You can request a tunnel by following these steps:

1. Click the gear icon in the bottom right corner to go to the configuration page
2. Select **Updates**, and click the **Support Tunnel** Tab
3. Click the **Request support tunnel** button. It may 60 seconds for the request to complete.
4. Once the request has been created, this page provides you with the tunnel ID and a preshared key. Please provide both of these to our support personnel in your communications.
