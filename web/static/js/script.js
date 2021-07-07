
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
  const src = Number(obj.id.substring(1,2));
  const to_add = obj.value;
  if (to_add) {
    const type = to_add.substring(0,1);
    const id = Number(to_add.substring(1));
    let req = { 'source_id' : src };
    if (type == 'z'){
      path =  '/zones/' + id;
    } else if (type == 'g') {
      path = '/groups/' + id;
    }
    sendRequestAndReload(path, 'PATCH', req, src);
  }
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
      $('#settings-header')[0].style.display = "none";
    }
    if (new_src != "settings-nav") {
      $('#' + new_src + '-input')[0].style.display = "block";
      $('#' + new_src + '-player')[0].style.display = "block";
    } else {
      $('#settings-header')[0].style.display = "block";
    }
  });
  setInterval(refresh, 2000);
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

function onPlayPause(ctrl) {
  if (ctrl.classList.contains('fa-play')) {
    sendStreamCommand(ctrl, 'play');
  } else {
    sendStreamCommand(ctrl, 'pause');
  }
}

function onNext(ctrl) {
  sendStreamCommand(ctrl, 'next');
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
    let song = $('#s' + src.id + '-player .info .song')[0];
    let next = $('#s' + src.id + '-player .step-forward')[0];
    let play_pause = $('#s' + src.id + '-player .play-pause')[0];
    let like = $('#s' + src.id + '-player .like')[0];
    let dislike = $('#s' + src.id + '-player .dislike')[0];
    let playing_indicator = $('#s' + src.id + ' i')[0];
    // defaults
    artist.innerHTML = 'No artist';
    album.innerHTML = 'No album';
    song.innerHTML = 'No song';
    like.style.visibility = "hidden";
    dislike.style.visibility = "hidden";
    play_pause.style.visibility = "hidden";
    next.style.visibility = "hidden";
    artist.innerHTML = src.info.artist ? src.info.artist : artist.innerHTML;
    album.innerHTML = src.info.album ? src.info.album : album.innerHTML;
    song.innerHTML = src.info.track ? src.info.track : song.innerHTML;
    cover.src = src.info.img_url ? src.info.img_url : icons['none'];
    const playing = src.info.state == "playing";
    playing_indicator.style.visibility = playing ? "visible" : "hidden";
    if (stream_id) {
      // find the right stream
      let stream = undefined;
      for (const s of status.streams) {
        if (s.id == stream_id) {
          stream = s;
          break;
        }
      }
      if (stream) {
        // update the player's song info
        if (stream.type == 'pandora') {
          next.style.visibility = "visible";
          like.style.visibility = "visible";
          dislike.style.visibility = "visible";
          play_pause.style.visibility = "visible";
          play_pause.classList.toggle('fa-play', !playing);
          play_pause.classList.toggle('fa-pause', playing);
        }
      }
    }
    // update each source's input
    player = $("#s" + src.id + "-player")[0];
    player.dataset.srcInput = src.input;
    $('#s' + src.id + '-input').val(src.input);
  }

  // update volumes
  const controls = document.querySelectorAll(".volume");
  for (const ctrl of controls) {
    if (ctrl.dataset.hasOwnProperty('zone')){
      let z = ctrl.dataset.zone;
      updateVol(ctrl, status.zones[z].mute, status.zones[z].vol);
    } else if (ctrl.dataset.hasOwnProperty('group')) {
      let gid = ctrl.dataset.group;
      for (const g of status.groups) {
        if (g.id == gid) {
          updateVol(ctrl, g.mute, g.vol_delta);
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
  // TODO: add/remove groups and zones?
  // TODO: for now can we detect a group/zone change and force an update?
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
      "vol_delta" : Number(vol),
      "mute" : false
    };
    sendRequest('/groups/' + g, 'PATCH', req);
  }
}
function onZoneVolChange(z, vol) {
  if (vol) {
    let req = {
      "vol" : Number(vol),
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
  let req_throttled = false;

  const initValue = (value) => {
    const pct = (value - range.min) / (range.max - range.min) * 100.0;
    fill.style.width = pct + "%";
    range.setAttribute("value", value);
    range.dispatchEvent(new Event("change"));
  }

  const setValue = (value) => {
    const val = clamp(range.min, range.max, value);
    initValue(val);
    const vol = Math.round(val);
    if (!req_throttled){
      if (zone){
        onZoneVolChange(zone, vol);
      } else if (group) {
        onGroupVolChange(group, vol);
      } else {
        console.log('volume control ' + ctrl.id + ' not bound to any zone or group');
      }
      req_throttled = true;
      setTimeout(() => {
        req_throttled = false
      }, VOL_REQ_THROTTLE_MS);

    }
  }

  const setPct = (pct) => {
    const delta = range.max - range.min;
    setValue((pct / 100.0 * delta) + Number(range.min))
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

async function plex_pin_req() {
  // Request a Plex pin to use for interacting with the Plex API
  document.getElementById('plexamp-connect').textContent = "Sending request...";
  let myuuid = uuidv4(); // UUID used as the 'clientIdentifier' for Plexamp requests/devices
  let details = { }
  let response = await fetch('https://plex.tv/api/v2/pins', {
    method: 'POST',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: "strong=true&X-Plex-Product=AmpliPi&X-Plex-Client-Identifier=" + myuuid
  }); // The actual pin request is sent. response holds the pin, pin code, and our UUID.
  response.json()
  .then(function(response){ // Make URL for the Plex Account Login
    const purl = `https://app.plex.tv/auth#?clientID=${response.clientIdentifier}&code=${response.code}&context%5Bdevice%5D%5Bproduct%5D=AmpliPi`;
    details.id = response.id; // The actual PIN
    details.code = response.code; // A code associated with the PIN
    details.uuid = response.clientIdentifier; // Our UUID associated with the PIN and authToken
    details.authToken = null; // Will eventually hold a token from plex_token_ret on a successful sign-in
    console.log(details);
    window.open(purl, "_blank"); // Open 'purl' in a new tab in the current browser window
  });
  return details; // Pin, code, UUID, and authToken are used in the other functions
}

async function plex_token_ret(details) {
  // Attempt to retrieve the plex token (this will return 'null' until the user enters their Plex account details)
  // NOTE: this token will only work for plexamp if the user has a Plex Pass subscription
  document.getElementById('plexamp-connect').textContent = "Awaiting Plex sign-in...";
  let response = await fetch('https://plex.tv/api/v2/pins/'+details.id, {
    method: 'GET',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
      'code': details.code,
      'X-Plex-Client-Identifier': details.uuid
    },
  }); // Information related to our PIN was requested. Parse that info to see if we've authenticated yet
  response.json().then(function(response){
    console.log("Token: " + response.authToken);
    details.authToken = response.authToken;
    console.log("Time remaining: " + response.expiresIn);
    details.expiresIn = response.expiresIn;
  });
  return details;
}

async function plex_stream(details) {
  // Create Plexamp stream using AmpliPi's API
  var req = {
    "name": "AmpliPi Plexamp",
    "client_id": details.uuid,
    "token": details.authToken,
    "type": "plexamp"
  } // POST a new stream to the AmpliPi API using the newly authenticated credentials
  sendRequest('/stream', 'POST', req);
  console.log(`Creating stream with these parameters: name = ${req.name}, UUID = ${req.client_id}, and token = ${req.token}`);
}

function sleepjs(ms) {
  return new Promise(resolve => setTimeout(resolve, ms)); // JavaScript sleep function
}

async function plexamp_create_stream() {
  // Connect to Plex's API and add a Plexamp stream to AmpliPi
  var connect_button = document.getElementById('plexamp-connect');
  var reset_button = document.getElementById('plexamp-reset');
  var done_button = document.getElementById('plexamp-done');
  var msg_box = document.getElementById('plexamp-msg');
  connect_button.disabled = true;
  let details = await plex_pin_req(); // Request a pin
  await sleepjs(2000); // Wait for info to propagate over
  reset_button.style.display = "inline-block";
  done_button.style.display = "none";
  msg_box.style.display = "none";

  do {
    let details2 = await plex_token_ret(details); // Retrieve our token
    await sleepjs(2000); // poll the plex servers slowly
    if (details2.expiresIn == null){
      msg_box.textContent = "Timed out while waiting for response from Plex";
      msg_box.style.color = "yellow";
      msg_box.style.display = "block";
      msg_box.style.alignSelf = "center";
      break; // Break when you run out of time (30 minutes, set by Plex)
    }
    details = details2; // Update authToken state and time until expiration
  } while (details.authToken == null); // "== null" should also check for undefined
  if (details.authToken){
    connect_button.style.display = "none";
    reset_button.style.display = "none";
    done_button.textContent = "Done - click to continue";
    done_button.style.display = "inline-block";
    msg_box.textContent = "'AmpliPi Plexamp' stream added";
    msg_box.style.color = "white";
    msg_box.style.display = "block";
    msg_box.style.alignSelf = "center";
    plex_stream(details); // Create a Plexamp stream using the API!
  }
}
