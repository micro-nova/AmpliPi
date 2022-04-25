
const icons = {
  'none'      : '/static/imgs/disconnected.png'
}

function onSrcInputChange(obj) {
  const input = obj.value;
  const src = obj.dataset.src;
  let req = {
    "input" : input
  };
  sendRequest('/sources/' + src, 'PATCH', req);
}

function onSrcAdd(obj) {
  const src = Number(obj[0].id.substring(1,2));
  const to_add = obj.val();

  zones = []
  groups = []

  for(i of to_add){
    const type = i.substring(0,1);
    const id = Number(i.substring(1));
    if (type == 'z'){
      zones.push(id);
    } else if (type == 'g') {
      groups.push(id);
    }
  }

  let req = {zones: zones, groups: groups, update: {source_id: src}}

  if(groups.length > 0 || zones.length > 0) sendRequestAndReload("/zones/", 'PATCH', req, src);
}

function onMuteToggle(icon) {
  let ctrl = icon.closest('.volume');
  let mute = !ctrl.classList.contains('muted');
  ctrl.classList.toggle('muted', mute); // immediately toggle the mute to give the user feedback
  let req = { 'mute' : mute};
  let path = null;
  if (ctrl.dataset.hasOwnProperty('zone')) {
    path = '/zones/' + Number(ctrl.dataset.zone)
  } else if (ctrl.dataset.hasOwnProperty('group')) {
    path = '/groups/' + Number(ctrl.dataset.group)
  }
  if (path) {
    sendRequest(path, 'PATCH', req);
  }
}

function debounce(ms, fun){
  var timer;
  return function(obj){
      clearTimeout(timer);
      timer = setTimeout(function(){
          fun(obj);
      }, ms);
  };
}

function refresh() {
  get();
}
current_src = 's0'; // this needs to be set base on the URL path
for (var i = 0; i < 4; i++) {
  if (window.location.href.endsWith(`/${i}`)) {
    current_src = `s${i}`;
    break;
  }
}

$(document).ready(function(){
  // Some things are not part of the automatic tab-content switching
  // hide things related to the old src and show things related to the new one
  $('a[data-toggle="tab"]').on('show.bs.tab', function (e) {
    // switch the source input selector to the one connected to the current source (or the settings pane)
    const old_src = e.relatedTarget.id;
    const new_src = e.target.id;
    if (old_src != "settings-nav") {
      $('#' + old_src + '-input')[0].style.display = "none";
      $('#' + old_src + '-player')[0].style.display = "none";
    } else {
      // reload the page to keep it up to date with any changes made in settings
      var src = new_src[1];
      window.location.assign('/' + src);
    }
    if (new_src != "settings-nav") {
      $('#' + new_src + '-input')[0].style.display = "block";
      $('#' + new_src + '-player')[0].style.display = "block";
    } else {
      $('#settings-sel')[0].style.display = "block";
      updateSettings();
    }
    current_src = new_src;
  });
  // Refresh the page sequentially in place of SSE
  setInterval(refresh, 2000);

  // Make all zone/group multiselectors multiselectors and configures them
  $('[id^=s][id$=-add-input]').multiselect({
    onDropdownHide: function(e){
      // Yeah I know this is a gross way to get the multiselector's id but it's all I could find.
      onSrcAdd($('#'+e.target.previousSibling.id))
    },
    buttonTextAlignment: "left"
  })

  // hook file selected event
  $('#settings-config-file-selector')[0].addEventListener('change', (event) => {
    $('#settings-config-load')[0].classList.remove('disabled');
  });
});

function updateVol(ctrl, muted, vol) {
  let range = ctrl.querySelector("input[type=range]");
  let fill = ctrl.querySelector(".bar .bar-fill");
  let mute_icon = ctrl.querySelector(".icon i");
  const pct = (vol - range.min) / (range.max - range.min) * 100.0;
  // update mute state and switch between muted and volume icon
  ctrl.classList.toggle('muted', muted);
  mute_icon.classList.toggle('fa-volume-up', !muted);
  mute_icon.classList.toggle('fa-volume-mute', muted);
  // update volume bar and value
  fill.style.width = pct + "%";
  range.setAttribute("value", vol);
  range.dispatchEvent(new Event("change"));
}

function sendStreamCommand(ctrl, command) {
  let player = ctrl.closest(".pandora-player");
  let src_input = player.dataset.srcInput;
  if (src_input.startsWith("stream=")) {
    let stream_id = Number(src_input.replace("stream=", ""));
    sendRequest('/streams/' + stream_id + '/' + command, 'POST', {});
  }
}

function timeSince(timeStamp) {
  var now = new Date(),
    secondsPast = (now.getTime() - timeStamp) / 1000;
  if (secondsPast < 60) {
    return parseInt(secondsPast) + 's';
  }
  if (secondsPast < 3600) {
    return parseInt(secondsPast / 60) + 'm';
  }
  if (secondsPast <= 86400) {
    return parseInt(secondsPast / 3600) + 'h';
  }
  if (secondsPast > 86400) {
    day = timeStamp.getDate();
    month = timeStamp.toDateString().match(/ [a-zA-Z]*/)[0].replace(" ", "");
    year = timeStamp.getFullYear() == now.getFullYear() ? "" : " " + timeStamp.getFullYear();
    return day + " " + month + year;
  }
}

$('#preset-list').on('show.bs.collapse', function () {
  // do something…
  for (pst of $('#preset-list .preset')) {
    let status = pst.querySelector(".status i");
    status.style.visibility = "hidden";
    status.classList.toggle('fa-check-circle', true); // we need something the right size to be there
    status.classList.toggle('fa-exclamation-triangle', false);
    status.classList.toggle('fa-circle-notch', false);
  }
})

function onLoadPreset(ctrl) {
  let pst = ctrl.closest(".preset");
  let pid = pst.dataset.id;
  let status = pst.querySelector(".status i");
  let name = pst.querySelector(".name");
  let last_used = pst.querySelector(".last-used");
  // start the progress spinner
  status.title='';
  status.style.visibility = "visible";
  status.classList.toggle('fa-check-circle', false);
  status.classList.toggle('fa-exclamation-triangle', false);
  status.classList.toggle('fa-circle-notch', true);
  let response = sendRequest('/presets/' + pid + '/load', 'POST', {},
  function (response) {
    try {
      status.classList.toggle('fa-circle-notch', false); // testing to see when we get here
      let preset = null;
      for (const p of response['presets']) {
        if (p['id'] == pid) {
          preset = p;
        }
      }
      // TODO: for some reason this check doesn't always get set, investigate tomorrow
      status.classList.toggle('fa-check-circle', preset != null);
      status.classList.toggle('fa-exclamation-triangle', preset == null);
      if (preset) {
        if (preset.id == 9999) {
          last_used.innerHTML = ''; // last config shouldnt show when it was last modified
        } else if (preset.hasOwnProperty('last_used') && preset.last_used) {
          last_used.innerHTML = timeSince(new Date(preset.last_used * 1000)); // js expects milliseconds from epoch
        } else {
          last_used.innerHTML = 'never';
        }
      }
    } catch (err) {
      last_used.innerHTML = err;
      console.log('err1: ' + err);
      status.classList.toggle('fa-circle-notch', false);
      status.classList.toggle('fa-check-circle', false);
      status.classList.toggle('fa-exclamation-triangle', true);
    }
  },
  function (err) {
    last_used.innerHTML = err;
    console.log('err2: ' + err);
    status.classList.toggle('fa-circle-notch', false);
    status.classList.toggle('fa-check-circle', false);
    status.classList.toggle('fa-exclamation-triangle', true);
  });
  // TODO: updated last-used time
}

function onPlayPauseStop(ctrl) {
  if (ctrl.classList.contains('fa-play')) {
    sendStreamCommand(ctrl, 'play');
  } else if (ctrl.classList.contains('fa-pause')) {
    sendStreamCommand(ctrl, 'pause');
  } else if (ctrl.classList.contains('fa-stop')) {
    sendStreamCommand(ctrl, 'stop');
  }
}

function onNext(ctrl) {
  sendStreamCommand(ctrl, 'next');
}

function onPrev(ctrl) {
  sendStreamCommand(ctrl, 'prev')
}

function onLike(ctrl) {
  sendStreamCommand(ctrl, 'love');
}

function onDislike(ctrl) {
  sendStreamCommand(ctrl, 'ban');
}

function updateSourceView(status) {
  // update player state
  for (const src of status['sources']) {
    const stream_id = src.input.startsWith("stream=") ? src.input.replace("stream=", "") : undefined;
    let cover = $('#s' + src.id + '-player .cover img')[0];
    let artist = $('#s' + src.id + '-player .info .artist')[0];
    let album = $('#s' + src.id + '-player .info .album')[0];
    let track = $('#s' + src.id + '-player .info .song')[0];
    let next = $('#s' + src.id + '-player .step-forward')[0];
    let prev = $('#s' + src.id + '-player .step-backward')[0];
    let play_pause = $('#s' + src.id + '-player .play-pause')[0];
    let like = $('#s' + src.id + '-player .like')[0];
    let dislike = $('#s' + src.id + '-player .dislike')[0];
    let playing_indicator = $('#s' + src.id + ' i')[0];

    track.innerHTML = src.info.track ? src.info.track : src.info.name;
    artist.innerHTML = src.info.artist ? src.info.artist : '';
    album.innerHTML = src.info.album ? src.info.album : '';
    cover.src = src.info.img_url ? src.info.img_url : icons['none'];
    const playing = src.info.state == "playing";
    playing_indicator.style.visibility = playing ? "visible" : "hidden";

    // update the control buttons
    supported_cmds = src.info.supported_cmds;
    next.classList.toggle('disabled', !supported_cmds.includes("next"));
    prev.classList.toggle('disabled', !supported_cmds.includes("prev"));

    like.style.visibility = supported_cmds.includes("love") ? "visible" : "hidden";
    dislike.style.visibility = supported_cmds.includes("ban") ? "visible" : "hidden";

    if (supported_cmds.includes("pause")) {
      play_pause.classList.toggle('disabled', false);
      play_pause.classList.toggle('fa-play', !playing);
      play_pause.classList.toggle('fa-pause', playing);
      play_pause.classList.toggle('fa-stop', false);
    } else if (supported_cmds.includes("stop")) {
      play_pause.classList.toggle('disabled', false);
      play_pause.classList.toggle('fa-play', !playing);
      play_pause.classList.toggle('fa-stop', playing);
      play_pause.classList.toggle('fa-pause', false);
    } else {
      play_pause.classList.toggle('disabled', true);
    }

    // update each source's input
    player = $("#s" + src.id + "-player")[0];
    player.dataset.srcInput = src.input;
    $('#s' + src.id + '-input').val(src.input);
  }

  // update volumes
  zone_mismatch = false; // detect when a zone's audio source is displayed wrong
  const controls = document.querySelectorAll(".volume");
  for (const ctrl of controls) {
    if (ctrl.dataset.hasOwnProperty('zone')){
      let z = ctrl.dataset.zone;
      const zone = status.zones[z];
      updateVol(ctrl, zone.mute, zone.vol_f);
      parent_src = ctrl.dataset.source;
      if (zone.source_id != parent_src) {
        zone_mismatch = true;
      }
    } else if (ctrl.dataset.hasOwnProperty('group')) {
      let gid = ctrl.dataset.group;
      for (const g of status.groups) {
        if (g.id == gid) {
          updateVol(ctrl, g.mute, g.vol_f);
          break;
        }
      }
    } else {
      console.log('volume control ' + ctrl.id + ' not bound to any zone or group');
    }
  }

  // TODO: update presets (their last applied times and status)
  for (const preset of status['presets']) {
    let pst = $('#pst-' + preset.id)[0];
    let last_used = pst.querySelector(".last-used");
    if (preset.last_used) {
      last_used.innerHTML = timeSince(new Date(preset.last_used * 1000)); // js expects milliseconds from epoch
    } else if (preset.id == 9999) {
      last_used.innerHTML = '';
    } else {
      last_used.innerHTML = 'never';
    }
  }
  // detect a group/zone change and force an update // TODO: zone changes shouldn't need a refresh
  // current_source can be ['s0', 's1', 's2', 's3', 'settings-nav']
  if (zone_mismatch && current_src != "settings-nav") {
    const selected_src = current_src.replace('s', '');
    window.location.assign('/' + selected_src);
  }
}

// basic request handling
function onRequest(req) {
}
function onResponse(resp) {
  updateSourceView(resp);
}
async function get() {
  let response = await fetch('/api');
  let result = await response.json();
  onResponse(result);
  return result;
}

async function sendRequest(path, method, req, handleResponse=function(result){}, handleErr=function(err){}) {
  onRequest(req)
  let response = await fetch('/api' + path, {
    method: method,
    headers: {
      'Content-Type': 'application/json;charset=utf-8'
    },
    body: JSON.stringify(req)
  });
  response.json()
  .then(function(response){
    handleResponse(response);
    onResponse(response);
  }).catch(handleErr);
}

async function sendRequestAndReload(path, method, req, src) {
  await sendRequest(path, method, req);
  // reload the page, making sure to stay on the same source tab
  window.location.assign('/' + src);
}
// group and zone volume control
function onGroupVolChange(g, vol) {
  if (vol) {
    let req = {
      "vol_f" : Number(vol),
      "mute" : false
    };
    sendRequest('/groups/' + g, 'PATCH', req);
  }
}
function onZoneVolChange(z, vol) {
  if (vol) {
    let req = {
      "vol_f" : Number(vol),
      "mute" : false
    };
    sendRequest('/zones/' + z, 'PATCH', req);
  }
}

// pretty volume controls, based on: codepen found here:
let vols = {};
document.addEventListener("DOMContentLoaded", () => {
  const controls = document.querySelectorAll(".volume");
  for (const ctrl of controls){
    initVolControl(ctrl);
  }
})

function clamp(min, max, val) {
  return Math.max(Math.min(val, max), min);
}

const VOL_REQ_THROTTLE_MS = 50; // Limit the volume requests that can be made to prevent overwhelming the interface

function initVolControl(ctrl) {
  const range = ctrl.querySelector("input[type=range]");
  const barHoverBox = ctrl.querySelector(".bar-hoverbox");
  const fill = ctrl.querySelector(".bar .bar-fill");
  const zone = ctrl.dataset.hasOwnProperty('zone') ? ctrl.dataset.zone : null;
  const group = ctrl.dataset.hasOwnProperty('group') ? ctrl.dataset.group : null;
  let last_req_stamp = Date(0); // keep track of request time stamps for throttling (so we don't overload AmpliPi)

  const initValue = (value) => {
    const pct = (value - range.min) / (range.max - range.min) * 100.0;
    fill.style.width = pct + "%";
    range.setAttribute("value", value);
    range.dispatchEvent(new Event("change"));
  }

  const setValue = (value) => {
    const val = clamp(range.min, range.max, value);
    initValue(val);
    const cur_stamp = Date.now();
    const req_throttled = (cur_stamp - last_req_stamp) < VOL_REQ_THROTTLE_MS;
    if (!req_throttled){
      if (zone){
        onZoneVolChange(zone, val);
      } else if (group) {
        onGroupVolChange(group, val);
      } else {
        console.log('volume control ' + ctrl.id + ' not bound to any zone or group');
      }
      last_req_stamp = cur_stamp; // only update on a successful request (avoids constant rejection of a stream of user requests)
    } else {
      console.debug('volume adjustment rejected, last request made < 50ms ago');
    }
  }

  const setPct = (pct) => {
    const delta = range.max - range.min;
    setValue((pct / 100.0 * delta) + Number(range.min));
  }

  initValue(range.value);

  const calculateFill = (e) => {
    let offsetX = e.offsetX

    if (e.type === "touchmove") {
      offsetX = e.touches[0].pageX - e.touches[0].target.offsetLeft;
    }

    const width = e.target.offsetWidth - 30;

    setPct((offsetX - 15) / width * 100.0)
  }
  vols[ctrl.id] = {}
  vols[ctrl.id].barStillDown = false;

  barHoverBox.addEventListener("touchstart", (e) => {
    vols[ctrl.id].barStillDown = true;

    calculateFill(e);
  }, true);

  barHoverBox.addEventListener("touchmove", (e) => {
    if (vols[ctrl.id].barStillDown) {
      calculateFill(e);
    }
  }, true);

  barHoverBox.addEventListener("mousedown", (e) => {
    vols[ctrl.id].barStillDown = true;

    calculateFill(e);
  }, true);

  barHoverBox.addEventListener("mousemove", (e) => {
    if (vols[ctrl.id].barStillDown) {
      calculateFill(e);
    }
  });

  document.addEventListener("mouseup", (e) => {
    vols[ctrl.id].barStillDown = false;
  }, true);

  document.addEventListener("touchend", (e) => {
   vols[ctrl.id].barStillDown = false;
  }, true);
}

function uploadConfig() {
  const reader = new FileReader();
  // TODO: disable button (it should have been enabled by the change event on the file selector)
  selector = $('#settings-config-file-selector')[0];
  reader.addEventListener('load', (event) => {
    const config = event.target.result;
    // TODO: parse the json config??
    // config_str = JSON.stringify(config)
    // load the new config
    fetch('/api/load', {method: 'POST', headers: { 'Content-Type': 'application/json;charset=utf-8'}, body: config});
    // TODO: show success or fail
  });
  reader.readAsText(selector.files[0]);
}

// From: https://stackoverflow.com/questions/19721439/download-json-object-as-a-file-from-browser
async function downloadConfig(){
  // get the current config
  let response = await fetch('/api');
  let config = await response.json();
  var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(config));
  var downloadAnchorNode = document.createElement('a');
  downloadAnchorNode.setAttribute("href",     dataStr);
  downloadAnchorNode.setAttribute("download", "config.json");
  document.body.appendChild(downloadAnchorNode); // required for firefox
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
}

async function resetDevice() {
  let response = await fetch('/api/reset', {method: 'POST'});
  // TODO: validate response (and potentially change button color)
}
