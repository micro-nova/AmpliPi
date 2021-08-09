/* On page load, get list of current streams */
$(function() {
  var streams = [];

  $.get("/api/streams", function(data) {
    $.each(data.streams, function(k, v) {
      streams[v.id] = v;
      $("#settings-tab-inputs-stream-selection").append(
        '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
        v.name +
        ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + v.type + '</span>'
      );
    });
  });

  /* Show new stream options */
  $("#settings-tab-inputs-new-stream").click(function(){
    $("#settings-tab-inputs-stream-selection li").removeClass('active'); // De-select "active" stream on the left menu if had been selected
    $(this).addClass('active');
    $("#settings-tab-inputs-stream-title").text("Add a new stream to AmpliPi");
    var html = `
      <form id="settings-tab-inputs-new-stream-form">
        <div class="form-group">
          <label for="type">Stream Type</label>
          <select class="form-control" name="type" id="new_type" data-required="true">
            <option value="0">- Select a Stream Type -</option>
            <option value="shairport">AirPlay Device</option>
            <option value="dlna">DLNA</option>
            <option value="fmradio">FM Radio Station</option>
            <option value="internetradio">Internet Radio Station</option>
            <option value="pandora">Pandora Station</option>
            <option value="plexamp">Plexamp</option>
            <option value="spotify">Spotify Device</option>
          </select>
        </div>
        <div class="form-group">
          <label for="name">Stream Name</label>
          <input type="text" class="form-control" name="name" data-required="true">
        </div>

        <div id="pandora_settings" class="addl_settings" style="display:none;">
          <div class="form-group">
            <label for="user">Pandora Username</label>
            <input type="text" class="form-control" name="user" data-required="true">
          </div>
          <div class="form-group">
            <label for="user">Pandora Password</label>
            <input type="password" class="form-control" name="password" data-required="true">
          </div>
          <div class="form-group">
            <label for="user">Pandora Station ID</label>
            <input type="text" class="form-control" name="station" data-required="true">
          </div>
        </div>

        <div id="internetradio_settings" class="addl_settings" style="display:none;">
          <div class="form-group">
            <label for="user">Station Audio URL</label>
            <input type="text" class="form-control" name="url" id="url" aria-describedby="urlHelp" data-required="true">
            <small id="urlHelp" class="form-text text-muted">Audio URL must be supported by <a href="https://www.videolan.org/" target="_blank">VLC</a>.</small>
          </div>
          <div class="form-group">
            <label for="user">Station Logo</label>
            <input type="text" class="form-control" name="logo">
          </div>
        </div>

        <div id="fmradio_settings" class="addl_settings" style="display:none;">
          <div class="form-group">
            <label for="user">FM Frequency</label>
            <input type="text" class="form-control" name="freq" aria-describedby="freqHelp" data-required="true">
            <small id="freqHelp" class="form-text text-muted">Enter an FM frequency 87.5 to 107.9. Requires an RTL-SDR compatible USB dongle.</small>
          </div>
          <div class="form-group">
            <label for="user">Station Logo</label>
            <input type="text" class="form-control" name="logo" aria-describedby="logoHelp">
            <small id="logoHelp" class="form-text text-muted">Default built-in logo is: static/imgs/fmradio.png</small>
          </div>
        </div>

        <button type="submit" class="btn btn-secondary">Add Stream</button>
      </form>
      `;
    $("#settings-tab-inputs-config").html(html);
  });

  /* Show selected stream settings */
  $("#settings-tab-inputs-stream-selection").on("click", ".stream", function() {
    $('#settings-tab-inputs-stream-selection li').removeClass('active');
    $("#settings-tab-inputs-new-stream").removeClass('active');
    $(this).addClass('active');
    var s = streams[$(this).data("id")];

    $("#settings-tab-inputs-stream-title").text(s.name + " (" + s.type + ")");
    var html = `
      <input type="hidden" id="edit-sid" name="id" value="${s.id}">
      <form id="editStreamForm">
        <div class="form-group">
          <label for="name">Stream Name</label>
          <input type="text" class="form-control" name="name" value="${s.name}" data-required="true">
        </div>
      `;

      if (s.type == "pandora") {
        html += `
        <div class="form-group">
          <label for="user">Pandora Username</label>
          <input type="text" class="form-control" name="user" value="${s.user}" data-required="true">
        </div>
        <div class="form-group">
          <label for="user">Pandora Password</label>
          <input type="password" class="form-control" name="password" value="${s.password}" data-required="true">
        </div>
        <div class="form-group">
          <label for="user">Pandora Station ID</label>
          <input type="text" class="form-control" name="station" value="${s.station}" data-required="true">
        </div>
        `;
      }

      if (s.type == "internetradio") {
        html += `
        <div class="form-group">
          <label for="user">Station Audio URL</label>
          <input type="text" class="form-control" name="url" value="${s.url}" aria-describedby="urlHelp" data-required="true">
          <small id="urlHelp" class="form-text text-muted">Audio URL must be supported by <a href="https://www.videolan.org/" target="_blank">VLC</a>.</small>
        </div>
        <div class="form-group">
          <label for="user">Station Logo</label>
          <input type="text" class="form-control" name="logo" value="${s.logo}">
        </div>
        `;
      }

      if (s.type == "fmradio") {
        html += `
        <div class="form-group">
          <label for="user">FM Frequency</label>
          <input type="text" class="form-control" name="freq" value="${s.freq}" aria-describedby="freqHelp" data-required="true">
          <small id="freqHelp" class="form-text text-muted">Enter an FM frequency 87.5 to 107.9. Requires an RTL-SDR compatible USB dongle.</small>
        </div>
        <div class="form-group">
          <label for="user">Station Logo</label>XS
          <input type="text" class="form-control" name="logo" value="${s.logo}" aria-describedby="logoHelp">
          <small id="logoHelp" class="form-text text-muted">Default built-in logo is: static/imgs/fmradio.png</small>
        </div>
        `;
      }

      html += `
        <button type="submit" class="btn btn-secondary">Save Changes</button>
        <button type="button" class="btn btn-danger" style="float:right" id="delete" data-id="${s.id}">Delete Stream</button>
      </form>
      `;
    $("#settings-tab-inputs-config").html(html);
  });

  /* Show selected stream settings */
  $("#settings-tab-inputs-config").on("click", "#new_type", function() {
    $(".addl_settings").hide(); // Hide all additional settings
    if ($(this).val() == "pandora") { $("#pandora_settings").show(); }
    else if ($(this).val() == "internetradio") { $("#internetradio_settings").show(); }
    else if ($(this).val() == "fmradio") { $("#fmradio_settings").show(); }

  });

  /* Add New Stream and Reload Page */
  $("#settings-tab-inputs-config").on("submit", "#settings-tab-inputs-new-stream-form", function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var $form = $("#settings-tab-inputs-new-stream-form");
    var formData = getFormData($form);

    $.ajax({
      type: "POST",
      url: '/api/stream',
      data: JSON.stringify(formData),
      contentType: "application/json",
      success: function(result) {
        $("#settings-tab-inputs-stream-title").text("Select a stream");
        $("#settings-tab-inputs-stream-selection").empty();
        $("#settings-tab-inputs-config").html("");
        $.get("/api/streams", function(data) {
          $.each(data.streams, function(k, v) {
            streams[v.id] = v;
            $("#settings-tab-inputs-stream-selection").append(
              '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
              v.name +
              ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + v.type + '</span>'
            );
          });
        });
      }
    });
  });


  /* Save stream changes and reload page */
  $("#settings-tab-inputs-config").on("submit", "#editStreamForm", function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var $form = $("#editStreamForm");
    var validation = checkFormData($("#editStreamForm :input"));
    if (!validation) { return; }

    var formData = getFormData($form);

    $.ajax({
      type: "PATCH",
      url: '/api/streams/' + $("#edit-sid").val(),
      data: JSON.stringify(formData),
      contentType: "application/json",
      success: function(data) {
        $("#settings-tab-inputs-stream-title").text("Select a stream");
        $("#settings-tab-inputs-stream-selection").empty();
        $("#settings-tab-inputs-config").html("");

        $.each(data.streams, function(k, v) {
          streams[v.id] = v;
          $("#settings-tab-inputs-stream-selection").append(
            '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
            v.name +
            ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + v.type + '</span>'
          );
        });
      }
    });
  });


  /* Delete stream and reload stream list and settings */
  $("#settings-tab-inputs-config").on("click", "#delete", function() {
    $.ajax({
      url: '/api/streams/' + $(this).data("id"),
      type: 'DELETE',
      success: function(data) {
        // Reload stream list and settings
        $("#settings-tab-inputs-stream-title").text("Select a stream");
        $("#settings-tab-inputs-stream-selection").empty();
        $("#settings-tab-inputs-config").html("");

        $.each(data.streams, function(k, v) {
          streams[v.id] = v;
          $("#settings-tab-inputs-stream-selection").append(
            '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
            v.name +
            ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + v.type + '</span>'
          );
        });
      }
    });
  });

  /* Make sure all required field are filled */
  function checkFormData($form) {
    var isValid = true;
    $form.each(function() {console.log($(this).data("required"));
      if ($(this).data("required") == true && $(this).val() === '') {
        isValid = false;
        $(this).addClass('is-invalid');
      }
    });
    return isValid;
  }

  // Return form data in AmpliPi's JSON format */
  function getFormData($form) {
    var unindexed_array = $form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function(n, i){
        indexed_array[n['name']] = n['value'];
    });

    return indexed_array;
}
});
