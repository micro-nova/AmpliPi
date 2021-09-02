/* Need to set up arrays that hold API data */
var zones = [];
var streams = [];
var groups = [];

$(function() {
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
          <input type="hidden" value="false" name="disabled">
          <input type="checkbox" id="disabled_state" name="disabled" value="true"${z.disabled ? " checked" : ""}>
          <label for="disabled_state">Disabled</label>
          <small id="disHelp" class="form-text text-muted">Disabling a zone removes its mute and volume controls. A zone should be disabled if it isn't going to be used, or has no speakers connected to it</small>
        </div>
      `;

      html += `
        <button type="submit" class="btn btn-secondary" aria-describedby="submitHelp">Save Changes</button>
        <small id="submitHelp" class="form-text text-muted"></small>
      </form>
      `;
    $("#settings-tab-zones-config").html(html);
  });

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
      success: updateSettings
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
