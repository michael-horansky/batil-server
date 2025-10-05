// ----------------------------------------------------------------------------
// ---------------------------------- Events ----------------------------------
// ----------------------------------------------------------------------------

// Keyboard shortcuts
var KEYBOARD_SHORTCUTS = {};

function register_shortcut(key, func, args) {
    // key is a string, func is a function, args is a list
    KEYBOARD_SHORTCUTS[key] = [func, args];
}
function remove_shortcut(key) {
    // removes shortcut if it exists
    if (KEYBOARD_SHORTCUTS[key] != null) {
        delete KEYBOARD_SHORTCUTS[key];
    }
}
function access_shortcut(key) {
    // a key was pressed which is associated to a shortcut
    if (KEYBOARD_SHORTCUTS[key] != null) {
        KEYBOARD_SHORTCUTS[key][0](...(KEYBOARD_SHORTCUTS[key][1] || []));
    }
}

function parse_keydown_event(event) {
    //alert(event.key);
    // If the focus is on a textbox, we ignore keypresses
    if (event.target.tagName === "INPUT" ||
        event.target.tagName === "TEXTAREA" ||
        event.target.isContentEditable) {
        return;
    }
    switch(event.key) {
        case "z":
            show_prev_timeslice();
            break;
        case "x":
            show_active_timeslice();
            break;
        case "c":
            show_next_timeslice();
            break;
        case "ArrowRight":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(1);
                document.getElementById(`azimuth_indicator_1`).style["fill-opacity"] = 0.7;
            } else {
                show_next_round();
            }
            break
        case "ArrowLeft":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(3);
                document.getElementById(`azimuth_indicator_3`).style["fill-opacity"] = 0.7;
            } else {
                show_prev_round();
            }
            break
        case "ArrowUp":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(0);
                document.getElementById(`azimuth_indicator_0`).style["fill-opacity"] = 0.7;
            } else {
                show_active_round();
            }
            break
        case "ArrowDown":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(2);
                document.getElementById(`azimuth_indicator_2`).style["fill-opacity"] = 0.7;
            }
            break
        case "q":
            cameraman.zoom_key_down("in");
            break;
        case "e":
            cameraman.zoom_key_down("out");
            break;
        case "r":
            if (cameraman.camera_zoom_status == "running") {
                clearInterval(cameraman.camera_zoom_daemon);
                cameraman.camera_zoom_status = "idle";
            }
            cameraman.reset_camera();
            break;
        case "f":
            if (cameraman.camera_zoom_status == "running") {
                clearInterval(cameraman.camera_zoom_daemon);
                cameraman.camera_zoom_status = "idle";
            }
            cameraman.fov_coef = 1.0;
            cameraman.apply_camera();
            break;
        case "w":
            cameraman.move_key_down(event.key);
            break;
        case "d":
            cameraman.move_key_down(event.key);
            break;
        case "s":
            cameraman.move_key_down(event.key);
            break;
        case "a":
            cameraman.move_key_down(event.key);
            break;
        // inspector highlight manipulation
        case "i":
            inspector.move_selection("up");
            break;
        case "j":
            inspector.move_selection("left");
            break;
        case "k":
            inspector.move_selection("down");
            break;
        case "l":
            inspector.move_selection("right");
            break;
        case "Escape":
            // The "Escape" behaviour is highly contextual, and the different
            // contexts it affects are sorted by priority as follows:
            //   1. Exits selection mode if board is in selection mode--otherwise,
            //   2. turns off tracking if tracking exists--otherwise,
            //   3. unselects square if selected
            if (inspector.selection_mode_enabled) {
                inspector.turn_off_selection_mode();
            } else if (cameraman.tracking_stone != null) {
                cameraman.track_stone(null);
            } else if (inspector.highlighted_square != null) {
                inspector.unselect_all();
            }
            break;
        case "Enter":
            // If selection mode is open, submits selection. Otherwise, if all commands were added, submits entire turn.
            if (inspector.selection_mode_enabled && (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false && inspector.selection_mode_information_level["swap_effect"] == false)) {
                inspector.submit_selection();
            } else if (["GAME", "TUTORIAL"].includes(client_access_context)) {
                if (!(commander.command_checklist.length > 0 || did_player_finish_turn)) {
                    document.getElementById("command_form").submit();
                }
            }
            break;
        default:
            // We check if a shortcut is registered for this
            access_shortcut(event.key);

    }
}
function parse_keyup_event(event) {
    //alert(event.key);
    switch(event.key) {
        case "ArrowRight":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_1`).style["fill-opacity"] = 0.5;
            }
            break
        case "ArrowLeft":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_3`).style["fill-opacity"] = 0.5;
            }
            break
        case "ArrowUp":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_0`).style["fill-opacity"] = 0.5;
            }
            break
        case "ArrowDown":
            if (inspector.selection_mode_enabled) {
                document.getElementById(`azimuth_indicator_2`).style["fill-opacity"] = 0.5;
            }
            break
        case "q":
            cameraman.zoom_key_up("in");
            break;
        case "e":
            cameraman.zoom_key_up("out");
            break;
        case "w":
            cameraman.move_key_up(event.key);
            break;
        case "d":
            cameraman.move_key_up(event.key);
            break;
        case "s":
            cameraman.move_key_up(event.key);
            break;
        case "a":
            cameraman.move_key_up(event.key);
            break;

    }
}


function show_next_timeslice(){
    if (timeslice_navigation_enabled && (selected_timeslice < t_dim - 1)) {
        if (inspector.selection_mode_enabled) {
            inspector.unselect_square();
        }
        select_timeslice(selected_timeslice += 1);
        animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice - 1, "canon", false]]);
        for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
            animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice, process_keys[process_key_index], false]]);
        }
        animation_manager.add_to_queue([["reset_to_canon", selected_round, selected_timeslice]]);
    } else if (timeslice_navigation_enabled && round_navigation_enabled && (selected_timeslice == t_dim - 1) && (selected_round < active_round)) {
        select_timeslice(0);
        show_next_round();
    }
}

function show_prev_timeslice(){
    if (timeslice_navigation_enabled && (selected_timeslice > 0)) {
        if (inspector.selection_mode_enabled) {
            inspector.unselect_square();
        }
        select_timeslice(selected_timeslice -= 1);
        for (let process_key_index = process_keys.length - 2; process_key_index >= 0; process_key_index--) {
            animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice + 1, process_keys[process_key_index], true]]);
        }
        animation_manager.add_to_queue([["change_process", selected_round, selected_timeslice, "canon", true]]);
        animation_manager.add_to_queue([["reset_to_canon", selected_round, selected_timeslice]]);
    } else if (timeslice_navigation_enabled && round_navigation_enabled && (selected_timeslice == 0) && (selected_round > 0)) {
        select_timeslice(t_dim - 1);
        show_prev_round();
    }
}

function show_active_timeslice(){
    // Always shows the timeslice corresponding to current_turn
    if (timeslice_navigation_enabled) {
        if (inspector.selection_mode_enabled) {
            inspector.unselect_square();
        }
        animation_manager.clear_queue();
        select_timeslice(active_timeslice);
        show_canon_board_slice(selected_round, selected_timeslice);
        cameraman.apply_tracking();
    }
}

function show_next_round() {
    if (round_navigation_enabled && (selected_round < active_round)) {
        select_round(selected_round += 1);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, ">>", "up"], ["reset_to_canon", selected_round, selected_timeslice]]);
        if (selected_timeslice == 0) {
            // We also show how the setup changed
            animation_manager.add_to_queue([["change_process", selected_round, 0, "setup", false]]);
            for (let process_key_index = 0; process_key_index < process_keys.length - 1; process_key_index++) {
                animation_manager.add_to_queue([["change_process", selected_round, 0, process_keys[process_key_index], false]]);
            }
            animation_manager.add_to_queue([["reset_to_canon", selected_round, 0]]);
        }
    }
}

function show_prev_round() {
    if (round_navigation_enabled && (selected_round > 0)) {
        select_round(selected_round -= 1);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, "<<", "down"], ["reset_to_canon", selected_round, selected_timeslice]]);
    }
}

function show_active_round() {
    if (round_navigation_enabled && (selected_round != active_round)) {
        select_round(active_round);
        animation_manager.add_to_queue([["change_round", selected_round, selected_timeslice, ">|", "up"], ["reset_to_canon", selected_round, selected_timeslice]]);
    }
}


