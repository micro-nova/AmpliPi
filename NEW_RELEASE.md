# How to make a new release of the AmpliPi software

So you think you are ready to make a release, eh? Follow the steps below :)

## Testing
- [ ] Web App (use chrome, firefox, and safari)
  - [ ] Test group and zone volume control
  - [ ] Check that each stream type can play music
  - [ ] Test added app functionality
- [ ] Android App
  - [ ] Test added App functionality
  - [ ] Verify group and zone volumes
  - [ ] Check that each stream type can play music
- [ ] Touchscreen display
  - [ ] Verify touch turns display on
  - [ ] Verify sources and volume sliders work with app
- [ ] Expanders
  - [ ] Verify expanders are detected
  - [ ] Test expander zone volume control
- [ ] Tester
  - [ ] Update end-of-line tester with new release
  - [ ] Verify all tests function

## Versioning
This project follows [Semantic Versioning](https://semver.org/). Here are some examples of versions we've used before:
* `0.2.1`: this is a public general-availability bugfix release of the `0.2` feature release.
* `0.3.0-alpha.0` is the first alpha release of the `0.3` feature release.

## Making a release
- [ ] Ensure the PR(s) with your features & fixes are merged into `main`.
- [ ] Update the API by running `scripts/create_spec` script.
- [ ] Create & merge a branch/PR off `main` to bump the version in the CHANGELOG and also using `poetry version ${VERSION}`
- [ ] Checkout main & create a detached HEAD: `git checkout main; git pull; git checkout --detach`
- [ ] Build the webapp in `web` with `npm run build` and force add the changes with `git add -f web/dist; git commit -m "Build web app for release"`
- [ ] Tag the changes so we can make a release on GitHub: `git tag -as ${VERSION} -m '' && git push origin ${VERSION}`
- [ ] Make a release using the GitHub interface. This should be marked as a "prerelease", until all testing and QA has occurred.
- [ ] Use the AmpliPi updater to update to the release. Since this is marked as a prerelease, you will find it in the 'Older Releases' tab. Sanity check your install - did it download, install, and reboot correctly?
- [ ] Build an image using [the `micro-nova/amplipi-img-gen` suite](https://github.com/micro-nova/amplipi-img-gen). When built, upload the image, its checksums, and [GPG signatures from a key in our public keyring](https://github.com/micro-nova/micronova-keyring) to the Google Cloud Storage bucket `amplipi-img` in our GCP project named `Amplipi`.
- [ ] Pass the image and release off to QA.
- [ ] Once the image and the GitHub package have passed QA, edit the release in GitHub. Uncheck the "Prerelease" check box, and check the "Latest release" box. Congrats! The release is now live and generally available!
