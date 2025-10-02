// -------------------------------- Inspector ---------------------------------

const inspector = new Object();
inspector.inspector_elements = {
    "stone" : {"title" : null, "containers" : new Object(), "values" : new Object()},
    "square" : {"title" : null, "containers" : new Object(), "values" : new Object()}
}
inspector.record_inspector_elements = function(which_inspector, element_name_list) {
    element_name_list.forEach(function(element_name, element_index) {
        inspector.inspector_elements[which_inspector]["containers"][element_name] = document.getElementById(`${which_inspector}_info_${element_name}_container`);
        inspector.inspector_elements[which_inspector]["values"][element_name] = document.getElementById(`${which_inspector}_info_${element_name}`);
    });
    inspector.inspector_elements[which_inspector]["title"] = document.getElementById(`${which_inspector}_inspector_title`);
}
inspector.display_value_list = function(which_inspector, element_name, value_list) {
    if (value_list.length == 0) {
        inspector.inspector_elements[which_inspector]["containers"][element_name].style.display = "none";
    } else {
        inspector.inspector_elements[which_inspector]["containers"][element_name].style.display = "block";
        html_object = "";
        for (let i = 0; i < value_list.length; i++) {
            html_object += `<p>${value_list[i]}</p>\n`;
        }
        inspector.inspector_elements[which_inspector]["values"][element_name].innerHTML = html_object;
    }
}


inspector.record_inspector_elements("stone", ["allegiance", "stone_type", "startpoint", "endpoint"]);
inspector.record_inspector_elements("square", ["active_effects", "activated_causes", "inactive_effects", "not_activated_causes"]);

inspector.reverse_causality_flags = []; // [round_n] = {"causes" : {"activated" : [], "not_activated" : [], "buffered" : []}, "effects" : {"active" : [], "inactive" : []}}
inspector.organise_reverse_causality_flags = function() {
    for (let round_n = 0; round_n <= active_round; round_n++) {
        inspector.reverse_causality_flags.push(new Object());
        inspector.reverse_causality_flags[round_n]["causes"] = {
            "activated" : [],
            "not_activated" : []
        }
        inspector.reverse_causality_flags[round_n]["effects"] = {
            "active" : [],
            "inactive" : [],
            "buffered" : []
        }
        // First, we check the non-buffered flags
        for (let passed_round_n = 0; passed_round_n < round_n; passed_round_n++) {
            for (let effect_i = 0; effect_i < effects[passed_round_n].length; effect_i++) {
                // Is effect active?
                if (scenarios[round_n]["effect_activity_map"][effects[passed_round_n][effect_i]]) {
                    inspector.reverse_causality_flags[round_n]["effects"]["active"].push(effects[passed_round_n][effect_i]);
                    // NOTE: If swapping, the corresponding cause may have been added on the last round, and will be encountered again!
                    inspector.reverse_causality_flags[round_n]["causes"]["activated"].push(scenarios[round_n]["effect_cause_map"][effects[passed_round_n][effect_i]]);
                } else {
                    inspector.reverse_causality_flags[round_n]["effects"]["inactive"].push(effects[passed_round_n][effect_i]);
                }

            }
            // Now we add the omitted non-buffered causes as not activated
            for (let cause_i = 0; cause_i < causes[passed_round_n].length; cause_i++) {
                // Is cause not activated?
                if (!(inspector.reverse_causality_flags[round_n]["causes"]["activated"].includes(causes[passed_round_n][cause_i]))) {
                    inspector.reverse_causality_flags[round_n]["causes"]["not_activated"].push(causes[passed_round_n][cause_i]);
                }

            }
        }
        // Now for the buffered flags: the effects are always inactive, for causes, it depends on the stone trajectory
        for (let effect_i = 0; effect_i < effects[round_n].length; effect_i++) {
            inspector.reverse_causality_flags[round_n]["effects"]["buffered"].push(effects[round_n][effect_i]);
        }
        for (let cause_i = 0; cause_i < causes[round_n].length; cause_i++) {
            if (!(inspector.reverse_causality_flags[round_n]["causes"]["activated"].includes(causes[round_n][cause_i]) || inspector.reverse_causality_flags[round_n]["causes"]["not_activated"].includes(causes[round_n][cause_i]))) {
                if (activated_buffered_causes[round_n].includes(causes[round_n][cause_i])) {
                    inspector.reverse_causality_flags[round_n]["causes"]["activated"].push(causes[round_n][cause_i]);
                } else {
                    inspector.reverse_causality_flags[round_n]["causes"]["not_activated"].push(causes[round_n][cause_i]);
                }
            }
        }
    }
}

// ----------------------- Human readable text methods ------------------------

inspector.human_readable_flag = function(action_role, flag_significance, flag_status, flag_ID) {
    // action_role defines the role of the flag in the sentence
    // flag_significance: cause or effect
    switch(action_role) {
        case "primary":
            switch(flag_significance) {
                case "effect":
                    switch(flag_status) {
                        case "active":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_in":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} time-jumps in`;
                                case "spawn_bomb":
                                    return `A bomb explodes`;

                            }
                        case "inactive":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_in":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} would time-jump in`;
                                case "spawn_bomb":
                                    return `A bomb would explode`;

                            }
                        case "buffered":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_in":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} is set to time-jump in`;
                                case "spawn_bomb":
                                    return `A bomb is set to explode`;

                            }
                    }
                case "cause":
                    switch(flag_status) {
                        case "activated":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_out":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} time-jumps out`;
                                case "attack":
                                    // switch stone type
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} attacks`;

                            }
                        case "not_activated":
                            switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                                case "time_jump_out":
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} would time-jump out`;
                                case "attack":
                                    // switch stone type
                                    return `A ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} would attack`;

                            }
                    }
            }
        case "secondary":
            switch(flag_significance) {
                case "effect":
                    switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                        case "time_jump_in":
                            return `causing a ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} to time-jump in`;
                        case "spawn_bomb":
                            return `causing a bomb to explode`;

                    }
                case "cause":
                    switch(reverse_causality_flag_properties[flag_ID]["flag_type"]) {
                        case "time_jump_out":
                            return `caused by a ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} time-jumping out`;
                        case "attack":
                            // switch stone type
                            return `caused by a ${stone_highlight(reverse_causality_flag_properties[flag_ID]["stone_ID"])} attacking`;

                    }
            }
    }
}

inspector.flag_description = function(flag_significance, flag_status, flag_ID) {
    // flag_significnce = effect or cause
    // NOTE: This function assumes selected_round is sane

    switch(flag_significance) {
        case "effect":
            primary_descriptor = inspector.human_readable_flag("primary", "effect", flag_status, flag_ID);
            if (["active", "buffered"].includes(flag_status)) {
                let corresponding_cause_ID = scenarios[selected_round]["effect_cause_map"][flag_ID];
                let cause_t = reverse_causality_flag_properties[corresponding_cause_ID]["t"];
                let cause_x = reverse_causality_flag_properties[corresponding_cause_ID]["x"];
                let cause_y = reverse_causality_flag_properties[corresponding_cause_ID]["y"];
                primary_descriptor += `, ${inspector.human_readable_flag("secondary", "cause", "activated", corresponding_cause_ID)} at ${square_highlight(cause_t, cause_x, cause_y)}`;
            }
            return primary_descriptor;
        case "cause":
            primary_descriptor = inspector.human_readable_flag("primary", "cause", flag_status, flag_ID);
            // We need to find the effect
            let corresponding_effect_ID = reverse_causality_flag_properties[flag_ID]["target_effect"];
            let corresponding_effect_status = undefined;
            let effect_statuses_to_try = ["active", "inactive", "buffered"];
            for (effect_status_index = 0; effect_status_index < effect_statuses_to_try.length; effect_status_index++) {
                if (inspector.reverse_causality_flags[selected_round]["effects"][effect_statuses_to_try[effect_status_index]].includes(corresponding_effect_ID)) {
                    corresponding_effect_status = effect_statuses_to_try[effect_status_index];
                    break;
                }
            }
            if (corresponding_effect_ID != undefined) {
                let effect_t = reverse_causality_flag_properties[corresponding_effect_ID]["t"];
                let effect_x = reverse_causality_flag_properties[corresponding_effect_ID]["x"];
                let effect_y = reverse_causality_flag_properties[corresponding_effect_ID]["y"];
                primary_descriptor += `, ${inspector.human_readable_flag("secondary", "effect", corresponding_effect_status, corresponding_effect_ID)} at ${square_highlight(effect_t, effect_x, effect_y)}`;
            }
            return primary_descriptor;
    }
}

inspector.endpoint_description = function(endpoint_event) {
    switch(endpoint_event) {
        case "setup":
            return "placed on setup";
        case "TJI":
            return "time-jumps-in";
        case "TJO":
            return "time-jumps-out";
        case "destruction":
            return "is destroyed";
        case "causally_free":
            return "becomes causally free";
        case "tag_locked":
            return "is tag-locked";
        case "unharmed":
            return "remains unharmed";
        default:
            return "UNKNOWN EVENT";
    }
}

inspector.square_type_description = function(board_static_val) {
    switch(board_static_val) {
        case " ":
            return "An empty square";
        case "X":
            return "A wall";
        default:
            return "UNKNOWN SQUARE";
    }
}

// ---------------------------- Stone info methods ----------------------------

// Selection mode methods - read only
inspector.selection_mode_enabled = false;
inspector.selection_mode_stone_ID = null;

// General stone properties

inspector.display_stone_info = function(x, y) {
    // Is there even a stone present?
    let stone_ID = find_stone_at_pos(x, y);
    inspector.inspector_elements["stone"]["title"].innerHTML = (stone_ID == null ? "No stone selected" : `A ${stone_highlight(stone_ID)} selected`);

    if (stone_ID != null) {
        inspector.display_value_list("stone", "allegiance", [stone_properties[stone_ID]["allegiance"]]);
        inspector.display_value_list("stone", "stone_type", [stone_properties[stone_ID]["stone_type"].toUpperCase()]);
        inspector.display_value_list("stone", "startpoint", [`Stone ${inspector.endpoint_description(stone_endpoints[selected_round][stone_ID]["start"]["event"])} at ${square_highlight(stone_endpoints[selected_round][stone_ID]["start"]["t"], stone_endpoints[selected_round][stone_ID]["start"]["x"], stone_endpoints[selected_round][stone_ID]["start"]["y"])}`]);
        inspector.display_value_list("stone", "endpoint", [`Stone ${inspector.endpoint_description(stone_endpoints[selected_round][stone_ID]["end"]["event"])} at ${square_highlight(stone_endpoints[selected_round][stone_ID]["end"]["t"], stone_endpoints[selected_round][stone_ID]["end"]["x"], stone_endpoints[selected_round][stone_ID]["end"]["y"])}`]);

        // Check if can be commanded
        if (stones_to_be_commanded.includes(stone_ID) && selected_round == active_round && selected_timeslice == active_timeslice && arrays_equal(stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID].slice(0, 2), [x, y])) {
            if (commander.command_checklist.includes(stone_ID)) {
                // Display commands
                inspector.display_stone_commands(stone_ID);
            } else {
                inspector.display_undo_button();
            }
        } else {
            inspector.display_stone_commands(null);
        }

    } else {
        inspector.display_value_list("stone", "allegiance", []);
        inspector.display_value_list("stone", "stone_type", []);
        inspector.display_value_list("stone", "startpoint", []);
        inspector.display_value_list("stone", "endpoint", []);
        inspector.display_stone_commands(null);
    }

    return stone_ID;
}

inspector.hide_stone_info = function() {
    inspector.inspector_elements["stone"]["title"].innerHTML = "No stone selected";
    inspector.display_value_list("stone", "allegiance", []);
    inspector.display_value_list("stone", "stone_type", []);
    inspector.display_value_list("stone", "startpoint", []);
    inspector.display_value_list("stone", "endpoint", []);
    // Hide commands
    inspector.display_stone_commands(null);
}

// --------------------------- Square info methods ----------------------------

inspector.highlighted_square = null;
inspector.set_square_highlight = function(new_square) {
    if (inspector.highlighted_square != null) {
        if (new_square == null) {
            // Change of the guard
            document.getElementById(`square_highlighter`).style.display = "none";
        } else if(!arrays_equal(new_square, inspector.highlighted_square)) {
            // Change of the guard
            document.getElementById(`square_highlighter`).style.display = "none";
        }
    }
    inspector.highlighted_square = new_square;
    if (inspector.highlighted_square != null) {
        document.getElementById(`square_highlighter`).style.display = "inline";
        document.getElementById(`square_highlighter`).style.transform = `translate(${inspector.highlighted_square[0] * 100}px,${inspector.highlighted_square[1] * 100}px)`;
    }
}

inspector.display_square_info = function(x, y) {

    // First, we find all reverse-causality flags associated with this square
    let active_effects_message_list = [];
    let inactive_effects_message_list = [];
    let activated_causes_message_list = [];
    let not_activated_causes_message_list = [];
    // Active effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["active"].length; effect_i++) {
        let active_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["active"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(active_effect_ID, selected_timeslice, x, y)) {
            active_effects_message_list.push(inspector.flag_description("effect", "active", active_effect_ID));
        }
    }
    // Inactive effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["inactive"].length; effect_i++) {
        let inactive_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["inactive"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(inactive_effect_ID, selected_timeslice, x, y)) {
            inactive_effects_message_list.push(inspector.flag_description("effect", "inactive", inactive_effect_ID));
        }
    }
    // Buffered effects
    for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["buffered"].length; effect_i++) {
        let buffered_effect_ID = inspector.reverse_causality_flags[selected_round]["effects"]["buffered"][effect_i];
        // Is flag at selected square?
        if (is_flag_at_pos(buffered_effect_ID, selected_timeslice, x, y)) {
            inactive_effects_message_list.push(inspector.flag_description("effect", "buffered", buffered_effect_ID));
        }
    }
    // Activated causes
    for (let cause_i = 0; cause_i < inspector.reverse_causality_flags[selected_round]["causes"]["activated"].length; cause_i++) {
        let activated_cause_ID = inspector.reverse_causality_flags[selected_round]["causes"]["activated"][cause_i];
        // Is flag at selected square?
        if (is_flag_at_pos(activated_cause_ID, selected_timeslice, x, y)) {
            activated_causes_message_list.push(inspector.flag_description("cause", "activated", activated_cause_ID));
        }
    }
    // Not activated causes
    for (let cause_i = 0; cause_i < inspector.reverse_causality_flags[selected_round]["causes"]["not_activated"].length; cause_i++) {
        let not_activated_cause_ID = inspector.reverse_causality_flags[selected_round]["causes"]["not_activated"][cause_i];
        // Is flag at selected square?
        if (is_flag_at_pos(not_activated_cause_ID, selected_timeslice, x, y)) {
            not_activated_causes_message_list.push(inspector.flag_description("cause", "not_activated", not_activated_cause_ID));
        }
    }

    // Display messages
    inspector.display_value_list("square", "active_effects", active_effects_message_list);
    inspector.display_value_list("square", "inactive_effects", inactive_effects_message_list);
    inspector.display_value_list("square", "activated_causes", activated_causes_message_list);
    inspector.display_value_list("square", "not_activated_causes", not_activated_causes_message_list);

    // Highligh square, reset stone highlight
    inspector.set_square_highlight([x, y]);
    inspector.inspector_elements["square"]["title"].innerHTML = `${inspector.square_type_description(board_static[x][y])} selected`;
    set_stone_highlight(null);
}


inspector.hide_square_info = function() {
    inspector.display_value_list("square", "active_effects", []);
    inspector.display_value_list("square", "inactive_effects", []);
    inspector.display_value_list("square", "activated_causes", []);
    inspector.display_value_list("square", "not_activated_causes", []);

    // Highligh square, reset stone highlight
    inspector.set_square_highlight(null);
    inspector.inspector_elements["square"]["title"].innerHTML = `No square selected`;
}

inspector.board_square_click = function(x, y){
    if (inspector.selection_mode_enabled) {
        for (let i = 0; i < inspector.selection_mode_options["squares"].length; i++) {
            if (inspector.selection_mode_options["squares"][i]["t"] == selected_timeslice && inspector.selection_mode_options["squares"][i]["x"] == x && inspector.selection_mode_options["squares"][i]["y"] == y) {
                inspector.select_square(x, y);
            }
        }
    } else {
        // We get information about the stone
        inspector.display_stone_info(x, y);
        // We get information about the square
        inspector.display_square_info(x, y);
    }
}

inspector.display_highlighted_info = function() {
    inspector.display_stone_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
    inspector.display_square_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
}

inspector.unselect_all = function() {
    inspector.hide_stone_info();
    inspector.hide_square_info();
}


function go_to_square(t, x, y, turn_off_tracking = true) {
    if (!inspector.selection_mode_enabled) {
        select_timeslice(t);
        show_stones_at_process(selected_round, selected_timeslice, "canon");
        show_time_jumps_at_time(selected_round, selected_timeslice);
        if (turn_off_tracking) {
            cameraman.track_stone(null);
        }
        cameraman.show_square(x, y);
        inspector.display_stone_info(x, y);
        inspector.display_square_info(x, y);
    }
}

function tracking_startpoint() {
    go_to_square(stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["t"], stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["x"], stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["y"], false)
}

function tracking_endpoint() {=
    go_to_square(stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["t"], stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["x"], stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["y"], false)
}

