This PR has revamped AmpliPi updates by entirely redesigning the partition structure of the system as well as the actual update flow.

# What's changed in the underlying system?

The old partition schema involved two partitions, boot and root, the same as most any linux system around; this new schema involves 7 partitions:

P1 (Autoboot): This partition contains [autoboot.txt](../config/autoboot.txt) and a linux kernel, it is the partition that is read by the RPi's firmware at the start of the boot process to decide which slot to boot into.
P2 (Boot A): The boot partition for slot A, contains everything a boot partition typically has (including a mapping to the related root, P5).
P3 (Boot B): The boot partition for slot B. The same contents as P2, but with mappings for P6.
P4 (extended): An extended partition, required due to RPi only supporting 4 "main" partition types. Contains P5, P6, and P7.
P5 (Root A): The root partition for slot A. Contains a full AmpliPi install and raspbian trixie OS.
P6 (Root B): The root partition for slot B. Contains a full AmpliPi install and raspbian trixie OS.
P7 (data): The shared data partition for the slots to persist data with, mounted in both slots as /data via fstab and contains the amplipi .config folder, LMS install, SSH host keys, a folder for user-created post update configuration scripts, and is also where updates are staged. The OS data that is persisted here is symlinked from both slots.

# What's changed with updates specifically?

Updates come in two forms: Full and Delta. All update packages contain a manifest.json, telling the updater what type of update they are, what version they are, where to get the related update files, and a few other things depending on the version

When you update, you update from the active slot to the inactive slot, then restart the system using `sudo reboot '0 tryboot'`, a standard reboot but with an arg that tells the bootloader to use the [tryboot] section of [autoboot.txt](../config/autoboot.txt). When the system reboots, it runs some post-boot, pre-amplipi checks using the [update commit service](../scripts/amplipi-tryboot-verify.service) (and [accompanying bash script](../scripts/amplipi-tryboot-verify.sh)) that then edits autoboot.txt in p1 to set the new slot to the default (non-tryboot) slot should the update prove successful. If the update isn't successful, it automatically reboots back to the original slot. If those post-boot checks never run due to something being broken, the [amplipi-boot-deadline service](../scripts/amplipi-boot-deadline.service) (and [related bash script](../scripts/amplipi-boot-deadline.sh)) revert to the good slot after a short timer that begins on system boot and is cancelled by the commit service's checks passing.
If something somehow is so screwed up that the OS can't even boot, the RPi bootloader should have some controls to correct for that and return to the known good slot as well, but we also sincerely should not ever reach that point if we're doing our due diligence with testing and release creation.


## Full Image Updates

Full Image `manifest.json`:

``` json
{
  "version": "0.5.0",
  "type": "full",
  "root": {"sha256": "(LONG STRING OF CHARS)", "size": 123456789, "url": "{fileserver domain}/050/root.img.xz"},
  "boot": {"sha256": "(LONG STRING OF CHARS)", "size": 1234, "url": "{fileserver domain}/050/boot.img.xz"}
}
```

A full update is when we image the inactive slot with updated code, ideally saved for when we change the underlying services or linux state of the system. These take about an hour to complete depending on the user's internet speed

A full update always contains a root image, and sometimes contains a boot image. These are downloaded, verified against the related sha256 checksum and bytesize values included in `manifest.json`, and then flashed if everything matches up. After flashing, the system reboots into the freshly updated slot before setting that slot to be the new default (assuming the previously mentioned post-boot checks succeed)

## Delta Updates

Delta `manifest.json`:

``` json
{
  "version": "0.4.12",
  "type": "delta",
  "min_base_version": "0.4.11"
}
```

A delta update is a simpler update, but slightly more fragile. While a full update doesn't care about what's on the inactive slot due to expecting to blow it all away, the delta update changes the existing files rather than authoritatively setting the partition state. As such, these updates are version gated by a `min_base_version` value that contains the version number of the most recent previous full image update. If the inactive slot's version is under that value, the updater will first download and flash that update to the inactive slot before handling the delta update.

The name "delta update" is a slight misnomer, as there's no file delta calculations involved - this is just an industry standard name for this update type (as seen by [Android having the same verbiage](https://source.android.com/docs/core/ota/ab/ab_implement)). What it actually does is download the github source tarball, much like our current update structure does, but instead of running the `configure.py` script and set all sorts of system state, we just use `rsync` to make sure the file contents are the same as the installed tarball before rebooting into the updated slot

## How are updates made?

See our [new release doc](../NEW_RELEASE.md) for a higher quality explanation, but here's a quick rundown:

### Delta Releases

Delta releases are similar to our previous update scheme, but instead of simply installing a tarball and self-applying with the configure script we first install a manifest.json for validation's sake, then download the tarball and rsync it to the inactive slot. If the inactive slot's version is under the `min_base_version` floor, a flash to that version happens automatically before the delta is applied. the `manifest.json` is made by by running `./scripts/make_delta_manifest {RELEASE_VERSION} {MIN_BASE_VERSION}`.

### Full Image Releases

Full Releases are a bit more complicated - firstly, they need to be hosted on our fileserver. Secondly, instead of just making a tarball on Github we have to take a snapshot of a dev unit, which demands we first wipe one of that unit's slots to ensure we have a clean basis without any dev crumbs (unneeded/abandoned services, unnecessarily mutated files) getting into our release. This means we do a slot wipe, fresh OS install, fresh deployment, and then take an image of the freshly made slot before creating the manifest.json and putting the manifest on Github along with the actual images on the hosting location.
This is a lot of work, which has caused multiple scripts ([make_image_manifest](../scripts/make_image_manifest), [make_images](../scripts/make_images), [build_golden_slot](../scripts/build_golden_slot), [make_update](../scripts/make_update)) to handle each step, but further I've created [one script to do the whole thing](../scripts/make_golden_release). This is run very simply, it gets pointed to a live unit in the same way the deploy script is and then it takes the SSH password once and goes on its way. This process takes a little over an hour.

### Initial Release

There will be one rip-off-the-bandaid style pain period with this migration. The existing units in the field don't have the ability to edit their own partitions safely, so there's no real way to make the migration automated for the end user. The intent for this migration is to make a progenitor image that contains everything from a new system other than one of the slots (which will be left empty for the sake of saving space on the image and time in the imaging process) and have users flash their devices themselves (or send them to us to do so, if necessary).

For this purpose, [make_progenitor](../scripts/make_progenitor) builds this image. It does *not* repartition a blank disk from scratch - an earlier version did exactly that (`build_golden_slot`'s own local/USB mode, live `parted`+`mkfs`+`rsync` over a USB rpiboot mass-storage connection), but it was found to be inconsistent and error prone. To account for this, the progenitor script starts by imaging the unit with an extremely lightweight partitioning image, then goes through the steps of installing the fresh `raspbian trixie lite` OS to one of the slots and configuring AmpliPi before taking an image of the full disk. The progenitor script leaves boot slot B empty to save some space and installation time, as the updater is fully capable of flashing an empty slot with a boot+root image pair without issue.

This takes time and requires a little babysitting as the system needs to go live and be remounted once or twice for the existing scripts to work, but it provides a good image that we will not need to generate again (unless we want to make a progenitor every major revision, which could be useful)
