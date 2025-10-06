// ----------------------------------------------------------------------------
// ------------------------------ Document setup ------------------------------
// ----------------------------------------------------------------------------

var all_factions = ["GM"].concat(factions)

var timeslice_navigation_enabled = true;
var round_navigation_enabled = true;

function set_timeslice_navigation(val) {
    timeslice_navigation_enabled = val;
    if (val) {
        let timeslice_buttons = document.getElementsByClassName("board_control_panel_button");
        for (i = 0; i < timeslice_buttons.length; i++) {
            timeslice_buttons[i].style.fill = "pink";
        }
    } else {
        let timeslice_buttons = document.getElementsByClassName("board_control_panel_button");
        for (i = 0; i < timeslice_buttons.length; i++) {
            timeslice_buttons[i].style.fill = "grey";
        }
    }
}

function set_round_navigation(val) {
    round_navigation_enabled = val;
    if (val) {
        let round_buttons = document.getElementsByClassName("game_control_panel_button");
        for (i = 0; i < round_buttons.length; i++) {
            round_buttons[i].style.fill = "pink";
        }
    } else {
        let round_buttons = document.getElementsByClassName("game_control_panel_button");
        for (i = 0; i < round_buttons.length; i++) {
            round_buttons[i].style.fill = "grey";
        }
    }
}

var selected_timeslice = 0; // this is the timeslice queued up to be displayed. The gameside label shows this number. Logic happens according to this number.
var visible_timeslice = 0; // this is the timeslice currently displayed by the animation. It is dragged by the animation and may not correspond to selected_timeslice.

let current_turn_props = round_from_turn(current_turn);

const active_round = current_turn_props[0];
const active_timeslice = current_turn_props[1];

// --------------------------- Fast animation setup ---------------------------

// initialise flat stone ID list for quick animations
var flat_stone_IDs = [];
all_factions.forEach(function(faction, faction_index) {
    faction_armies[faction].forEach(function(stone_ID, stone_index){
        flat_stone_IDs.push(stone_ID);
    });
});

// initialise inbetweens
// inbetweens[round][t][process] = {
//     "redundant" : true if start state and end state are equal
//     "cont_stones" : [list of stone IDs of stones existing at this process and next process],
//     "cont_stones_states" : [start_state_matrix, end_state_matrix],
//     "dest_stones" : [list of stone IDs destroyed by next process],
//     "dest_stones_states" : [state matrix for destroyed stones at this process],
//     "new_stones" : [list of stone IDs created by next process],
//     "new_stones_states" : [state matrix for created stones at next process],
//     "hide_stones" : [list of stone IDs of stones which are not placed on board at either this or the next process],
//     "new_time_jumps" : [list of used and unused time jump marker ids to fade in, corresponding list of types],
//     "old_time_jumps" : [list of used and unused time jump marker ids to fade out, corresponding list of types],
//     "captured_bases" : [list of captured base IDs, list of old allegiances, list of new allegiances],
//     "stable_bases" : [list of uncaptured base IDs, list of allegiances] -- only non-empty when end_process is canon!
// }

// The process tagscreens -> canon is never redundant, since we need to let the sand in the hourglasses fall

const process_keys = ["flags", "pushes", "destructions", "tagscreens", "canon"];
const inbetweens = [];
for (let inbetween_round_index = 0; inbetween_round_index <= active_round; inbetween_round_index++) {
    inbetweens.push([]);

    for (let inbetween_time = 0; inbetween_time < t_dim; inbetween_time++) {
        inbetweens[inbetween_round_index].push(new Object());

        if (inbetween_time == 0) {
            // We add a special inbetween object which describes the "setup" start process for the setup -> time-slice 0 animation (i.e. the new time jumps)
            let start_process = "setup";
            inbetweens[inbetween_round_index][inbetween_time][start_process] = new Object();
            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones_states"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones_states"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["hide_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["captured_bases"] = [[], [], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["stable_bases"] = [[], []];
            let is_redundant = true;
            let end_process = process_keys[0];
            let end_time = 0;
            for (let stone_ID_index = 0; stone_ID_index < flat_stone_IDs.length; stone_ID_index++) {
                let start_state = stone_trajectories[0][inbetween_time]["canon"][flat_stone_IDs[stone_ID_index]];
                let end_state = stone_trajectories[inbetween_round_index][end_time][end_process][flat_stone_IDs[stone_ID_index]];
                if (start_state == null) {
                    if (end_state == null) {
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["hide_stones"].push(flat_stone_IDs[stone_ID_index]);
                    } else {
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones"].push(flat_stone_IDs[stone_ID_index]);
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones_states"].push(end_state.slice());
                        is_redundant = false;
                    }
                } else {
                    if (end_state == null) {
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones"].push(flat_stone_IDs[stone_ID_index]);
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones_states"].push(start_state.slice());
                        is_redundant = false;
                    } else {
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones"].push(flat_stone_IDs[stone_ID_index]);
                        let start_state_copy = start_state.slice();
                        let end_state_copy = end_state.slice();
                        if (!(arrays_equal(start_state, end_state))) {
                            is_redundant = false;
                        }
                        // If the stone rotates, we want to choose the sensible rotation direction
                        if (end_state_copy[2] - start_state_copy[2] > 2) {
                            end_state_copy[2] -= 4;
                        }
                        if (end_state_copy[2] - start_state_copy[2] < -2) {
                            end_state_copy[2] += 4;
                        }
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"][0].push(start_state_copy);
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"][1].push(end_state_copy);

                    }
                }
            }
            for (let x = 0; x < x_dim; x++) {
                for (let y = 0; y < y_dim; y++) {
                    let used_tj_marker = inds(time_jumps[inbetween_round_index], [end_time, x, y, "used"]);
                    let unused_tj_marker = inds(time_jumps[inbetween_round_index], [end_time, x, y, "unused"]);
                    if (used_tj_marker != undefined) {
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][0].push(`used_time_jump_marker_${x}_${y}`);
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][1].push(`used_${used_tj_marker}`);
                        is_redundant = false;
                    }
                    if (unused_tj_marker != undefined) {
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][0].push(`unused_time_jump_marker_${x}_${y}`);
                        inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][1].push(`unused_${unused_tj_marker}`);
                        is_redundant = false;
                    }
                }
            }
            inbetweens[inbetween_round_index][inbetween_time][start_process]["redundant"] = is_redundant;
        }

        for (let inbetween_process_index = 0; inbetween_process_index < process_keys.length; inbetween_process_index++) {
            let start_process = process_keys[inbetween_process_index];
            inbetweens[inbetween_round_index][inbetween_time][start_process] = new Object();
            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones_states"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones_states"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["hide_stones"] = [];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"] = [[], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["captured_bases"] = [[], [], []];
            inbetweens[inbetween_round_index][inbetween_time][start_process]["stable_bases"] = [[], []];
            // We initialise the current inbetween
            if (inbetween_time == t_dim - 1 && start_process == "canon") {
                // This is the final state of the final timeslice, and therefore cannot be animated into a "next" state.
                inbetweens["redundant"] = true;
            } else {
                let is_redundant = true;

                let end_process;
                let end_time;
                if (start_process == "canon") {
                    end_process = process_keys[0];
                    end_time = inbetween_time + 1;
                } else {
                    end_process = process_keys[inbetween_process_index + 1];
                    end_time = inbetween_time;
                }
                // If start process if "destructions", tagscreens present make the animation not redundant
                // If start process is "tagscreens", then the animation shows stone and board actions. Therefore if any such (non-tagscreen) actions exist, this animation is not redundant, even if no stone state changes.
                /*if (start_process == "destructions") {
                    for (let b_i = 0; b_i < board_actions[inbetween_round_index][inbetween_time].length; b_i++) {
                        if (["tagscreen_lock", "tagscreen_unlock", "tagscreen_hide"].includes(board_actions[inbetween_round_index][inbetween_time][b_i][0])) {
                            is_redundant = false;
                            break;
                        }
                    }
                }
                if (start_process == "tagscreens") {
                    if (stone_actions[inbetween_round_index][inbetween_time].length > 0) {
                        is_redundant = false;
                    }
                    for (let b_i = 0; b_i < board_actions[inbetween_round_index][inbetween_time].length; b_i++) {
                        if (!["tagscreen_lock", "tagscreen_unlock", "tagscreen_hide"].includes(board_actions[inbetween_round_index][inbetween_time][b_i][0])) {
                            is_redundant = false;
                            break;
                        }
                    }
                }*/
                // stone actions
                if (start_process == "tagscreens") {
                    if (stone_actions[inbetween_round_index][inbetween_time].length > 0) {
                        is_redundant = false;
                    }
                }
                // If board actions included for this start_process, animation is not redundant
                for (let b_a_i = 0; b_a_i < board_actions_by_s_process[start_process].length; b_a_i++) {
                    if (board_actions[inbetween_round_index][inbetween_time][board_actions_by_s_process[start_process][b_a_i]].length > 0) {
                        is_redundant = false;
                        break;
                    }
                }

                for (let stone_ID_index = 0; stone_ID_index < flat_stone_IDs.length; stone_ID_index++) {
                    let start_state = stone_trajectories[inbetween_round_index][inbetween_time][start_process][flat_stone_IDs[stone_ID_index]];
                    let end_state = stone_trajectories[inbetween_round_index][end_time][end_process][flat_stone_IDs[stone_ID_index]];
                    if (start_state == null) {
                        if (end_state == null) {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["hide_stones"].push(flat_stone_IDs[stone_ID_index]);
                        } else {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones"].push(flat_stone_IDs[stone_ID_index]);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["new_stones_states"].push(end_state.slice());
                            is_redundant = false;
                        }
                    } else {
                        if (end_state == null) {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones"].push(flat_stone_IDs[stone_ID_index]);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["dest_stones_states"].push(start_state.slice());
                            is_redundant = false;
                        } else {
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones"].push(flat_stone_IDs[stone_ID_index]);
                            let start_state_copy = start_state.slice();
                            let end_state_copy = end_state.slice();
                            if (!(arrays_equal(start_state, end_state))) {
                                is_redundant = false;
                            }
                            // If the stone rotates, we want to choose the sensible rotation direction
                            if (end_state_copy[2] - start_state_copy[2] > 2) {
                                end_state_copy[2] -= 4;
                            }
                            if (end_state_copy[2] - start_state_copy[2] < -2) {
                                end_state_copy[2] += 4;
                            }
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"][0].push(start_state_copy);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["cont_stones_states"][1].push(end_state_copy);

                        }
                    }
                }

                // We check the time jump fades

                // If the end process is the first process in process_keys, if there are time jumps associated with end time, the animation is not redundant
                // Ditto for start process being "canon" and start time being associated with time jumps
                if (end_process == process_keys[0]) {
                    for (let x = 0; x < x_dim; x++) {
                        for (let y = 0; y < y_dim; y++) {
                            let used_tj_marker = inds(time_jumps[inbetween_round_index], [end_time, x, y, "used"]);
                            let unused_tj_marker = inds(time_jumps[inbetween_round_index], [end_time, x, y, "unused"]);
                            if (used_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][0].push(`used_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][1].push(`used_${used_tj_marker}`);
                                is_redundant = false;
                            }
                            if (unused_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][0].push(`unused_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["new_time_jumps"][1].push(`unused_${unused_tj_marker}`);
                                is_redundant = false;
                            }
                        }
                    }
                }
                if (start_process == "canon") {
                    for (let x = 0; x < x_dim; x++) {
                        for (let y = 0; y < y_dim; y++) {
                            let used_tj_marker = inds(time_jumps[inbetween_round_index], [inbetween_time, x, y, "used"]);
                            let unused_tj_marker = inds(time_jumps[inbetween_round_index], [inbetween_time, x, y, "unused"]);
                            if (used_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][0].push(`used_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][1].push(`used_${used_tj_marker}`);
                                is_redundant = false;
                            }
                            if (unused_tj_marker != undefined) {
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][0].push(`unused_time_jump_marker_${x}_${y}`);
                                inbetweens[inbetween_round_index][inbetween_time][start_process]["old_time_jumps"][1].push(`unused_${unused_tj_marker}`);
                                is_redundant = false;
                            }
                        }
                    }
                }

                // If the end process is canon, then we need to check if any base was captured
                if (end_process == "canon") {
                    for (let b_i = 0; b_i < bases.length; b_i++) {
                        is_redundant = false;
                        let old_allegiance = null;
                        if (inbetween_time == 0) {
                            // we compare to the setup
                            old_allegiance = base_trajectories[0][0][bases[b_i]][2];
                        } else {
                            old_allegiance = base_trajectories[inbetween_round_index][inbetween_time - 1][bases[b_i]][2];
                        }
                        let new_allegiance = base_trajectories[inbetween_round_index][inbetween_time][bases[b_i]][2];
                        if (old_allegiance != new_allegiance) {
                            // base was captured
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["captured_bases"][0].push(`base_${bases[b_i]}`);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["captured_bases"][1].push(old_allegiance);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["captured_bases"][2].push(new_allegiance);
                        } else {
                            // base is stable
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["stable_bases"][0].push(`base_${bases[b_i]}`);
                            inbetweens[inbetween_round_index][inbetween_time][start_process]["stable_bases"][1].push(old_allegiance);
                        }
                    }
                }


                inbetweens[inbetween_round_index][inbetween_time][start_process]["redundant"] = is_redundant;
            }
        }
    }
}

