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
if (game_status == "in_progress" && ["A", "B"].includes(editor_role)) {
    commander.initialise_command_checklist();
}

// Set up inspector
inspector.organise_reverse_causality_flags();
inspector.hide_stone_info();
inspector.hide_square_info();

// If the game state was updated automatically, we animate the latest changes. Otherwise, we display the active timeslice
let last_displayed_turn_props = round_from_turn(last_displayed_turn);
let last_displayed_round = last_displayed_turn_props[0];
let last_displayed_timeslice = last_displayed_turn_props[1];

show_canon_board_slice(last_displayed_round, last_displayed_timeslice);
select_round(last_displayed_round, last_displayed_timeslice);
