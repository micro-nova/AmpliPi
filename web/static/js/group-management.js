/* On page load, get list of current groups and zones */
$(function() {
  var groups = [];
  $.get("/api/groups", function(data) {
    $.each(data.groups, function(k, v) {
      groups[v.id] = v;
      $("#settings-tab-groups-selection").append(
        '<li class="list-group-item list-group-item-action list-group-item-dark man_group" style="vertical-align: bottom;" data-id="' + v.id + '">' +
        v.name
      );
    });
  });

  var zones = [];
  $.get("/api/zones", function(data) {
    $.each(data.zones, function(k, v) {
      zones[v.id] = v;
    });
  });

  /* Show new group options */
  $("#settings-tab-groups-new-group").click(function(){
    $("#settings-tab-groups-selection li").removeClass('active'); // De-select "active" group on the left menu if had been selected
    $(this).addClass('active');
    $("#settings-tab-groups-title").text("Add a new group to AmpliPi");
    var html = `
      <form id="settings-tab-groups-new-group-form">
        <div class="form-group">
          <label for="name">Group Name</label>
          <input type="text" class="form-control" name="name" id="grp_name" data-required="true">
        </div>

        <button type="submit" class="btn btn-secondary" aria-describedby="submitHelp">Add Group</button>
        <small id="submitHelp" class="form-text text-muted"></small>
      </form>
      `;
    $("#settings-tab-groups-config").html(html);
  });

  /* Show selected group settings */
  $("#settings-tab-groups-selection").on("click", ".man_group", function() {
    $('#settings-tab-groups-selection li').removeClass('active');
    $("#settings-tab-groups-new-group").removeClass('active');
    $(this).addClass('active');
    var g = groups[$(this).data("id")];
    console.log(g)
///////////////////////////////TODO BELOW THIS LINE////////////////////////
    $("#settings-tab-groups-title").text(g.name);
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

      if (s.type == "plexamp") {
        html += `
        <div class="form-group">
          <label for="user">UUID</label>
          <input type="text" class="form-control" name="client_id" id="client_id" aria-describedby="uuidHelp" value="${s.client_id}" data-required="true" readonly>
          <small id="uuidHelp" class="form-text text-muted">Click the 'Request Authentication' button to input your Plex credentials, generating a UUID and Token</small>
        </div>
        <div class="form-group">
          <button class="btn btn-success" onclick="plexamp_create_stream();" id="plexamp-connect">Request Authentication</button>
          <button class="btn btn-warning" onclick="window.location.reload();"style="display: none" id="plexamp-reset">Reset</button>
          <button class="btn btn-primary" onclick="window.location.reload();" style="display: none" id="plexamp-done"></button>
        </div>
        <div class="form-group">
          <label for="user">Authentication Token</label>
          <input type="text" class="form-control" name="token" id="token" aria-describedby="authHelp" value="${s.token}" data-required="true" readonly>
          <small id="authHelp" class="form-text text-muted">UUID and authToken will be provided after signing into your Plex account</small>
        </div>
        `;
      }

      if (s.type == null) {
        del = '<button type="button" class="btn btn-danger" style="display:none" id="delete" data-id="${s.id}">Delete Stream</button>'
      } else {
        del = '<button type="button" class="btn btn-danger" style="float:right" id="delete" data-id="${s.id}">Delete Stream</button>'
      }

      html += `
        <button type="submit" class="btn btn-secondary" aria-describedby="submitHelp">Save Changes</button>
        ${del}
        <small id="submitHelp" class="form-text text-muted"></small>
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
    else if ($(this).val() == "plexamp") { $("#plexamp_settings").show(); }

  });

  /* Add New Stream and Reload Page */
  $("#settings-tab-inputs-config").on("submit", "#settings-tab-inputs-new-stream-form", function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var $form = $("#settings-tab-inputs-new-stream-form");
    var validation = checkFormData($("#settings-tab-inputs-new-stream-form :input"))
    console.log(validation);
    if (!validation) { return; }

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
        $.get("/api/sources", function(data) {
          $.each(data.sources, function(k, v) {
            streams[v.id] = v;
            $("#settings-tab-inputs-stream-selection").append(
              '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
              v.name +
              ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + `rca ${v.id+1}` + '</span>'
            );
          });
        });
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
    var s = streams[document.getElementById('edit-sid').value];
    console.log(s)
    if (s.type == null) {
      var nurl = '/api/sources/'
    } else {
      var nurl = '/api/streams/'
    }

    $.ajax({
      type: "PATCH",
      url: nurl + $("#edit-sid").val(),
      data: JSON.stringify(formData),
      contentType: "application/json",
      success: function(data) {
        $("#settings-tab-inputs-stream-title").text("Select a stream");
        $("#settings-tab-inputs-stream-selection").empty();
        $("#settings-tab-inputs-config").html("");

        $.get("/api/sources", function(data) {
          $.each(data.sources, function(k, v) {
            streams[v.id] = v;
            $("#settings-tab-inputs-stream-selection").append(
              '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
              v.name +
              ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + `rca ${v.id+1}` + '</span>'
            );
          });
        });
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


  /* Delete stream and reload stream list and settings */
  $("#settings-tab-inputs-config").on("click", "#delete", function() {
    $.ajax({
      url: '/api/streams/' + document.getElementById("edit-sid").value,
      type: 'DELETE',
      success: function(data) {
        // Reload stream list and settings
        $("#settings-tab-inputs-stream-title").text("Select a stream");
        $("#settings-tab-inputs-stream-selection").empty();
        $("#settings-tab-inputs-config").html("");

        $.get("/api/sources", function(data) {
          $.each(data.sources, function(k, v) {
            streams[v.id] = v;
            $("#settings-tab-inputs-stream-selection").append(
              '<li class="list-group-item list-group-item-action list-group-item-dark stream" style="vertical-align: bottom;" data-id="' + v.id + '">' +
              v.name +
              ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + `rca ${v.id+1}` + '</span>'
            );
          });
        });
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

  /* Make sure all required field are filled */
  function checkFormData($form) {
    var isValid = true;
    var sub_text = document.getElementById('submitHelp');
    sub_text.textContent = "";
    $form.each(function() {console.log($(this).data("required"));
      if ($(this).data("required") == true && $(this).val() === '' && $(this).is(':visible')) {
        isValid = false;
        sub_text.textContent = "Please fill out all required fields.";
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
