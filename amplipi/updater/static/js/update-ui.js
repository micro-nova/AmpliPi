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
      ui_add_log('Redirecting back to AmpliPi server', 'info');
      ui_show_done();
      setTimeout(ui_redirect_to_amplipi, 5000);
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

function ui_redirect_to_amplipi() {
  window.location = window.location.toString().replace(":5001/update", ":80")
}

// Translate the backend messages into consumable percentages for the progress bar
const UPDATE_PROGRESS_RE = /^(.+): (\d+(?:\.\d+)?)%$/;

// Phases shown on the progress bar, 2-5 depending on whether this run is downloading (Latest
// Release/Other Releases add one; an already-staged flash doesn't) and whether the update
// includes a boot image.
const DOWNLOAD_PHASE = 'Downloading root image';
const FLASH_PHASES_WITH_BOOT = ['Verifying root image', 'Verifying boot image', 'Flashing root', 'Flashing boot'];
const FLASH_PHASES_ROOT_ONLY = ['Verifying root image', 'Flashing root'];
let flashPhases = FLASH_PHASES_ROOT_ONLY;
// Cached by ui_configure_progress_phases() so ui_update_progress_bar() doesn't recompute per message.
let flashSegment = 100 / flashPhases.length;
let boldLabelEl = null;

function ui_update_progress_bar(message) {
  let match = message.match(UPDATE_PROGRESS_RE);
  if (!match) return;
  let label = match[1];
  let pct = parseFloat(match[2]);
  let idx = flashPhases.indexOf(label);
  if (idx === -1) return;
  let overall = idx * flashSegment + (pct / 100) * flashSegment;
  let bar = $('#update-progress-bar');
  bar.css('width', overall + '%').attr('aria-valuenow', overall).text(Math.round(overall) + '%');
  bar.toggleClass('bg-info', label.indexOf('Verifying') === 0 || label.indexOf('Downloading') === 0);
  bar.toggleClass('bg-primary', label.indexOf('Flashing') === 0);
  if (boldLabelEl === null || boldLabelEl.data('bound-label') !== label) {
    if (boldLabelEl) boldLabelEl.removeClass('font-weight-bold');
    boldLabelEl = $('.update-progress-label[data-label="' + label + '"]').addClass('font-weight-bold');
    boldLabelEl.data('bound-label', label);
  }
}

// Sets up the progress bar for the given phases (2-5, see FLASH_PHASES_* above).
function ui_configure_progress_phases(phases) {
  flashPhases = phases;
  flashSegment = 100 / flashPhases.length;
  boldLabelEl = null;
  $('#update-progress-bar').css('width', '0%').attr('aria-valuenow', 0).text('0%')
    .removeClass('bg-primary').addClass('bg-info');
  $('.update-progress-label').removeClass('font-weight-bold').addClass('d-none').css('width', '0%');
  flashPhases.forEach(function(label) {
    $('.update-progress-label[data-label="' + label + '"]').removeClass('d-none').css('width', flashSegment + '%');
  });

  // Tick marks between each pair of phases.
  $('.update-progress-tick').remove();
  for (let i = 1; i < flashPhases.length; i++) {
    $('<div class="update-progress-tick"></div>')
      .css({position: 'absolute', top: 0, bottom: 0, width: '2px', background: 'rgba(255,255,255,0.75)', left: (i * flashSegment) + '%'})
      .appendTo($('#update-progress-bar').parent());
  }
}

function ui_reset_progress_bars() {
  ui_configure_progress_phases(FLASH_PHASES_ROOT_ONLY);
}

function ui_show_update_progress(status) {
  // assumes status {'message': str, 'type': 'info'|'warning'|'error'|'success'|'failed'}
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
    $('#submit-older-update').removeClass('disabled');
    $('#older-update-desc').empty().append(md.render(selected.data('desc')));
  } else {
    $('#submit-older-update').addClass('disabled');
  }
}

// Watches an SSE progress channel until a terminal event - onSuccess() on 'success',
// ui_show_failure() on 'error'. Shared by ui_begin_flash_watch() and ui_download_then_flash().
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

// Shared by all download-then-flash flows. urls: {manifest_url, root_url, boot_url}.
// expectedVersion (optional) makes the backend refuse to proceed to the big downloads if the
// manifest it fetches doesn't match. Callers handle their own button/log/progress-bar setup
// first, same as ui_begin_flash_watch().
function ui_download_then_flash(urls, expectedVersion) {
  fetch('/update/download/images', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      manifest_url: urls.manifest_url,
      root_url: urls.root_url,
      boot_url: urls.boot_url || null,
      expected_version: expectedVersion || null,
    }),
  }).then((response) => response.json()).then((data) => {
    // Watch regardless of whether this started a fresh download or one was already running.
    ui_watch_sse('update/download/images/progress', function() {
      ui_add_log('Download complete, starting flash', 'info');
      ui_begin_flash_watch(false);
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
    let urls = extract_image_urls(release);
    if (!urls) {
      ui_add_log('This release has no manifest.json/root.img.xz assets attached', 'danger');
      ui_show_failure();
      return;
    }
    ui_configure_progress_phases([DOWNLOAD_PHASE].concat(urls.boot_url ? FLASH_PHASES_WITH_BOOT : FLASH_PHASES_ROOT_ONLY));
    ui_add_log('Downloading ' + release.tag_name, 'info');
    ui_download_then_flash(urls, release.tag_name);
  }

  if (skipIfStaged) {
    fetch('/update/staged').then((r) => r.json()).then((staged) => {
      if (staged.staged && staged.version === release.tag_name) {
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
fetch('/update/version').then((resp) => {
  resp.json().then((info) => {
    version = info.version;
  });
});

// Set by show_latest_release(), read by ui_start_latest_release_update(). Holds the full GH
// release object (not just tarball_url) since the flash flow needs real asset URLs out of it.
let latestRelease = null;

function show_latest_release(latest_release) {
  if (latest_release.tag_name == version) {
    console.log('already up to date');
    $('#latest-update-name').empty().append('Your system is up to date  <i class="fas fa-check-circle text-success"></i>')
  } else {
    latestRelease = latest_release;
    // show the release info with its markdown from GH
    $('#submit-latest-update').removeClass('d-none');
    $('#latest-update-name').text(latest_release.name);
    $('#latest-update-desc').append(md.render(latest_release.body));
  }
}

// Same idea as latestRelease, but keyed by tag_name since Other Releases can point at any of several.
let availableReleases = {};

function populate_available_releases(releases) {
  // TODO: indicate difference between pre-releases and full-releases
  for (const release of releases) {
    console.log(`found "${release.name}" - ${release.tag_name}`);
    availableReleases[release.tag_name] = release;
    $('#older-update-sel').append(`<option value="${release.tag_name}"
                                           data-name="${release.name}"
                                           data-desc="${release.body}">
                                           ${release.name}
                                   </option>`);
  }
}

// Pulls manifest.json/root.img.xz/boot.img.xz URLs from a GH release's assets (not tarball_url,
// GitHub's source archive). Returns null if they're missing - true for every real release right
// now since CI doesn't attach them yet.
function extract_image_urls(release) {
  let assets = release.assets || [];
  let find_url = (filename) => {
    let asset = assets.find((a) => a.name === filename);
    return asset ? asset.browser_download_url : null;
  };
  let manifest_url = find_url('manifest.json');
  let root_url = find_url('root.img.xz');
  if (!manifest_url || !root_url) return null;
  return {manifest_url: manifest_url, root_url: root_url, boot_url: find_url('boot.img.xz')};
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

