
const icons = {
  'shairport' : '/static/shairport.png',
  'local'     : '/static/rca_inputs.svg',
  'pandora'   : '/static/pandora.png'
}

function onSrcInputChange(obj) {
  const input = obj.value;
  const src = obj.dataset.src;
  let req = {
    "command": "set_source",
    "id" : Number(src),
    "input" : input
  };
  sendRequest(req);
}

function onSrcAdd(obj) {
  const src = Number(obj.id.substring(1,2));
  const to_add = obj.value;
  if (to_add) {
    const type = to_add.substring(0,1);
    const id = Number(to_add.substring(1));
    let req = {};
    if (type == 'z'){
      req.command = 'set_zone';
    } else if (type == 'g') {
      req.command = 'set_group';
    }
    req.id = id;
    req.source_id = src;
    sendRequestAndReload(req, src);
  }
}

function onMuteToggle(icon) {
  let ctrl = icon.closest('.volume');
  let mute = !ctrl.classList.contains('muted');
  ctrl.classList.toggle('muted', mute); // immediately toggle the mute to give the user feedback
  let req = {};
  if (ctrl.dataset.hasOwnProperty('zone')) {
    req.command = 'set_zone';
    req.id = Number(ctrl.dataset.zone);
  } else if (ctrl.dataset.hasOwnProperty('group')) {
    req.command = 'set_group';
    req.id = Number(ctrl.dataset.group);
  }
  req.mute = mute;
  sendRequest(req);
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
    let req = {
      "command" : "set_stream",
      "id" : stream_id,
      "cmd" : command
    };
    sendRequest(req);
  }
}

function onPlay(ctrl) {
  sendStreamCommand(ctrl, 'play');
}

function onPause(ctrl) {
  sendStreamCommand(ctrl, 'pause');
}

function onNext(ctrl) {
  sendStreamCommand(ctrl, 'next');
}

function updateSourceView(status) {
  // update player state
  for (const src of status['sources']) {
    const stream_id = src.input.startsWith("stream=") ? src.input.replace("stream=", "") : undefined;
    let cover = $('#s' + src.id + '-player .cover img')[0];
    let artist = $('#s' + src.id + '-player .info .artist')[0];
    let album = $('#s' + src.id + '-player .info .album')[0];
    let song = $('#s' + src.id + '-player .info .song')[0];
    // play/pause switching
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
          try {
            // update albumn art
            cover.src = stream.info.img_url ? stream.info.img_url : icons['pandora'];
            artist.innerHTML = stream.info.artist ? stream.info.artist : "";
            album.innerHTML = stream.info.album ? stream.info.album : "";
            song.innerHTML = stream.info.track ? stream.info.track : "";
          } catch (err) {}
        } else if (stream.type == 'shairport') {
          cover.src = icons['shairport'];
          // TODO: populate shairport album info
          artist.innerHTML = '';
          album.innerHTML = '';
          song.innerHTML = '';
        }
      }
      const playing = stream.status == "playing";
      $('#s' + src.id + '-player .play')[0].style.visibility = playing ? "hidden" : "visible";
      $('#s' + src.id + '-player .pause')[0].style.visibility = playing ? "visible" : "hidden";
    } else {
      $('#s' + src.id + '-player .play')[0].style.visibility = "hidden";
      $('#s' + src.id + '-player .pause')[0].style.visibility = "hidden";
      $('#s' + src.id + '-player .step-foreward')[0].style.visibility = "hidden";
      $('#s' + src.id + '-player .slider')[0].style.visibility = "hidden";
      $('#s' + src.id + '-player .timer')[0].style.visibility = "hidden";
      cover.src = icons['local'];
      artist.innerHTML = src.name;
      album.innerHTML = '';
      song.innerHTML = '';
    }
    // update each source's input
    $("#s" + src.id + "-player")[0].dataset.srcInput = src.input;
    $("#s" + src.id + '-input option[value="' + src.input + '"]').attr('selected', 'selected')
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
  let response = await fetch('/api');
  let result = await response.json();
  onResponse(result);
  return result;
}
async function sendRequest(obj) {
  onRequest(obj)
  let response = await fetch('/api', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json;charset=utf-8'
    },
    body: JSON.stringify(obj)
  });
  let result = await response.json();
  onResponse(result);
}
// TODO: we shouldn't need to reload the page, this is a crutch
async function sendRequestAndReload(obj, src) {
  onRequest(obj)
  let response = await fetch('/api', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json;charset=utf-8'
    },
    body: JSON.stringify(obj)
  });
  let result = await response.json();
  onResponse(result);
  // reload the page, making sure to stay on the same source tab
  window.location.assign('/' + src);
}

// group and zone volume control
function onGroupVolChange(g, vol) {
  let req = {
    "command": "set_group",
    "id" : Number(g),
    "vol_delta" : Number(vol),
    "mute" : false
  };
  sendRequest(req)
}
function onZoneVolChange(z, vol) {
  let req = {
    "command": "set_zone",
    "id" : Number(z),
    "vol" : Number(vol),
    "mute" : false
  };
  sendRequest(req)
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

function initVolControl(ctrl) {
  const range = ctrl.querySelector("input[type=range]");
  const barHoverBox = ctrl.querySelector(".bar-hoverbox");
  const fill = ctrl.querySelector(".bar .bar-fill");

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
    if (ctrl.dataset.hasOwnProperty('zone')){
      onZoneVolChange(ctrl.dataset.zone, vol);
    } else if (ctrl.dataset.hasOwnProperty('group')) {
      onGroupVolChange(ctrl.dataset.group, vol);
    } else {
      console.log('volume control ' + ctrl.id + ' not bound to any zone or group');
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
