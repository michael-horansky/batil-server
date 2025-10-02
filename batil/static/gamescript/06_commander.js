// -------------------------------- Commander ---------------------------------
// Commander makes sure submission of commands is only possible once every c.f.
// stone has had a command specified, and marks stones to be commanded.
// Stones to be commanded: red square below. Commanded circles: green square.

const commander = new Object();
commander.command_checklist = [];
commander.touch_order = [];
commander.initialise_command_checklist = function() {
    for (i = 0; i < stones_to_be_commanded.length; i++) {
        commander.add_to_checklist(stones_to_be_commanded[i]);
    }
    commander.toggle_form_submission();
}

commander.add_to_checklist = function(stone_ID) {
    commander.command_checklist.push(stone_ID);
    if (commander.touch_order.includes(stone_ID)) {
        commander.touch_order.splice(commander.touch_order.indexOf(stone_ID), 1);
    }
    document.getElementById(`command_marker_${stone_ID}`).style.stroke = "red";
    document.getElementById(`command_marker_${stone_ID}`).style.display = "block";
    commander.toggle_form_submission();
}

commander.mark_as_checked = function(stone_ID) {
    commander.command_checklist.splice(commander.command_checklist.indexOf(stone_ID), 1);
    commander.touch_order.push(stone_ID);
    document.getElementById(`command_marker_${stone_ID}`).style.stroke = "green";
    commander.toggle_form_submission();
}

commander.update_meta_inputs = function() {
    // updated the meta fieldset of command form
    document.getElementById("touch_order_input").value = commander.touch_order.toString();
}

commander.toggle_form_submission = function() {
    if (commander.command_checklist.length > 0 || did_player_finish_turn) {
        document.getElementById("submit_commands_button").style.display = "none";
    } else {
        commander.update_meta_inputs();
        document.getElementById("submit_commands_button").style.display = "block";
    }
}

