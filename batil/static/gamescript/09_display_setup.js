// -------------------------- Initial display setup ---------------------------
var selected_round = active_round; // Selected by GUI logic, not affected by animations
var visible_round = selected_round; // Displayed by the GUI, affected by animations
var visible_process = "canon";

var selection_mode = false;

// Set up the camera
//cameraman.put_down_tripod();
cameraman.update_board_dimension();
cameraman.reset_camera();

// Set up commander if game in progress
if (game_status == "in_progress") {
    commander.initialise_command_checklist();
}

// Set up inspector
inspector.organise_reverse_causality_flags();
inspector.hide_stone_info();
inspector.hide_square_info();

// If the game state was updated automatically, we animate the latest changes. Otherwise, we display the active timeslice
if (last_displayed_turn < current_turn) {
    let last_displayed_turn_props = round_from_turn(last_displayed_turn);
    let last_displayed_round = last_displayed_turn_props[0];
    let last_displayed_timeslice = last_displayed_turn_props[1];

    show_canon_board_slice(last_displayed_round, last_displayed_timeslice);

    if (last_displayed_round < active_round) {
        // The game crossed into a new round. Let's ffw to it
        animation_manager.add_to_queue([["change_round", active_round, 0, ">|", "up"], ["reset_to_canon", active_round, 0]]);
        last_displayed_timeslice = 0;
        animation_manager.add_to_queue([["change_process", active_round, 0, "setup", false]]);
        for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
            animation_manager.add_to_queue([["change_process", active_round, 0, process_keys[process_key_index], false]]);
        }
    }

    //select_round(active_round, last_displayed_timeslice);
    // Now we add the animation for every timeslice in between
    for (t_i = last_displayed_timeslice; t_i < active_timeslice; t_i++) {
        //select_timeslice(selected_timeslice += 1);
        //select_timeslice(t_i);
        animation_manager.add_to_queue([["change_process", active_round, t_i, "canon", false]]);
        for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
            animation_manager.add_to_queue([["change_process", active_round, t_i + 1, process_keys[process_key_index], false]]);
        }
        animation_manager.add_to_queue([["reset_to_canon", active_round, t_i + 1]]);
    }
    select_round(active_round, active_timeslice);

} else {
    show_active_timeslice();

}

// If seconds_left_to_timeout is not null, we need to create a countdown.
function format_time(seconds) {
    const hours   = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs    = seconds % 60;

    // Hours can be arbitrary length, but minutes and seconds should be 2 digits
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function update_countdown() {
    const label = document.getElementById("time_countdown_label");
    if (seconds_left_to_timeout <= 0) {
        label.innerText = "Timeout";
        clearInterval(countdown_daemon);  // stop updating
        window.location.href = window.location.pathname;
    }

    label.innerText = format_time(seconds_left_to_timeout);
    seconds_left_to_timeout--;
}
if (seconds_left_to_timeout != null) {
    update_countdown();
    if (!did_player_finish_turn) {
        // Set up countdown daemon
        const countdown_daemon = setInterval(update_countdown, 1000);
    }
}

