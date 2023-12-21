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
- [ ] Create & merge a branch/PR off `main` to bump the version in the CHANGELOG and also using `poetry version ${VERSION}`
- [ ] Create another branch off `main` named the version number (ie, `0.3.0`.)
- [ ] Build the webapp in `web` with `npm run build` and force add the changes with `git add -f web/dist; git commit -m "Build web app for release"`
- [ ] Update the API by running the `scripts/create_spec` script and commit the resulting changes to `docs/amplipi_api.yaml` with `git commit --patch -m "Update API specification used by GitHub Pages"`
- [ ] Tag the changes so we can make a release on GitHub: `git tag -as ${VERSION} -m '' && git push origin ${VERSION}`
- [ ] Make a release using the GitHub interface
- [ ] Remove the branch (but not the tag) from Github, or else the ref is ambiguous to Github and the updater fails to download the right tarball.
- [ ] Use the AmpliPi updater to update to the release
- [ ] Test it again! If it needs changes, pull request your bugfixes against `main` and stamp a new release 😎
