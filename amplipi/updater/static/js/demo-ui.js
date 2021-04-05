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
  // TODO: hide file uploader
  // TODO: setup SSE events, for intermediate step info
  var source = new EventSource("update/install/progress");
  source.onmessage = function(event) {
    var data = JSON.parse(event.data);
    ui_show_update_progress(data);
    if (data.type == 'success' || data.type == 'error') {
      source.close();
    }
  };
  fetch("update/install"); // start the install TODO: check response
}

function ui_show_update_progress(status) {
  // assumes status {'message': str, 'type': 'info'|'warning'|'error'|'success'}
  let color = status.type == 'error' ? 'danger' : status.type;
  ui_add_log(status.message, color);
}

function upload_software_update() {
  let data = new FormData();
  let file = $('#update-file-selector')[0].files[0];
  data.append('file', file);
  try{
    fetch('/update/upload', {
      method: 'POST',
      body: data,
    }).then((response) => {
      ui_add_log('file uploaded', 'info');
      ui_begin_update();
    });
  } catch(e) {
    ui_add_log(e, 'danger');
  }
}
