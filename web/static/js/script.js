
const icons = {
  'shairport' : '/static/imgs/shairport.png',
  'local'     : '/static/imgs/rca_inputs.svg',
  'pandora'   : '/static/imgs/pandora.png',
  'spotify'   : '/static/imgs/spotify.png',
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
    // switch the source input selector to the one connected to the current source
    const old_src = e.relatedTarget.id;
    const new_src = e.target.id;
    $('#' + new_src + '-input')[0].style.display = "block";
    $('#' + old_src + '-input')[0].style.display = "none";
    // switch the player to the one connected to the current source
    $('#' + new_src + '-player')[0].style.display = "block";
    $('#' + old_src + '-player')[0].style.display = "none";
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
    let req = { "cmd" : command };
    sendRequest('/streams/' + stream_id, 'PATCH', req);
  }
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
    playing_indicator.style.visibility = "hidden"; // TODO: add audio playing detection to rca inputs
    like.style.visibility = "hidden";
    dislike.style.visibility = "hidden";
    play_pause.style.visibility = "hidden";
    next.style.visibility = "hidden";
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
          const playing = stream.status == "playing";
          next.style.visibility = "visible";
          like.style.visibility = "visible";
          dislike.style.visibility = "visible";
          playing_indicator.style.visibility = playing ? "visible" : "hidden";
          play_pause.style.visibility = "visible";
          play_pause.classList.toggle('fa-play', !playing);
          play_pause.classList.toggle('fa-pause', playing);
          try {
            // update album art
            cover.src = stream.info.img_url ? stream.info.img_url : icons['pandora'];
            artist.innerHTML = stream.info.artist ? stream.info.artist : artist.innerHTML;
            album.innerHTML = stream.info.album ? stream.info.album : album.innerHTML;
            song.innerHTML = stream.info.track ? stream.info.track : song.innerHTML;
          } catch (err) {}
        } else if (stream.type == 'shairport') {
          // TODO: populate shairport album info
          cover.src = icons['shairport'];
          try {
            artist.innerHTML = stream.info.artist ? stream.info.artist : artist.innerHTML;
            album.innerHTML = stream.info.album ? stream.info.album : album.innerHTML;
            song.innerHTML = stream.info.track ? stream.info.track : song.innerHTML;
          } catch (err) {}
        } else if (stream.type == 'spotify') {
          // TODO: populate spotify album info
          cover.src = icons['spotify'];
        }
      }
    } else if (src.input == 'local') {
      cover.src = icons['local'];
      artist.innerHTML = src.name;
    } else {
      cover.src = icons['none'];
    }
    // update each source's input
    $("#s" + src.id + "-player")[0].dataset.srcInput = src.input;
    $("#s" + src.id + '-input select').val(src.input);
  }

  // update volumes
  const controls = document.querySelectorAll(".volume");
  for (const ctrl of controls) {
    if (ctrl.dataset.hasOwnProperty('zone')){
      let z = ctrl.dataset.zone;
      updateVol(ctrl, status.zones[z].mute, status.zones[z].vol);
    } else if (ctrl.dataset.hasOwnProperty('group')) {
      let g = ctrl.dataset.group;
      updateVol(ctrl, status.groups[g].mute, status.groups[g].vol_delta);
    } else {
      console.log('volume control ' + ctrl.id + ' not bound to any zone or group');
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
  let response = await fetch('/api/');
  let result = await response.json();
  onResponse(result);
  return result;
}

async function sendRequest(path, method, req) {
  onRequest(req)
  let response = await fetch('/api' + path, {
    method: method,
    headers: {
      'Content-Type': 'application/json;charset=utf-8'
    },
    body: JSON.stringify(req)
  });
  let result = await response.json();
  onResponse(result);
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

  barHoverBox.addEventListener("wheel", (e) => {
    const j = (range.max - range.min) / 200.0;
    const val = +range.value + e.deltaY * j;
    setValue(val);
  });

  document.addEventListener("mouseup", (e) => {
    vols[ctrl.id].barStillDown = false;
  }, true);

  document.addEventListener("touchend", (e) => {
   vols[ctrl.id].barStillDown = false;
  }, true);
}
