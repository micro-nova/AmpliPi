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
  const src = obj.id.substring(1,2);
  const to_add = obj.value;
  if (to_add) {
    const type = to_add.substring(0,1);
    const id = Number(to_add.substring(1));
    let req = {
      "id" : id,
      "source_id" : src,
      "command" : ""
    };
    if (type == 'z'){
      req['command'] = 'set_zone';
    } else if (type == 'g') {
      req['command'] = 'set_group';
    }
    sendRequestAndReload(req, src);
  }
}

$(document).ready(function(){
  $('a[data-toggle="tab"]').on('show.bs.tab', function (e) {
    let new_src_sel = '#' + e.target.id + '-input';
    let old_src_sel = '#' + e.relatedTarget.id + '-input';
    $(new_src_sel)[0].style.display = "block"; // newly activated tab
    $(old_src_sel)[0].style.display = "none"; // previously active tab
  });
});

//  TODO: is any of this needed? it is from the media player pen we started from
var myMedia = document.createElement('audio');
$('#player').append(myMedia);
myMedia.id = "myMedia";
function setVolume(myVolume) {
  var myMedia = document.getElementById('myMedia');
  myMedia.volume = 0;
}

function updateVol(ctrl, vol) {
  let range = ctrl.querySelector("input[type=range]");
  const fill = ctrl.querySelector(".bar .bar-fill");
  const pct = (vol - range.min) / (range.max - range.min) * 100.0;
  fill.style.width = pct + "%";
  range.setAttribute("value", vol);
  range.dispatchEvent(new Event("change"));
}

function updateSourceView(status) {
  // update volumes
  const controls = document.querySelectorAll(".volume");
  for (const ctrl of controls) {
    if (ctrl.dataset.hasOwnProperty('zone')){
      let z = ctrl.dataset.zone;
      updateVol(ctrl, status.zones[z].vol);
    } else if (ctrl.dataset.hasOwnProperty('group')) {
      let g = ctrl.dataset.group;
      updateVol(ctrl, status.groups[g].vol_delta);
    } else {
      console.log('volume control ' + ctrl.id + ' not bound to any zone or group');
    }
  }
}

// basic request handling
function onRequest(req) {
  //document.getElementById("request").innerHTML = JSON.stringify(req);
}
function onResponse(resp) {
  updateSourceView(resp);
  //document.getElementById("response").innerHTML = JSON.stringify(resp);
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
  window.location.assign('test/' + src);
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

// new volume
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
