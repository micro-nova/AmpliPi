# How to make a new release of the AmpliPi software

So you think you are ready to make a release, eh? Follow the steps below :)

## Making a prelease
- [ ] Merge main into develop
- [ ] Make a branch off develop called VERSION-prelease
- [ ] Update the changelog with notes and the latest version (and commit it!)
- [ ] Use poetry to bump the version with `poetry version ${VERSION}-alpha0 && git commit -m "Bump pre-release version`
- [ ] Tag the changes so we can make a pre-release on GH `git tag ${VERSION}-alpha0 && git push --tags`
- [ ] Make a pre-release using the GH interface
- [ ] Use the AmpliPi updater to update to the pre-release
- [ ] Test it (See below), if it needs changes follow the steps above again but stay on the pre-release branch and increment the number after alpha eg `alpha8`
- When it works skip below to #Finalizing the release

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
  - [ ] Verify volume sliders work with app

## Finalizing the release
Alright so the release is tested and it actually works! Nice!
- [ ] merge the prerelease branch into develop and merge that into the main branch
- [ ] use poetry to bump the version `poetry version ${VERSION}` && `git commit -m "bump release"`
- [ ] use git to delete any prelease tags `git push --delete-tags ${VERSION}-alpha*`
- [ ] Tag the changes so we can make a release on GH `git tag ${VERSION} && git push --tags`
- [ ] Make a release using the GH interface, add notes from the CHANGELOG.md
