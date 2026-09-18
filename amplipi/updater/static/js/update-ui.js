  /*
   * Some helper functions to work with our UI and keep our code cleaner
   */

// Adds an entry to our debug area
function ui_add_log(message, color)
{
  var d = new Date();

  var dateString = (('0' + d.getHours())).slice(-2) + ':' +
    (('0' + d.getMinutes())).slice(-2) + ':' +
    (('0' + d.getSeconds())).slice(-2);

  color = (typeof color === 'undefined' ? 'muted' : color);

  var template = $('#debug-template').text();
  template = template.replace('%%date%%', dateString);
  template = template.replace('%%message%%', message);
  template = template.replace('%%color%%', color);

  $('#debug').find('li.empty').fadeOut(); // remove the 'no messages yet'
  $('#debug').prepend(template);
}

// Updates a file progress, depending on the parameters it may animate it or change the color.
function ui_multi_update_file_progress(id, percent, color, active)
{
  color = (typeof color === 'undefined' ? false : color);
  active = (typeof active === 'undefined' ? true : active);

  var bar = $('#uploaderFile' + id).find('div.progress-bar');

  bar.width(percent + '%').attr('aria-valuenow', percent);
  bar.toggleClass('progress-bar-striped progress-bar-animated', active);

  if (percent === 0){
    bar.html('');
  } else {
    bar.html(percent + '%');
  }

  if (color !== false){
    bar.removeClass('bg-success bg-info bg-warning bg-danger');
    bar.addClass('bg-' + color);
  }
}

function ui_begin_update() {
  // setup SSE events, for intermediate step info
  var source = new EventSource("update/install/progress");
  source.onmessage = function(event) {
    var data = JSON.parse(event.data);
    ui_show_update_progress(data);
    if (data.type == 'success' || data.type == 'failed') {
      source.close();
      if (data.type == 'success') {
        ui_reboot_app();
      } else {
        ui_show_failure();
      }
    }
  };
  fetch("update/install").catch( err => {
    ui_add_log('Error starting installation: ' + err.message, 'danger');
    ui_show_failure();
  });
}

function ui_reboot_app() {
  // initiate a reboot
  fetch("update/restart").then(function (response) {
    if (response.ok) {
      ui_add_log('Restarting AmpliPi Update server to finish update', 'info');
      setTimeout(ui_check_after_reboot, 5000, 2 * 60 / 5 - 1); // wait for 2 minutes just in case we ever have to restart the pi
    } else {
      ui_add_log('Error restarting update server: ' + response, 'danger');
      ui_show_failure();
    }
  }).catch( err => {
    ui_add_log('Error restarting update server: ' + err.message, 'danger');
    ui_show_failure();
  })
}

function ui_check_after_reboot(retry_check_ct) {
  // check reported version
  r = fetch("update/version").then(function (response) {
    response.json().then(function(json) {
      ui_add_log(json.version, 'info');
      ui_add_log('Done restarting updater', 'info');
      // No longer forcibly sends user back to amplipi home screen due to multi step
      // (full -> delta) updates seeming like a device issue when the second half completed
      ui_show_done();
    }).catch( err => {
      if (retry_check_ct > 0) {
        setTimeout(ui_check_after_reboot, 5000, retry_check_ct - 1); // don't continue to retry forever
        ui_add_log('Waiting for the updater to start', 'info');
      } else {
        ui_add_log('Error checking version: ' + err.message, 'danger');
        ui_show_failure();
      }
    });
  }).catch( err => {
    if (retry_check_ct > 0) {
      setTimeout(ui_check_after_reboot, 5000, retry_check_ct - 1); // don't continue to retry forever
      ui_add_log('Waiting for the updater to start', 'info');
    } else {
      ui_add_log('Unable to communicate with New updater: ' + err.message, 'danger');
      ui_show_failure();
    }
  });
}

// Translate the backend messages into consumable percentages for the progress bar
const UPDATE_PROGRESS_RE = /^(.+): (\d+(?:\.\d+)?)%$/;

// Phases shown on the progress bar - varies with whether this run needs a download first
// (see DOWNLOAD_THEN_FLASH_PHASES_* below) and whether the update includes a boot image.
const FLASH_PHASES_WITH_BOOT = ['Verifying root image', 'Verifying boot image', 'Flashing root', 'Flashing boot'];
const FLASH_PHASES_ROOT_ONLY = ['Verifying root image', 'Flashing root'];
// Same as FLASH_PHASES_WITH_BOOT/ROOT_ONLY, with download segments prepended - without them the
// bar sits still for however long the download takes before flashing even starts.
const DOWNLOAD_THEN_FLASH_PHASES_WITH_BOOT = ['Downloading root image', 'Downloading boot image'].concat(FLASH_PHASES_WITH_BOOT);
const DOWNLOAD_THEN_FLASH_PHASES_ROOT_ONLY = ['Downloading root image'].concat(FLASH_PHASES_ROOT_ONLY);
// The three percentage-bearing steps of a delta update (no images involved at all). Weighted,
// not equal thirds - the manifest is a few hundred bytes and takes no perceptible time next to
// the other two, so an equal share would make the bar sit idle through most of that segment.
const DELTA_PHASES = [
  {label: 'Downloading manifest', weight: 1},
  {label: 'Downloading release', weight: 4},
  {label: 'Applying update', weight: 3},
];
let flashPhases = FLASH_PHASES_ROOT_ONLY;
let boldLabelEl = null;

// Accepts a plain label string (equal weight) or {label, weight} (e.g. DELTA_PHASES) - assigns
// each phase its [start, start+segment) range along the bar, cached so per-message lookups are cheap.
function normalize_phases(phases) {
  let withWeights = phases.map((p) => typeof p === 'string' ? {label: p, weight: 1} : p);
  let totalWeight = withWeights.reduce((sum, p) => sum + p.weight, 0);
  let offset = 0;
  return withWeights.map((p) => {
    let segment = (p.weight / totalWeight) * 100;
    let withRange = {label: p.label, segment: segment, start: offset};
    offset += segment;
    return withRange;
  });
}

function ui_update_progress_bar(message) {
  let match = message.match(UPDATE_PROGRESS_RE);
  if (!match) return;
  let label = match[1];
  let pct = parseFloat(match[2]);
  let phase = flashPhases.find((p) => p.label === label);
  if (!phase) return;
  let overall = phase.start + (pct / 100) * phase.segment;
  let bar = $('#update-progress-bar');
  bar.css('width', overall + '%').attr('aria-valuenow', overall).text(Math.round(overall) + '%');
  bar.toggleClass('bg-info', label.indexOf('Verifying') === 0 || label.indexOf('Downloading') === 0);
  bar.toggleClass('bg-primary', label.indexOf('Flashing') === 0 || label.indexOf('Applying') === 0);
  if (boldLabelEl === null || boldLabelEl.data('bound-label') !== label) {
    if (boldLabelEl) boldLabelEl.removeClass('font-weight-bold');
    boldLabelEl = $('.update-progress-label[data-label="' + label + '"]').addClass('font-weight-bold');
    boldLabelEl.data('bound-label', label);
  }
}

// Sets up the progress bar for the given phases (2-5, see FLASH_PHASES_*/DELTA_PHASES above).
function ui_configure_progress_phases(phases) {
  flashPhases = normalize_phases(phases);
  boldLabelEl = null;
  $('#update-progress-bar').css('width', '0%').attr('aria-valuenow', 0).text('0%')
    .removeClass('bg-primary').addClass('bg-info');
  $('.update-progress-label').removeClass('font-weight-bold').addClass('d-none').css('width', '0%');
  flashPhases.forEach(function(p) {
    $('.update-progress-label[data-label="' + p.label + '"]').removeClass('d-none').css('width', p.segment + '%');
  });

  // Tick marks between each pair of phases.
  $('.update-progress-tick').remove();
  for (let i = 1; i < flashPhases.length; i++) {
    $('<div class="update-progress-tick"></div>')
      .css({position: 'absolute', top: 0, bottom: 0, width: '2px', background: 'rgba(255,255,255,0.75)', left: flashPhases[i].start + '%'})
      .appendTo($('#update-progress-bar').parent());
  }
}

function ui_reset_progress_bars() {
  ui_configure_progress_phases(FLASH_PHASES_ROOT_ONLY);
}

// A delta whose target slot doesn't meet min_base_version gets a base image flashed first, then
// the delta - two stages, reusing the same bar (reset between them, not reconfigured mid-fill,
// which would visibly shrink an already-filled segment). Most deltas never hit this.
//
// Detected by matching substrings of do_minimal_update's log lines - if those phrases change,
// this silently stops detecting the transition.
function ui_check_delta_phase_transition(message) {
  if (message.includes('flashing that version as a base first')) {
    ui_configure_progress_phases(DOWNLOAD_THEN_FLASH_PHASES_WITH_BOOT);
  } else if (message.includes('continuing with delta to')) {
    ui_configure_progress_phases(DELTA_PHASES);
  }
}

function ui_show_update_progress(status) {
  // assumes status {'message': str, 'type': 'info'|'warning'|'error'|'success'|'failed'}
  ui_check_delta_phase_transition(status.message);
  ui_update_progress_bar(status.message);
  let color = (status.type == 'error' || status.type == 'failed') ? 'danger' : status.type;
  if (status.message.trim().length > 0) {
    ui_add_log(status.message, color);
  }
}

function ui_upload_software_update() {
  ui_disable_buttons();
  $('#update-log').show();
  let data = new FormData();
  let file = $('#update-file-selector')[0].files[0];
  data.append('file', file);
  try {
    fetch('/update/upload', {
      method: 'POST',
      body: data,
    }).then((response) => {
      ui_add_log('updates typically take 10-15 minutes, please be patient', 'info');
      ui_add_log('file uploaded', 'info');
      ui_begin_update();
    });
  } catch(e) {
    ui_add_log('Failed to upload file: ' + e, 'danger');
    ui_show_failure();
  }
}

function ui_disable_buttons() {
  $('#back-to-app').addClass('disabled');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').addClass('disabled');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').empty().append('Updating <i class="fas fa-circle-notch"></i>');
  $('#older-update-sel, #update-file-selector').attr('disabled', '');
}

function ui_show_done() {
  $('#back-to-app').removeClass('disabled');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').removeClass('btn-primary').addClass('btn-success');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').empty().append('Done!');
}

function ui_show_failure() {
  $('#back-to-app').removeClass('disabled');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').removeClass('btn-primary').addClass('btn-danger');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').empty().append('Failed, Retry?');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').attr('onclick', 'window.location.reload(true)');
  $('#submit-latest-update, #submit-older-update, #submit-custom-update').removeClass('disabled');
}

let md = new remarkable.Remarkable();

function ui_select_release(sel) {
  selected = $(sel).find(':selected');
  // data-name presence (not a separate data-version) distinguishes a real release option from
  // the "Choose..." placeholder.
  if (selected.data('name') !== undefined) {
    $('#older-update-desc').empty().append(md.render(selected.data('desc')));
    apply_update_label('#submit-older-update', releaseManifestInfo[sel.value]); // greys out itself if not yet known
  } else {
    $('#submit-older-update').addClass('disabled');
  }
}

// Watches an SSE progress channel until a terminal event - onSuccess() on 'success',
// ui_show_failure() on 'error'. Shared by ui_begin_flash_watch() and ui_download_then_finish().
function ui_watch_sse(url, onSuccess) {
  var source = new EventSource(url);
  source.onmessage = function(event) {
    var data = JSON.parse(event.data);
    ui_show_update_progress(data);
    if (data.type == 'success' || data.type == 'error') {
      source.close();
      if (data.type == 'success') {
        onSuccess();
      } else {
        ui_show_failure();
      }
    }
  };
}

// Kicks off /update/flash and watches its progress. Shared by "Begin Flash" and the
// download-then-flash flows - callers set up their own button/log/progress-bar state first.
// reconfigureBoot=false skips re-shaping the bar (used after a download, which already set it
// up - redoing it here would wipe the download segment's progress).
function ui_begin_flash_watch(reconfigureBoot) {
  reconfigureBoot = (typeof reconfigureBoot === 'undefined' ? true : reconfigureBoot);
  // Starts in the background and returns immediately - a dropped connection just reconnects to
  // the watcher instead of losing track. Safe to call even if a flash is already running (backend
  // refuses a second one, but there's still something to watch).
  fetch('/update/flash?tryboot=true', {
    method: 'POST',
  }).then((response) => response.json()).then((data) => {
    if (reconfigureBoot) {
      // has_boot is known upfront from the manifest, no need to wait for a boot-labeled message.
      ui_configure_progress_phases(data.has_boot ? FLASH_PHASES_WITH_BOOT : FLASH_PHASES_ROOT_ONLY);
    }
    ui_watch_sse('update/flash/progress', function() {
      // tryboot=true means the backend already triggered the reboot - safe to go straight to
      // waiting for the new slot.
      ui_add_log('Waiting for the unit to reboot into the new slot', 'info');
      setTimeout(ui_check_after_reboot, 5000, 2 * 60 / 5 - 1);
    });
  }).catch((e) => {
    ui_add_log('Failed to start flash: ' + e, 'danger');
    ui_show_failure();
  });
}

// Shared by all download-then-finish flows. manifestUrl is the only download location needed -
// image urls live inside the manifest itself, read directly by the backend. expectedVersion
// (optional) rejects a manifest that doesn't match. type must already be known by the caller
// (every caller already fetched it once to label its own button) - looking it up again after
// calling would race do_minimal_update's own reboot. Callers set up their own button/log/progress
// state first, same as ui_begin_flash_watch().
//
// Named "finish", not "flash": a full manifest still needs a follow-up /update/flash call, but a
// delta manifest is already fully applied (including its own reboot) by the time this reports
// success - calling /update/flash after a delta would be wrong.
function ui_download_then_finish(manifestUrl, expectedVersion, type) {
  fetch('/update/download/images', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      manifest_url: manifestUrl,
      expected_version: expectedVersion || null,
      tryboot: true,
    }),
  }).then((response) => response.json()).then((data) => {
    // Watch regardless of whether this started a fresh download or one was already running.
    ui_watch_sse('update/download/images/progress', function() {
      if (type === 'delta') {
        // do_minimal_update already applied the change and triggered tryboot - nothing left to
        // call, just wait for the reboot the same way the full-image path does after /update/flash.
        ui_add_log('Delta update applied, waiting for the unit to reboot into the new slot', 'info');
        setTimeout(ui_check_after_reboot, 5000, 2 * 60 / 5 - 1);
      } else {
        ui_add_log('Download complete, starting flash', 'info');
        ui_begin_flash_watch(false);
      }
    });
  }).catch((e) => {
    ui_add_log('Failed to start download: ' + e, 'danger');
    ui_show_failure();
  });
}

// Shared by both release buttons. skipIfStaged checks GET /update/staged first and flashes
// directly if that version's already there (Latest Release only - Other Releases always
// redownloads since the picked release may not match what's staged).
function ui_start_release_download(release, skipIfStaged) {
  ui_disable_buttons();
  $('#update-log').show();

  function download() {
    let manifest_url = find_manifest_url(release);
    if (!manifest_url) {
      ui_add_log('This release has no manifest.json asset attached', 'danger');
      ui_show_failure();
      return;
    }
    let info = releaseManifestInfo[release.tag_name];
    if (info && info.type === 'delta') {
      ui_configure_progress_phases(DELTA_PHASES);
    } else {
      ui_configure_progress_phases(info && info.hasBoot ? DOWNLOAD_THEN_FLASH_PHASES_WITH_BOOT : DOWNLOAD_THEN_FLASH_PHASES_ROOT_ONLY);
    }
    ui_add_log('Downloading ' + release.tag_name, 'info');
    ui_download_then_finish(manifest_url, release.tag_name, info ? info.type : null);
  }

  if (skipIfStaged) {
    fetch('/update/staged').then((r) => r.json()).then((staged) => {
      // type check matters: this shortcut skips a redundant multi-GB re-download, which only
      // applies to type full - a staged delta has no images to skip re-downloading, so treating
      // it the same way would send the flow to /update/flash looking for a root.img.xz that was
      // never there.
      if (staged.staged && staged.type === 'full' && staged.version === release.tag_name) {
        ui_add_log('Already downloaded, flashing directly', 'info');
        ui_reset_progress_bars();
        ui_begin_flash_watch();
      } else {
        download();
      }
    }).catch((e) => {
      ui_add_log('Failed to check staged update: ' + e, 'danger');
      ui_show_failure();
    });
  } else {
    download();
  }
}

// "Begin Flash" on the Latest Release tab - skips redownloading if the right version's already staged.
function ui_start_latest_release_update() {
  if (!latestRelease) return;
  ui_start_release_download(latestRelease, true);
}

// "Start Update" on the Other Releases tab.
function ui_start_selected_release_update() {
  let release = availableReleases[$('#older-update-sel').val()];
  if (!release) return;
  ui_start_release_download(release, false);
}

function ui_show_offline_message() {
  $('#latest-update-name').empty().append('Unable to automatically check for latest release <i class="fas fa-times text-danger"></i>');
  OFFLINE_INFO = 'To update:\n\n\
  1. Download the latest tar.gz release file from our \n\
      [GitHub releases page](https://github.com/micro-nova/AmpliPi/releases).\n\
  1. Use the the **Custom** update tab to upload the release.'
  $('#latest-update-desc').append(md.render(OFFLINE_INFO));
}

// get the current AmpliPi version
let version = 'unknown';
// undefined = not yet loaded (stay pending); null/'' = a real but unreadable inactive slot,
// treated as definitely below any delta's min_base_version floor. See compute_label_type.
let inactiveVersion;
fetch('/update/version').then((resp) => {
  resp.json().then((info) => {
    version = info.version;
    inactiveVersion = info.inactive_version;
    MIN_SECURE_VERSION = info.min_secure_version;
    // A release's label may have already been computed (and skipped, since inactiveVersion was
    // still undefined) before this resolved - redo it now for whatever's currently on screen.
    if (latestRelease) apply_update_label('#submit-latest-update', releaseManifestInfo[latestRelease.tag_name]);
    let selectedTag = $('#older-update-sel').val();
    if (availableReleases[selectedTag]) apply_update_label('#submit-older-update', releaseManifestInfo[selectedTag]);
  });
});

// Set by show_latest_release(), read by ui_start_latest_release_update(). Holds the full GH
// release object (not just tarball_url) since the flash flow needs its manifest.json asset URL
// and tag_name out of it.
let latestRelease = null;

function show_latest_release(latest_release) {
  // Pre-A/B releases (< MIN_SUPPORTED_VERSION) have no manifest.json and don't fit this update
  // flow - treated the same as already being up to date, matching populate_available_releases.
  if (latest_release.tag_name == version || !version_at_least(latest_release.tag_name, MIN_SUPPORTED_VERSION)
      || (MIN_SECURE_VERSION && !version_at_least(latest_release.tag_name, MIN_SECURE_VERSION))) {
    console.log('no A/B-compatible update available');
    $('#latest-update-name').empty().append('Your system is up to date  <i class="fas fa-check-circle text-success"></i>')
  } else {
    latestRelease = latest_release;
    // show the release info with its markdown from GH
    $('#submit-latest-update').removeClass('d-none');
    $('#latest-update-name').text(latest_release.name);
    $('#latest-update-desc').append(md.render(latest_release.body));
    apply_update_label('#submit-latest-update', undefined); // grey out until the manifest resolves below

    let manifest_url = find_manifest_url(latest_release);
    if (manifest_url) {
      fetch_manifest(manifest_url).then((manifest) => {
        releaseManifestInfo[latest_release.tag_name] = manifest;
        apply_update_label('#submit-latest-update', manifest);
      });
    } else {
      releaseManifestInfo[latest_release.tag_name] = MANIFEST_UNAVAILABLE;
      apply_update_label('#submit-latest-update', MANIFEST_UNAVAILABLE);
    }
  }
}

// TODO: update once the actual first A/B-scheme release version is decided
const MIN_SUPPORTED_VERSION = '0.5.0'; // Used to prevent users from attempting to install a pre-A:B partition update
let MIN_SECURE_VERSION = null; // Null until info fetch, gates what versions show in the other releases dropdown

// Simple major.minor.patch comparison, not full semver - fine here since this is only a UI-side
// preview (real enforcement is asgi.py's do_minimal_update, with real semver parsing). Returns
// true if `v` >= `floor`.
function version_at_least(v, floor) {
  let vp = v.split('.').map(Number);
  let fp = floor.split('.').map(Number);
  for (let i = 0; i < Math.max(vp.length, fp.length); i++) {
    let a = vp[i] || 0, b = fp[i] || 0;
    if (a !== b) return a > b;
  }
  return true;
}

// Same idea as latestRelease, but keyed by tag_name since Other Releases can point at any of several.
let availableReleases = {};
// tag_name -> {type, min_base_version, hasBoot}, populated as each release's manifest resolves
// in the background. Read here instead of re-fetching on every dropdown/button interaction - by
// the time a release is clickable, its manifest fetch has near-certainly already finished.
let releaseManifestInfo = {};

function populate_available_releases(releases) {
  // TODO: indicate difference between pre-releases and full-releases
  for (const release of releases) {
    if (!version_at_least(release.tag_name, MIN_SUPPORTED_VERSION)) continue;
    if (MIN_SECURE_VERSION && !version_at_least(release.tag_name, MIN_SECURE_VERSION)) continue;

    console.log(`found "${release.name}" - ${release.tag_name}`);
    availableReleases[release.tag_name] = release;
    let option = $(`<option value="${release.tag_name}"
                            data-name="${release.name}"
                            data-desc="${release.body}">
                            ${release.name}
                    </option>`);
    $('#older-update-sel').append(option);

    let manifest_url = find_manifest_url(release);
    if (manifest_url) {
      // No min_base_version-vs-inactive-slot check here: do_minimal_update's floor-check fallback
      // (asgi.py) handles that automatically server-side, flashing min_base_version as a base
      // image before applying the delta. Every post-cutoff release stays selectable here.
      fetch_manifest(manifest_url).then((manifest) => {
        // Stored even on failure (null): distinguishes "fetch failed" from "not fetched yet" for
        // apply_update_label/compute_label_type, which key their pending-vs-fail-open state off that.
        releaseManifestInfo[release.tag_name] = manifest;
      });
    } else {
      releaseManifestInfo[release.tag_name] = MANIFEST_UNAVAILABLE;
    }
  }
}

// Pulls manifest.json's URL from a GH release's assets (not tarball_url). Image urls aren't
// resolved here - they live inside the manifest itself, read directly by the backend. Returns
// null if manifest.json is missing from the release's assets - shouldn't happen for any release
// that passed the MIN_SUPPORTED_VERSION filter above, so callers treat it as a real anomaly.
function find_manifest_url(release) {
  let assets = release.assets || [];
  let asset = assets.find((a) => a.name === 'manifest.json');
  return asset ? asset.browser_download_url : null;
}

// Label shown on an update button once its manifest's type is known. Falls back to the type full
// label if the manifest can't be fetched/parsed at all (offline, CORS, ...) - the label is a
// convenience, not load-bearing, so failing open here just means it doesn't update.
const UPDATE_TYPE_LABELS = {full: 'Begin Flash', delta: 'Update now'};
// Shown (button greyed out via the 'disabled' class) while a button's real label is still unknown.
const CHECKING_LABEL = 'Checking update...';
// Sentinel stored in releaseManifestInfo/passed to apply_update_label when a release has no
// manifest.json asset at all - distinct from a fetch failure (null), since it's a genuine data
// problem rather than a transient one. Button stays disabled since there's nothing to flash.
const MANIFEST_UNAVAILABLE = 'unavailable';
const MANIFEST_UNAVAILABLE_LABEL = 'Update package unavailable';

// Resolves manifestUrl to {type, min_base_version, hasBoot}, or null on failure. type defaults
// to 'full' if omitted. hasBoot decides which progress-bar phases to show before download starts.
function fetch_manifest(manifestUrl) {
  return fetch(manifestUrl).then((r) => r.json())
    .then((m) => ({type: m.type || 'full', min_base_version: m.min_base_version || null, hasBoot: m.boot != null}))
    .catch(() => null);
}

// A DELTA manifest alone doesn't say whether clicking it triggers a flash - do_minimal_update
// flashes a base image first if the inactive slot doesn't meet min_base_version. version_at_least
// isn't hardened for dirty version strings on purpose: a non-numeric segment parses to NaN, and
// NaN comparisons are always false, so an unparseable version already fails the floor check safely.
function compute_label_type(manifest) {
  if (manifest === MANIFEST_UNAVAILABLE) return MANIFEST_UNAVAILABLE; // no manifest.json asset exists
  if (manifest === undefined) return null; // not fetched yet - stay pending
  if (manifest === null) return 'full'; // fetch failed - fail open to the safe default
  if (manifest.type !== 'delta') return manifest.type; // 'full' as today
  if (inactiveVersion === undefined) return null; // /update/version hasn't resolved yet - don't guess
  if (!inactiveVersion || !version_at_least(inactiveVersion, manifest.min_base_version)) {
    return 'full'; // will flash a base image first - same label, same mechanics as a real full release
  }
  return 'delta';
}

// Greys the button out with a neutral label until compute_label_type has a real answer, rather
// than showing (and enabling) a default label that might have to change moments later.
function apply_update_label(buttonSelector, manifest) {
  let t = compute_label_type(manifest);
  if (t === MANIFEST_UNAVAILABLE) {
    $(buttonSelector).text(MANIFEST_UNAVAILABLE_LABEL).addClass('disabled');
  } else if (t && UPDATE_TYPE_LABELS[t]) {
    $(buttonSelector).text(UPDATE_TYPE_LABELS[t]).removeClass('disabled');
  } else {
    $(buttonSelector).text(CHECKING_LABEL).addClass('disabled');
  }
}

async function requestSupportTunnel() {
  // the below is 2 lines long intentionally, because it renders into a <pre> tag.
  $('#support-tunnel-detail').text(`Requesting a support tunnel. This may take up to 60s.
  `);

  $('#support-tunnel-spinner').removeClass("d-none");
  $('#support-tunnel-detail-container').removeClass("d-none");

  res = await fetch('/support', {
    method: 'POST',
  });

  $('#support-tunnel-spinner').addClass("d-none");

  if(!res.ok) {
    alert(`Error: ${res.statusText}`);
    return;
  }

  body = await res.text();
  $('#support-tunnel-detail').text(body);

  $('#support-tunnel-email').attr(
      'href',
      `mailto:support@micro-nova.com?subject=Support%20tunnel%20request&body=${encodeURIComponent(body)}`
  );
  $('#support-tunnel-detail-caption').removeClass("d-none");
}

// Fetch the GitHub Releases and populate the release selector and latest release
// We use releases/latest to make the decision on what the latest release is,
//  avoiding having to sort the raw releases endpoint.
// Note: we use the failure of the releases/latest fetch to populate the offline messages
//  since the related tab is where the offline messages are shown.
fetch('https://api.github.com/repos/micro-nova/AmpliPi/releases/latest').then((resp) => {
  console.log(resp);
  if (resp.status != 200) {
    ui_show_offline_message();
    return;
  }
  resp.json().then((release) => {
    if (release.name) {
      show_latest_release(release);
    } else {
      ui_show_offline_message();
    }
  }).catch((err) => { return; });
}).catch((err) => { return; });

fetch('https://api.github.com/repos/micro-nova/AmpliPi/releases').then((resp) => {
  console.log(resp);
  if (resp.status != 200) {
    return
  }
  resp.json().then((releases) => {
    if (releases.length == 0) {
      return;
    }
    populate_available_releases(releases);
  }).catch((err) => { ui_show_offline_message(); });
}).catch((err) => { ui_show_offline_message(); });

