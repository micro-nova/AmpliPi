/* Set up the necessary arrays and populate them */
var streams = [];
var zones = [];
var groups = [];
updateSettings();

/* Main function "on load" */
$(function() {
  /* Show new group options */
  $("#settings-tab-groups-new-group").click(function(){
    $("#settings-tab-groups-selection li").removeClass('active'); // De-select "active" group on the left menu if had been selected
    $(this).addClass('active');
    $("#settings-tab-groups-title").text("Add a new group to AmpliPi");
    var zone_html = ``;

    for (const zone in zones) {
      zone_html += `
      <option value="${zone}">${zones[zone].name}</option>
      `;
    };

    var html = `
      <form id="settings-tab-groups-new-group-form">
        <div class="form-group">
          <label for="name">Group Name</label>
          <input type="text" class="form-control" name="name" id="grp_name" data-required="true">
        </div>
        <div class="form-group">
          <select class="selectpicker" id="zone-picker" multiple>
            ${zone_html}
          </select>
        </div>
        <button type="submit" class="btn btn-secondary" aria-describedby="submitHelp">Add Group</button>
        <small id="submitHelp" class="form-text text-muted"></small>
      </form>
      `;
    $("#settings-tab-groups-config").html(html);
    /* Initialize selectpicker */
    $('.selectpicker').selectpicker();
  });

  /* Show selected group settings */
  $("#settings-tab-groups-selection").on("click", ".group-config", function() {
    $('#settings-tab-groups-selection li').removeClass('active');
    $("#settings-tab-groups-new-group").removeClass('active');
    $(this).addClass('active');
    var g = groups[$(this).data("id")];
    console.log(g)
    $("#settings-tab-groups-title").text(g.name);
    var zone_html = ``;

    for (const zone in zones) {
      const incl = g.zones.includes(parseInt(zone));
      zone_html += `
      <option value="${zone}"${incl ? " selected" : ""}>${zones[zone].name}</option>
      `;
    };

    var html = `
      <input type="hidden" id="edit-gid" name="id" value="${g.id}">
      <form id="editGroupForm">
        <div class="form-group">
          <label for="name">Group Name</label>
          <input type="text" class="form-control" name="name" value="${g.name}" data-required="true">
        </div>
        <div class="form-group">
          <select class="selectpicker" id="zone-picker" multiple>
            ${zone_html}
          </select>
        </div>
        <button type="submit" class="btn btn-secondary" aria-describedby="submitHelp">Save Changes</button>
        <button type="button" class="btn btn-danger" id="delete" data-id="${g.id}">Delete</button>
        <small id="submitHelp" class="form-text text-muted"></small>
      </form>
      `;
    $("#settings-tab-groups-config").html(html);
    /* Initialize selectpicker */
    $('.selectpicker').selectpicker();
  });

  /* Add New Group and Reload Page */
  $("#settings-tab-groups-config").on("submit", "#settings-tab-groups-new-group-form", function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var $form = $("#settings-tab-groups-new-group-form");
    var validation = checkFormData($("#settings-tab-groups-new-group-form :input"))
    console.log(validation);
    if (!validation) { return; }

    var formData = getFormData($form);
    console.log(formData);

    $.ajax({
      type: "POST",
      url: '/api/group',
      data: JSON.stringify(formData),
      contentType: "application/json",
      success: updateSettings
    });
  });


  /* Save group changes and reload page */
  $("#settings-tab-groups-config").on("submit", "#editGroupForm", function(e) {
    e.preventDefault(); // avoid to execute the actual submit of the form.

    var $form = $("#editGroupForm");
    var validation = checkFormData($("#editGroupForm :input"));
    if (!validation) { return; }

    var formData = getFormData($form);
    var g = groups[document.getElementById('edit-gid').value];
    console.log(g)

    $.ajax({
      type: "PATCH",
      url: '/api/groups/' + $("#edit-gid").val(),
      data: JSON.stringify(formData),
      contentType: "application/json",
      success: updateSettings
    });
  });


  /* Delete stream and reload stream list and settings */
  $("#settings-tab-groups-config").on("click", "#delete", function() {
    $.ajax({
      url: '/api/groups/' + document.getElementById("edit-gid").value,
      type: 'DELETE',
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
    var zone_array = [];
    const zone_sel = document.getElementById('zone-picker');
    for (const option of document.querySelectorAll('#zone-picker option')) {
      const val = Number.parseInt(option.value);
      if (option.selected) {
        zone_array.push(val);
      }
    }

    $.map(unindexed_array, function(n, i){
        indexed_array[n['name']] = n['value'];
        indexed_array['zones'] = zone_array;
    });

    return indexed_array;
  }
});
