/* On page load, get list of zones */
$(function() {
  var zones = [];
  $.get("/api/zones", function(data) {
    $.each(data.zones, function(k, v) {
      zones[v.id] = v;
      $("#settings-tab-zones-selection").append(
        '<li class="list-group-item list-group-item-action list-group-item-dark man_zone" style="vertical-align: bottom;" data-id="' + v.id + '">' +
        v.name +
        ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + (v.disabled ? 'disabled' : '') + '</span>'
      );
    });
  });

  /* Show selected zone settings */
  $("#settings-tab-zones-selection").on("click", ".man_zone", function() {
    $('#settings-tab-zones-selection li').removeClass('active');
    $(this).addClass('active');
    var z = zones[$(this).data("id")];
    console.log(z)

    $("#settings-tab-zones-title").text(z.name);
    var html = `
      <input type="hidden" id="edit-zid" name="id" value="${z.id}">
      <form id="editZoneForm">
        <div class="form-group">
          <label for="name">Zone Name</label>
          <input type="text" class="form-control" name="name" value="${z.name}" data-required="true">
        </div>
        <div class="form-group">
          <label for="disabled">Disabled?</label>
          <input type="text" class="form-control" name="disabled" aria-describedby="disHelp" value="${z.disabled}" data-required="true">
          <small id="disHelp" class="form-text text-muted">Enter 'true' to disable the Zone; enter 'false' to enable it.</small>
        </div>
      `;

      html += `
        <button type="submit" class="btn btn-secondary" aria-describedby="submitHelp">Save Changes</button>
        <small id="submitHelp" class="form-text text-muted"></small>
      </form>
      `;
    $("#settings-tab-zones-config").html(html);
  });

  /* Show selected zone settings */
  // $("#settings-tab-zones-config").on("click", "#new_type", function() {
  //   /* Do I need this for something? */
  // });

  /* Save zone changes and reload page */
  $("#settings-tab-zones-config").on("submit", "#editZoneForm", function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var $form = $("#editZoneForm");
    var validation = checkFormData($("#editZoneForm :input"));
    if (!validation) { return; }

    var formData = getFormData($form);
    var z = zones[document.getElementById('edit-zid').value];
    console.log(z)

    $.ajax({
      type: "PATCH",
      url: '/api/zones/' + $("#edit-zid").val(),
      data: JSON.stringify(formData),
      contentType: "application/json",
      success: function(data) {
        $("#settings-tab-zones-title").text("Select a zone");
        $("#settings-tab-zones-selection").empty();
        $("#settings-tab-zones-config").html("");

        $.get("/api/zones", function(data) {
          $.each(data.zones, function(k, v) {
            zones[v.id] = v;
            $("#settings-tab-zones-selection").append(
              '<li class="list-group-item list-group-item-action list-group-item-dark man_zone" style="vertical-align: bottom;" data-id="' + v.id + '">' +
              v.name +
              ' <span style="float:right;font-size:0.8rem;color:navy;line-height:25px;vertical-align: bottom;">' + (v.disabled ? 'disabled' : '') + '</span>'
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
