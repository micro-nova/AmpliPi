# Troubleshooting

If you are having problems with your AmpliPro device, start here.

## Updating

From the App
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

Manual backups are taken by navigating to Settings (gear icon) -> Config -> Download Config. This configuration includes all configured streams. These backups can be restored going to Settings -> Config -> Upload Config and selecting the downloaded config file. It is a good idea to take a manual backup before upgrading your appliance.

### Automated system backups and restores

Automated backups are also taken nightly at 2AM and stored for 90 days, and also whenever you upgrade to a newer version of software. These are raw system backups, accessible only by an advanced user via the backend. These backups help either support, or a technical user, to restore prior system configuration from a particular point in time. If the below instructions do not make sense to you, you should feel free to email [support@micro-nova.com](mailto:support@micro-nova.com) and we can help restore a backup from your appliance.

These backups are dated tarballs stored at `/home/pi/backups`. This tarball contains the entire `/home/pi/.config/amplipi` directory. To restore this backup:
1. Stop the AmpliPi service (`systemctl stop --user amplipi` as the `pi` user).
2. Unpack a backup tarball and overwrite the contents of `.config/amplipi` (something like `tar --force-local -xvzf backups/config_2024-08-22T12:42:31-04:00_pre-fw-upgrade.tgz -C /`).  Here we use `config_2024-08-22T12:42:31-04:00_pre-fw-upgrade.tgz` as an example backup file.
3. Start AmpliPi again (`systemctl start --user amplipi`).`

## Reimaging AmpliPro
For directions on how to bring AmpliPro system back to a previous version, follow this link: www.amplipi.com/reimaging. It is a good idea to take a system backup before running this process; see the above section labelled "Taking and restoring configuration backups".

## Still need help?

You can contact our support. We can be reached via email at [support@micro.nova.com](mailto:support@micro-nova.com).

### Gathering Logs

In most cases, the first thing that our support techicians will ask you for is to send us your system logs. These logs are wiped out on system reboot, so when possible try to collect them whenever an issue occurs _before_ rebooting your device.
Logs can be reached by going to Settings -> About -> Logs, or by navigating directly to `http://{Device_IP}:19531/entries`. Once you reach this page, you can either copy and paste the logs into your email, or hit control+S to save them to a file that you can attach to your email.

### Support Tunnel

We may ask you to open a support tunnel so we can connect to your running appliance. When you request a tunnel, the web interface will generate and provide you with two pieces of information - the tunnel ID and a preshared key. Without these pieces of information, we are _incapable_ of connecting to your appliance. Additionally, a support tunnel can be stopped at any time and has an expiration date of 2 weeks after it was created. This is for your privacy and security.

You can request a tunnel by following these steps:

1. Click the gear icon in the bottom right corner to go to the configuration page
2. Select **Updates**, and click the **Support Tunnel** Tab
3. Click the **Request support tunnel** button. It may 60 seconds for the request to complete.
4. Once the request has been created, this page provides you with the tunnel ID and a preshared key. Please provide both of these to our support personnel in your communications.
