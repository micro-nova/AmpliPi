# How to make a new release of the AmpliPi software

So you think you are ready to make a release, eh? Follow the steps below :)

## Making a prelease
- [ ] Merge main into develop
- [ ] Make a branch off develop called VERSION-prelease
- [ ] Update the changelog with notes and the latest version (and commit it!)
- [ ] Update the API by running the `scripts/create_spec` script and commit the resulting changes to `docs/amplipi_api.yaml` with `git commit --patch -m "Update API specification used by GitHub Pages"`
- [ ] Use poetry to bump the version with `poetry version ${VERSION}-alpha.0 && git add pyproject.toml && git commit -m "Bump pre-release version"`
- [ ] Tag the changes so we can make a pre-release on GitHub `git tag -as ${VERSION}-alpha.0 -m '' && git push --follow-tags`
- [ ] Make a pre-release using the GitHub interface
- [ ] Use the AmpliPi updater to update to the pre-release
- [ ] Test it (see below), if it needs changes follow the steps above again but stay on the pre-release branch and increment the number after alpha eg `alpha8`
- When it works skip below to [Finalizing the release](#finalizing-the-release)

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

## Finalizing the release
Alright so the release is tested and it actually works! Nice!
- [ ] merge the prerelease branch into develop and merge that into the main branch
- [ ] use poetry to bump the version `poetry version ${VERSION} && git add pyproject.toml && git commit -m "Bump release"`
- [ ] use git to delete any prelease tags `git push origin -d $(git tag -l '${VERSION}-alpha*') && git tag -d $(git tag -l '${VERSION}-alpha*')`
- [ ] Tag the changes so we can make a release on GitHub `git tag -as ${VERSION} -m '' && git push --follow-tags`
- [ ] Make a release using the GitHub interface, add notes from the CHANGELOG.md
- [ ] Make a new Raspberry Pi image to program onto units before shipping.
