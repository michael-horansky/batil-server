// ----------------------------------------------------------------------------
// -------------------------------- Inspector ---------------------------------
// ----------------------------------------------------------------------------

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

// Selection mode methods

// Information level: for every "true", the user needs to specify the value of
// the corresponding arg key before submitting the command and exiting sel. m.
inspector.selection_mode_enabled = false;
inspector.selection_mode_stone_ID = null;
inspector.selection_mode_information_level = {"square" : false, "azimuth" : false, "swap_effect" : false, "choice_option" : false};
inspector.selection = {"square" : "NOT_SELECTED", "azimuth" : "NOT_SELECTED", "swap_effect" : "NOT_SELECTED", "choice_option" : "NOT_SELECTED"};
inspector.selection_submission = null;

inspector.selection_mode_options = new Object();

inspector.selection_keywords = ["stone_ID",
            "type",
            "t",
            "x",
            "y",
            "a",
            "target_t",
            "target_x",
            "target_y",
            "target_a",
            "swap_effect"];

inspector.turn_on_selection_mode = function(stone_ID, selection_mode_props) {
    cameraman.track_stone(null);
    inspector.selection_mode_enabled = true;
    // Commit current selection options to cache
    inspector.selection_mode_options = selection_mode_props;
    inspector.selection_mode_stone_ID = stone_ID;

    inspector.selection_mode_information_level["square"] = true;
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.selection_mode_information_level["swap_effect"] = true;
    inspector.selection_mode_information_level["choice_option"] = true;
    inspector.selection_mode_information_level["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["swap_effect"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["choice_option"] = "NOT_SELECTED";

    // Interrupt animations, disable tracking, force active round, disable round navigation, show selection highlights
    animation_manager.clear_queue();
    set_round_navigation(false);
    select_round(active_round);
    inspector.set_square_highlight(null);
    if (inspector.selection_mode_options["lock_timeslice"] != null) {
        set_timeslice_navigation(false);
        select_timeslice(inspector.selection_mode_options["lock_timeslice"]);
    } else if (inspector.selection_mode_options["squares"].length == 1) {
        set_timeslice_navigation(false);
        select_timeslice(inspector.selection_mode_options["squares"][0]["t"]);
    } else if (inspector.selection_submission["type"] == "spatial_move" && selected_timeslice < t_dim - 1) {
        select_timeslice(selected_timeslice + 1);
    }
    document.getElementById("selection_mode_highlights").style.visibility = "visible";

    // Replace trackers with selectors
    document.getElementById("tracking_inspector").style.display = "none";
    document.getElementById("square_inspector").style.display = "none";
    document.getElementById("choice_selector").style.display = "block";
    document.getElementById("swap_effect_selector").style.display = "block";

    if (inspector.selection_mode_options["choice_keyword"] == null) {
        inspector.select_choice_option(null);
    } else {
        // Create choice buttons in choice selector
        inspector.prepare_choice_selection();
    }

    if (inspector.selection_mode_options["squares"].length == 1) {
        // The square is chosen automatically
        inspector.select_square(inspector.selection_mode_options["squares"][0]["x"], inspector.selection_mode_options["squares"][0]["y"]);
    }

    // Remove command buttons, create abort button
    let stone_inspector_commands_svg = document.getElementById("stone_inspector_commands_svg");
    while (stone_inspector_commands_svg.firstChild) {
        stone_inspector_commands_svg.removeChild(stone_inspector_commands_svg.lastChild);
    }
    document.getElementById("stone_inspector_commands_svg").style.display = "none";
    document.getElementById("abort_selection_button").style.display = "block";


    show_canon_board_slice(selected_round, selected_timeslice);

}

inspector.turn_off_selection_mode = function() {

    // Enable round navigation
    animation_manager.clear_queue();
    set_round_navigation(true);
    set_timeslice_navigation(true);

    // Hide highlights and dummies and azimuth indicators
    document.getElementById("selection_mode_highlights").style.visibility = "hidden";
    selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
    for (i = 0; i < selection_mode_dummies.length; i++) {
        selection_mode_dummies[i].style.display = "none";
    }
    for (ind_a = 0; ind_a < 4; ind_a++) {
        document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "none";
    }

    // Hide selection mode buttons
    document.getElementById("abort_selection_button").style.display = "none";
    document.getElementById("submit_selection_button").style.display = "none";
    document.getElementById("stone_inspector_commands_svg").style.display = "block";

    // Remove choice selector buttons
    let choice_selector_svg = document.getElementById("choice_selector_buttons_svg");
    while (choice_selector_svg.firstChild) {
        choice_selector_svg.removeChild(choice_selector_svg.lastChild);
    }

    // Remove swap effect selection options
    inspector.unselect_swap_effect();

    // Replace selectors with trackers
    document.getElementById("choice_selector").style.display = "none";
    document.getElementById("swap_effect_selector").style.display = "none";
    document.getElementById("tracking_inspector").style.display = "block";
    document.getElementById("square_inspector").style.display = "block";


    inspector.selection_mode_enabled = false;


    select_round(active_round);
    select_timeslice(active_timeslice);

    show_canon_board_slice(selected_round, selected_timeslice);

    inspector.board_square_click(stone_trajectories[active_round][active_timeslice]["canon"][inspector.selection_mode_stone_ID][0], stone_trajectories[active_round][active_timeslice]["canon"][inspector.selection_mode_stone_ID][1]);

    // Clear cache
    inspector.selection_mode_options = null;
    inspector.selection_submission = null;
    inspector.selection_mode_stone_ID = null;

}

inspector.prepare_choice_selection = function() {
    let choice_selector_svg = document.getElementById("choice_selector_buttons_svg");
    offset_x = 10;
    offset_y = 8;
    for (let i = 0; i < inspector.selection_mode_options["choice_options"].length; i++) {
        let new_button = make_SVG_element("rect", {
            class : "choice_option_button",
            id : `choice_option_${inspector.selection_mode_options["choice_options"][i]}`,
            onclick : `inspector.select_choice_option(\"${inspector.selection_mode_options["choice_options"][i]}\")`,
            x : offset_x,
            y : offset_y,
            width : choice_option_btn_width,
            height : choice_option_btn_height
        });
        let new_button_label = make_SVG_element("text", {
            class : "button_label",
            id : `choice_option_${inspector.selection_mode_options["choice_options"][i]}_label`,
            x : offset_x + choice_option_btn_width / 2,
            y : offset_y + choice_option_btn_height / 2,
            "text-anchor" : "middle"
        });
        new_button_label.textContent = inspector.selection_mode_options["choice_labels"][i];
        choice_selector_svg.appendChild(new_button);
        choice_selector_svg.appendChild(new_button_label);
        offset_x += choice_option_btn_width + 10;

    }
}

inspector.toggle_submit_button = function() {
    if (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false && inspector.selection_mode_information_level["swap_effect"] == false && inspector.selection_mode_information_level["choice_option"] == false) {
        document.getElementById("submit_selection_button").style.display = "inline";
    } else {
        document.getElementById("submit_selection_button").style.display = "none";
    }
}

inspector.add_swap_effect_option = function(effect_ID) {
    let swap_effect_table = document.getElementById("swap_effect_selector_table");
    let option_id;
    let option_onclick;
    let option_button;
    let option_desc;
    if (effect_ID == null) {
        option_id = "swap_effect_option_null";
        option_onclick = "inspector.select_swap_effect(null)";
        option_button = "No swap";
        option_desc = "";
    } else {
        option_id = `swap_effect_option_${effect_ID}`;
        option_onclick = `inspector.select_swap_effect(${effect_ID})`;
        option_button = "Swap";
        option_desc = "unknown effect";
        // Check if active or inactive

        // Active effects
        for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["active"].length; effect_i++) {
            if (inspector.reverse_causality_flags[selected_round]["effects"]["active"][effect_i] == effect_ID) {
                // Is active
                option_desc = inspector.flag_description("effect", "active", effect_ID)
            }
        }
        // Inactive effects
        for (let effect_i = 0; effect_i < inspector.reverse_causality_flags[selected_round]["effects"]["inactive"].length; effect_i++) {
            if (inspector.reverse_causality_flags[selected_round]["effects"]["active"][effect_i] == effect_ID) {
                // Is inactive
                option_desc = inspector.flag_description("effect", "inactive", effect_ID)
            }
        }
    }
    let option_row = swap_effect_table.insertRow(-1);
    option_row.setAttribute("id", option_id);
    option_row.setAttribute("class", "swap_effect_option");
    let option_button_element = option_row.insertCell(0);
    option_button_element.setAttribute("id", `${option_id}_button`);
    option_button_element.setAttribute("class", "swap_effect_option_button");
    option_button_element.setAttribute("onclick", option_onclick);
    option_button_element.innerHTML = option_button;
    let option_desc_element = option_row.insertCell(1);
    option_desc_element.setAttribute("id", `${option_id}_description`);
    option_desc_element.setAttribute("class", "swap_effect_option_description");
    option_desc_element.innerHTML = option_desc;
}

inspector.select_square = function(x, y) {
    // We find the correct element of squares
    for (let i = 0; i < inspector.selection_mode_options["squares"].length; i++) {
        if (inspector.selection_mode_options["squares"][i]["t"] == selected_timeslice && inspector.selection_mode_options["squares"][i]["x"] == x && inspector.selection_mode_options["squares"][i]["y"] == y) {
            animation_manager.clear_queue();
            show_canon_board_slice(selected_round, selected_timeslice);
            let cur_square = inspector.selection_mode_options["squares"][i];
            inspector.selection["square"] = i;
            inspector.selection_mode_information_level["square"] = false;
            inspector.set_square_highlight([x, y]);
            if (cur_square["a"] != null) {
                if (cur_square["a"].length == 1) {
                    inspector.select_azimuth(cur_square["a"][0]);
                } else {
                    inspector.selection["azimuth"] = "NOT_SELECTED";
                    inspector.selection_mode_information_level["azimuth"] = true;
                }
            } else {
                inspector.select_azimuth(null);
            }

            inspector.unselect_swap_effect();
            if (cur_square["swap_effects"] != null) {
                for (ind_swap = 0; ind_swap < cur_square["swap_effects"].length; ind_swap++) {
                    inspector.add_swap_effect_option(cur_square["swap_effects"][ind_swap]);
                }

                if (cur_square["swap_effects"].length == 1) {
                    inspector.select_swap_effect(cur_square["swap_effects"][0]);
                } else {
                    inspector.selection["swap_effect"] = "NOT_SELECTED";
                    inspector.selection_mode_information_level["swap_effect"] = true;
                }
            } else {
                inspector.selection["swap_effect"] = null;
                inspector.selection_mode_information_level["swap_effect"] = false;
            }

            inspector.toggle_submit_button();
            show_canon_board_slice(selected_round, selected_timeslice);

            // Now, based on what we know and what is yet to be inputted, we show and hide the azimuth and swap_effect dialogues
            if (inspector.selection_mode_information_level["azimuth"]) {
                for (ind_a = 0; ind_a < 4; ind_a++) {
                    if (cur_square["a"].includes(ind_a)) {
                        document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "inline";
                    } else {
                        document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "none";
                    }
                }
            } else {
                for (ind_a = 0; ind_a < 4; ind_a++) {
                    document.getElementById(`azimuth_indicator_${ind_a}`).style.display = "none";
                }
            }
        }
    }
}

inspector.unselect_square = function() {
    inspector.selection["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["square"] = true;
    inspector.set_square_highlight(null);
    inspector.unselect_swap_effect();
    let selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
    for (i = 0; i < selection_mode_dummies.length; i++) {
        selection_mode_dummies[i].style.display = "none";
    }
    inspector.selection["azimuth"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.selection["swap_effect"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["swap_effect"] = true;
    inspector.toggle_submit_button();
}

inspector.unselect_swap_effect = function() {
    // Clears cache, resets swap_effect selector
    inspector.selection["swap_effect"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["swap_effect"] = true;
    let swap_effect_table = document.getElementById("swap_effect_selector_table");
    while (swap_effect_table.firstChild) {
        swap_effect_table.removeChild(swap_effect_table.lastChild);
    }
}

inspector.select_azimuth = function(target_azimuth) {
    if (inspector.selection_mode_options["squares"][inspector.selection["square"]]["a"] == null) {
        target_azimuth = null;
    }
    if (target_azimuth == null || inspector.selection_mode_options["squares"][inspector.selection["square"]]["a"].includes(target_azimuth)) {
        inspector.selection["azimuth"] = target_azimuth;
        inspector.selection_mode_information_level["azimuth"] = false;
        inspector.toggle_submit_button();
        console.log(`azimuth is known to be ${inspector.selection["azimuth"]}.`);
        show_canon_board_slice(selected_round, selected_timeslice);
    }
}

inspector.select_swap_effect = function(target_swap_effect) {
    if (target_swap_effect == null || inspector.selection_mode_options["squares"][inspector.selection["square"]]["swap_effects"].includes(target_swap_effect)) {
        inspector.selection["swap_effect"] = target_swap_effect;
        inspector.selection_mode_information_level["swap_effect"] = false;

        // Reset color of all elements, then color the selected element
        let swap_effect_option_buttons = document.getElementsByClassName("swap_effect_option_button");
        for (i = 0; i < swap_effect_option_buttons.length; i++) {
            swap_effect_option_buttons[i].style["background-color"] = "transparent";
        }
        document.getElementById(`swap_effect_option_${target_swap_effect}_button`).style["background-color"] = "lightgreen";

        inspector.toggle_submit_button();
        console.log(`swap effect is known to be ${inspector.selection["swap_effect"]}.`);
    }
}

inspector.select_choice_option = function(selected_choice_option) {
    inspector.selection["choice_option"] = selected_choice_option;
    inspector.selection_mode_information_level["choice_option"] = false;
    // Reset highlight of option button
    if (inspector.selection_mode_options["choice_keyword"] != null) {
        for (let i = 0; i < inspector.selection_mode_options["choice_options"].length; i++) {
            document.getElementById(`choice_option_${inspector.selection_mode_options["choice_options"][i]}`).style.fill = "pink";
            document.getElementById(`choice_option_${inspector.selection_mode_options["choice_options"][i]}`).style["fill-opacity"] = "0.2";
        }
        if (selected_choice_option != null) {
            document.getElementById(`choice_option_${selected_choice_option}`).style.fill = "green";
            document.getElementById(`choice_option_${selected_choice_option}`).style["fill-opacity"] = "0.5";
            inspector.toggle_submit_button();
        }
    }
}

inspector.submit_selection = function() {
    // onclick of the submit selection button
    // stores the command object in a hidden HTML dataform
    inspector.selection_submission["target_t"] = inspector.selection_mode_options["squares"][inspector.selection["square"]]["t"];
    inspector.selection_submission["target_x"] = inspector.selection_mode_options["squares"][inspector.selection["square"]]["x"];
    inspector.selection_submission["target_y"] = inspector.selection_mode_options["squares"][inspector.selection["square"]]["y"];
    inspector.selection_submission["target_a"] = inspector.selection["azimuth"];
    inspector.selection_submission["swap_effect"] = inspector.selection["swap_effect"];
    inspector.selection_submission["choice_option"] = inspector.selection["choice_option"];

    for (i = 0; i < inspector.selection_keywords.length; i++) {
        document.getElementById(`cmd_${inspector.selection_keywords[i]}_${inspector.selection_mode_stone_ID}`).value = inspector.selection_submission[inspector.selection_keywords[i]];
    }
    if (inspector.selection_mode_options["choice_keyword"] != null) {
        document.getElementById(`cmd_choice_keyword_${inspector.selection_mode_stone_ID}`).name = inspector.selection_mode_options["choice_keyword"];
        document.getElementById(`cmd_choice_keyword_${inspector.selection_mode_stone_ID}`).value = inspector.selection_submission["choice_option"];
    }

    if (inspector.selection_mode_options["squares"][inspector.selection["square"]]["override_cmd_type"] != undefined) {
        if (inspector.selection_mode_options["squares"][inspector.selection["square"]]["override_cmd_type"] != null) {
            document.getElementById(`cmd_type_${inspector.selection_mode_stone_ID}`).value = inspector.selection_mode_options["squares"][inspector.selection["square"]]["override_cmd_type"];
        }
    }

    commander.mark_as_checked(inspector.selection_mode_stone_ID);

    inspector.turn_off_selection_mode();

}


inspector.undo_command = function() {
    let stone_ID = find_stone_at_pos(inspector.highlighted_square[0], inspector.highlighted_square[1]);

    // Delete the values from the form
    for (i = 0; i < inspector.selection_keywords.length; i++) {
        document.getElementById(`cmd_${inspector.selection_keywords[i]}_${stone_ID}`).value = null;
    }
    document.getElementById(`cmd_choice_keyword_${stone_ID}`).name = `cmd_choice_keyword_${stone_ID}`;
    document.getElementById(`cmd_choice_keyword_${stone_ID}`).value = null;

    commander.add_to_checklist(stone_ID);
    inspector.display_stone_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
}

// Stone commands

inspector.prepare_command = function(stone_ID, command_key) {
    // Prompts user further to specify the arguments for the command
    console.log(`stone ${stone_ID} performs ${command_key}`);
    let cur_cmd_props = available_commands[stone_ID]["command_properties"][command_key];

    inspector.selection_submission = new Object();

    inspector.selection_submission["stone_ID"] = stone_ID;
    inspector.selection_submission["type"] = cur_cmd_props["command_type"];
    inspector.selection_submission["t"] = active_timeslice;
    inspector.selection_submission["x"] = stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID][0];
    inspector.selection_submission["y"] = stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID][1];
    inspector.selection_submission["a"] = stone_trajectories[selected_round][selected_timeslice]["canon"][stone_ID][2];

    inspector.turn_on_selection_mode(stone_ID, cur_cmd_props["selection_mode"]);

}

inspector.display_stone_commands = function(stone_ID) {
    document.getElementById("undo_command_button_svg").style.display = "none";
    document.getElementById("stone_inspector_commands_svg").style.display = "block";
    // if stone_ID = null, hides stone commands
    let stone_inspector_commands_svg = document.getElementById("stone_inspector_commands_svg");
    if (stone_ID == null) {
        while (stone_inspector_commands_svg.firstChild) {
            stone_inspector_commands_svg.removeChild(stone_inspector_commands_svg.lastChild);
        }
    } else {
        // First, we delete everything
        inspector.display_stone_commands(null);

        // Now, we find the list of commands
        let list_of_commands = available_commands[stone_ID]["commands"];

        // We draw every button
        offset_x = 0;
        offset_y = 0;
        for (let i = 0; i < list_of_commands.length; i++) {
            let new_button = make_SVG_element("rect", {
                class : "stone_command_panel_button",
                id : `stone_command_${list_of_commands[i]}`,
                onclick : `inspector.prepare_command(${stone_ID}, \"${list_of_commands[i]}\")`,
                x : offset_x,
                y : 0,
                width : stone_command_btn_width,
                height : stone_command_btn_height
            });
            let new_button_label = make_SVG_element("text", {
                class : "button_label",
                id : `stone_command_${list_of_commands[i]}_label`,
                x : offset_x + stone_command_btn_width / 2,
                y : stone_command_btn_height / 2,
                "text-anchor" : "middle"
            });
            new_button_label.textContent = available_commands[stone_ID]["command_properties"][list_of_commands[i]]["label"];
            stone_inspector_commands_svg.appendChild(new_button);
            stone_inspector_commands_svg.appendChild(new_button_label);
            offset_x += 110;

        }
    }
}

inspector.display_undo_button = function() {
    document.getElementById("stone_inspector_commands_svg").style.display = "none";
    document.getElementById("undo_command_button_svg").style.display = "block";
}



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
    /*if (cameraman.tracking_stone != null) {
        if (stone_endpoints[selected_round][cameraman.tracking_stone] == undefined) {
            console.log("Stone not placed on board");
        } else {
            console.log(`Startpoint: ${stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["event"]} at (${stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["x"]}, ${stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["y"]})`);
        }
    }*/
    go_to_square(stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["t"], stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["x"], stone_endpoints[selected_round][cameraman.tracking_stone]["start"]["y"], false)
}

function tracking_endpoint() {
    /*if (cameraman.tracking_stone != null) {
        if (stone_endpoints[selected_round][cameraman.tracking_stone] == undefined) {
            console.log("Stone not placed on board");
        } else {
            console.log(`Endpoint: ${stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["event"]} at (${stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["x"]}, ${stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["y"]})`);
        }
    }*/
    go_to_square(stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["t"], stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["x"], stone_endpoints[selected_round][cameraman.tracking_stone]["end"]["y"], false)
}

