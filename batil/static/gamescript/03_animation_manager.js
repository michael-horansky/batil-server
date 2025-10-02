
function show_canon_board_slice(round_n, timeslice){
    visible_round = round_n;
    visible_timeslice = timeslice;
    visible_process = "canon";
    show_stones_at_process(round_n, timeslice, "canon");
    show_time_jumps_at_time(round_n, timeslice);
    show_bases_at_time(round_n, timeslice);
    if (inspector.selection_mode_enabled) {
        // We take care of the selection choice highlighting
        for (x = 0; x < x_dim; x++) {
            for (y = 0; y < y_dim; y++) {
                document.getElementById(`selection_mode_highlight_${x}_${y}`).style.fill = "grey";
            }
        }
        for (i = 0; i < inspector.selection_mode_options["squares"].length; i++) {
            if (inspector.selection_mode_options["squares"][i]["t"] == visible_timeslice) {
                document.getElementById(`selection_mode_highlight_${inspector.selection_mode_options["squares"][i]["x"]}_${inspector.selection_mode_options["squares"][i]["y"]}`).style.fill = "green";
            }
        }
        // If a choice has been made, we place the selection mode dummy at its appropriate place
        selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
        for (i = 0; i < selection_mode_dummies.length; i++) {
            selection_mode_dummies[i].style.display = "none";
        }
        if (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false) {
            let selected_square = inspector.selection_mode_options["squares"][inspector.selection["square"]];
            let dummy_label = `${stone_properties[inspector.selection_mode_stone_ID]["allegiance"]}_${stone_properties[inspector.selection_mode_stone_ID]["stone_type"]}_dummy`;
            document.getElementById(dummy_label).style.transform = `translate(${100 * selected_square["x"]}px,${100 * selected_square["y"]}px)`;
            if (stone_properties[inspector.selection_mode_stone_ID]["orientable"]) {
                document.getElementById(`${dummy_label}_rotation`).style.transform = `rotate(${90 * inspector.selection["azimuth"]}deg)`;
            }
            document.getElementById(dummy_label).style.display = "inline";
        }
    }
}

function hide_all_stones(){
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            document.getElementById(`stone_${stone_ID}`).style.display = "none";
        });
    });
}

function show_time_jumps_at_time(round_n, time) {
    for (let x = 0; x < x_dim; x++) {
        for (let y = 0; y < y_dim; y++) {
            let current_used_time_jump_marker = document.getElementById(`used_time_jump_marker_${x}_${y}`);
            let current_unused_time_jump_marker = document.getElementById(`unused_time_jump_marker_${x}_${y}`);
            if (current_used_time_jump_marker != undefined) {
                let used_tj_marker = inds(time_jumps[round_n], [time, x, y, "used"]);
                let unused_tj_marker = inds(time_jumps[round_n], [time, x, y, "unused"]);
                if (used_tj_marker != undefined) {
                    current_used_time_jump_marker.style.fill = `url(#grad_used_${used_tj_marker})`;
                    current_used_time_jump_marker.style.opacity = "1";
                    current_used_time_jump_marker.style.visibility = "visible";
                } else {
                    current_used_time_jump_marker.style.visibility = "hidden";
                }
                if (unused_tj_marker != undefined) {
                    current_unused_time_jump_marker.style.fill = `url(#grad_unused_${unused_tj_marker})`;
                    current_unused_time_jump_marker.style.opacity = "1";
                    current_unused_time_jump_marker.style.visibility = "visible";
                } else {
                    current_unused_time_jump_marker.style.visibility = "hidden";
                }
            }
        }
    }
}

function show_bases_at_time(round_n, time) {
    for (let base_i = 0; base_i < bases.length; base_i++) {
        let base_ID = bases[base_i];
        let x = base_trajectories[round_n][time][base_ID][0];
        let y = base_trajectories[round_n][time][base_ID][1];
        let allegiance = base_trajectories[round_n][time][base_ID][2];
        document.getElementById(`base_${base_ID}`).style.transform = `translate(${100 * x}px,${100 * y}px)`;
        switch(allegiance) {
            case "neutral":
                document.getElementById(`base_${base_ID}_indicator`).style.fill = 'yellow';
                break;
            case "A":
                document.getElementById(`base_${base_ID}_indicator`).style.fill = 'green';
                break;
            case "B":
                document.getElementById(`base_${base_ID}_indicator`).style.fill = 'red';
                break;
        }
    }
}

function show_stones_at_process(round_n, time, process_key){
    // NOT animated
    // This resets the animation properties (opacity, scale)
    visible_timeslice = time;
    visible_process = process_key;
    all_factions.forEach(function(faction, faction_index) {
        faction_armies[faction].forEach(function(stone_ID, stone_index){
            let stone_state = stone_trajectories[round_n][time][process_key][`${stone_ID}`];
            //alert(`stone ${stone_ID} is in state ${stone_state}`);
            if (stone_state == null) {
                document.getElementById(`stone_${stone_ID}`).style.display = "none";
            } else {
                document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * stone_state[0]}px,${100 * stone_state[1]}px)`;
                if (stone_properties[stone_ID]["orientable"]) {
                    document.getElementById(`stone_${stone_ID}_rotation`).style.transform = `rotate(${90 * stone_state[2]}deg)`;
                }
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.transform = "";
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.opacity = "1";
                document.getElementById(`stone_${stone_ID}`).style.display = "inline";
            }
        });
    });
}

function hide_stones(local_stone_list) {
    local_stone_list.forEach(function(stone_ID, stone_index){
        document.getElementById(`stone_${stone_ID}`).style.display = "none";
    });
}

function show_stones_at_state(local_stone_list, state_matrix, scale = null, opacity = null){
    // state_matrix[index in local_stone_list] = null or [x, y, azimuth]
    // scale and opacity are global properties and default to 1
    local_stone_list.forEach(function(stone_ID, stone_index){
        let stone_state = state_matrix[stone_index];
        if (stone_state == null) {
            document.getElementById(`stone_${stone_ID}`).style.display = "none";
        } else {
            document.getElementById(`stone_${stone_ID}`).style.transform = `translate(${100 * stone_state[0]}px,${100 * stone_state[1]}px)`;
            if (stone_properties[stone_ID]["orientable"]) {
                document.getElementById(`stone_${stone_ID}_rotation`).style.transform = `rotate(${90 * stone_state[2]}deg)`;
            }
            if (scale != null) {
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.transform = `scale(${scale})`;
            }
            if (opacity != null) {
                document.getElementById(`stone_${stone_ID}_animation_effects`).style.opacity = `${opacity}`;
            }
            document.getElementById(`stone_${stone_ID}`).style.display = "inline";
        }
    });
}

function show_class_at_state(class_name, scale = null, opacity = null) {
    let class_elements = document.getElementsByClassName(class_name);
    for (let class_index = 0; class_index < class_elements.length; class_index++) {
        if (scale != null) {
            class_elements[class_index].style.transform = `scale(${scale})`;
        }
        if (opacity != null) {
            class_elements[class_index].style.opacity = `${opacity}`;
        }
        class_elements[class_index].style.display = `inline`;
    }
}

function show_ids_at_state(list_of_ids, scale = null, opacity = null) {
    for (let id_index = 0; id_index < list_of_ids.length; id_index++) {
        cur_element = document.getElementById(list_of_ids[id_index]);
        if (cur_element != undefined) {
            if (scale != null) {
                cur_element.style.transform = `scale(${scale})`;
            }
            if (opacity != null) {
                cur_element.style.opacity = `${opacity}`;
            }
            cur_element.style.display = `inline`;
        }
    }
}

// ----------------------------------------------------------------------------
// ---------------------------- Animation manager -----------------------------
// ----------------------------------------------------------------------------

const animation_manager = new Object();
animation_manager.animation_queue = [];
animation_manager.animation_daemon = null;
animation_manager.temporary_element_classes = [];
animation_manager.temporary_animation_elements = []; // [{"id" : id, "class" : class, kwargs}]
animation_manager.is_playing = false;
animation_manager.current_frame_key = 0;
animation_manager.default_total_frames = 40;
animation_manager.default_frame_latency = 5;
animation_manager.dictionary_of_animations = new Object();
animation_manager.magic_words = ["reset_to_canon"];
animation_manager.reset_animation = function() {
    animation_manager.animation_daemon = null;
    animation_manager.is_playing = false;
    animation_manager.current_frame_key = 0;
    while (animation_manager.temporary_element_classes.length > 0) {
        remove_elements_by_class(animation_manager.temporary_element_classes.shift());
    }
    animation_manager.temporary_animation_elements = [];
}

// ---------------------------- Jukebox management ----------------------------

animation_manager.shift_frame_method = function(current_animation) {
    if (animation_manager.current_frame_key == animation_manager.total_frames) {
        clearInterval(animation_manager.animation_daemon);
        // animation cleanup
        animation_manager.dictionary_of_animations[current_animation[0]]["cleanup"](current_animation.slice(1));
        animation_manager.reset_animation();
        animation_manager.play_if_available();
    } else {
        animation_manager.current_frame_key += 1;
        animation_manager.dictionary_of_animations[current_animation[0]]["frame"](current_animation.slice(1));
    }
}
animation_manager.play_if_available = function() {
    if (animation_manager.is_playing == false) {
        if (animation_manager.animation_queue.length > 0) {
            let current_animation = animation_manager.animation_queue.shift();
            if (animation_manager.magic_words.includes(current_animation[0])) {
                // Magic word
                switch(current_animation[0]) {
                    case "reset_to_canon":
                        visible_process = "canon";
                        show_canon_board_slice(current_animation[1], current_animation[2]);
                        cameraman.apply_tracking();
                }
                animation_manager.play_if_available();
            } else {
                animation_manager.is_playing = true;
                // prepare contextual animation specifications
                animation_manager.total_frames = animation_manager.dictionary_of_animations[current_animation[0]]["total_frames"];
                animation_manager.frame_latency = animation_manager.dictionary_of_animations[current_animation[0]]["frame_latency"];
                animation_manager.dictionary_of_animations[current_animation[0]]["preparation"](current_animation.slice(1));
                animation_manager.animation_daemon = setInterval(animation_manager.shift_frame_method, animation_manager.frame_latency, current_animation);
            }
        }
    }
}

animation_manager.add_to_queue = function(list_of_animations) {
    // Each animation is a list, where the first element is a key in dictionary_of_animations
    list_of_animations.forEach(function(animation_args, index) {
        if (typeof(animation_args) == 'string') {
            // It's a magic word!
            animation_manager.animation_queue.push(animation_args);
        } else {
            switch(animation_args[0]) {
                case "change_process":
                    if (!(inbetweens[animation_args[1]][animation_args[2]][animation_args[3]]["redundant"])) {
                        animation_manager.animation_queue.push(animation_args);
                    }
                    break;
                default:
                    animation_manager.animation_queue.push(animation_args);
            }
        }
    });
    //animation_manager.animation_queue = animation_manager.animation_queue.concat(list_of_animations);
    animation_manager.play_if_available();
}

animation_manager.clear_queue = function() {
    // clears queue and interrupts current animation
    if (animation_manager.is_playing) {
        clearInterval(animation_manager.animation_daemon);
    }
    animation_manager.reset_animation();
    animation_manager.animation_queue = [];
}

animation_manager.default_preparation = function(animation_args) {

}
animation_manager.default_cleanup = function(animation_args) {

}

animation_manager.add_animation = function(animation_name, animation_object) {
    if (animation_object["frame"] == undefined) {
        alert("Submitted animation object has to posses the 'frame' property!");
        return null;
    }
    animation_manager.dictionary_of_animations[animation_name] = animation_object;
    if (animation_manager.dictionary_of_animations[animation_name]["preparation"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["preparation"] = animation_manager.default_preparation;
    }
    if (animation_manager.dictionary_of_animations[animation_name]["cleanup"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["cleanup"] = animation_manager.default_cleanup;
    }
    if (animation_manager.dictionary_of_animations[animation_name]["total_frames"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["total_frames"] = animation_manager.default_total_frames;
    }
    if (animation_manager.dictionary_of_animations[animation_name]["frame_latency"] == undefined) {
        animation_manager.dictionary_of_animations[animation_name]["frame_latency"] = animation_manager.default_frame_latency;
    }
}

// ----------------------- Temporary animation elements -----------------------

animation_manager.add_TAE_class = function(TAE_class_name) {
    if (!(animation_manager.temporary_element_classes.includes(TAE_class_name))) {
        animation_manager.temporary_element_classes.push(TAE_class_name);
    }
}
animation_manager.create_causal_freedom_marker = function(pos_x, pos_y) {
    let new_group = make_SVG_element("g", {
        class : "TAE_causal_freedom_marker",
        id : `causal_freedom_marker_${pos_x}_${pos_y}`,
        x : 0,
        y : 0,
        width : 100,
        height : 100,
        display : "none"
    });
    document.getElementById("board_layer_4").appendChild(new_group);
    question_mark = make_SVG_element("text", {
        x : 30,
        y : 80,
        "font-size" : "5em"
    });
    question_mark.textContent = "?";
    new_group.appendChild(question_mark);
    new_group.style.transform = `translate(${100 * pos_x}px,${100 * pos_y}px)`;
    // No need to add a separate TAE, since these are updated by-class
}
animation_manager.create_stone_action_marker = function(stone_action) {
    switch(true) {
        case arrays_equal(stone_action.slice(0,2), ["tank", "attack"]):
            new_group = make_SVG_element("g", {
                class : "TAE_tank_attack",
                id : `TAE_tank_attack_${stone_action[2]}_${stone_action[3]}`,
                x : 0,
                y : 0
            });
            document.getElementById("board_layer_2").appendChild(new_group);
            laser_line = make_SVG_element("line", {
                x1 : 50,
                y1 : 50,
                x2 : 50 + 100*(stone_action[4]-stone_action[2]),
                y2 : 50 + 100*(stone_action[5]-stone_action[3]),
                "stroke" : "red",
                "stroke-width" : 7
            });
            new_group.appendChild(laser_line);
            new_group.style.transform = `translate(${100 * stone_action[2]}px,${100 * stone_action[3]}px)`;

            animation_manager.temporary_animation_elements.push({
                "id" : `TAE_tank_attack_${stone_action[2]}_${stone_action[3]}`,
                "class" : "TAE_tank_attack",
                "x" : stone_action[2],
                "y" : stone_action[3],
                "target_x" : stone_action[4],
                "target_y" : stone_action[5]
            });

            break;
        case arrays_equal(stone_action.slice(0,2), ["sniper", "attack"]):
            new_group = make_SVG_element("g", {
                class : "TAE_sniper_attack",
                id : `TAE_sniper_attack_${stone_action[2]}_${stone_action[3]}`,
                x : 0,
                y : 0
            });
            document.getElementById("board_layer_2").appendChild(new_group);
            laser_line = make_SVG_element("line", {
                x1 : 50 - 2*(stone_action[4]-stone_action[2]),
                y1 : 50 - 2*(stone_action[5]-stone_action[3]),
                x2 : 50 + 2*(stone_action[4]-stone_action[2]),
                y2 : 50 + 2*(stone_action[5]-stone_action[3]),
                "stroke" : "red",
                "stroke-width" : 5
            });
            new_group.appendChild(laser_line);
            new_group.style.transform = `translate(${100 * stone_action[2]}px,${100 * stone_action[3]}px)`;

            animation_manager.temporary_animation_elements.push({
                "id" : `TAE_sniper_attack_${stone_action[2]}_${stone_action[3]}`,
                "class" : "TAE_sniper_attack",
                "x" : stone_action[2],
                "y" : stone_action[3],
                "target_x" : stone_action[4],
                "target_y" : stone_action[5]
            });

            break;
    }
}
animation_manager.create_board_action_marker = function(board_action) {
    // board_action = [action type, x, y]
    switch(board_action[0]) {
        case "explosion":
            // a bomb explosion! The marker is a big red cross
            new_group = make_SVG_element("g", {
                class : "TAE_explosion",
                id : `TAE_explosion_${board_action[1]}_${board_action[2]}`,
                x : 0,
                y : 0
            });
            new_group.setAttribute("opacity", "0");
            new_scaling_group = make_SVG_element("g", {
                class : "TAE_explosion_scaling",
                id : `TAE_explosion_scaling_${board_action[1]}_${board_action[2]}`,
                x : 0,
                y : 0
            });
            new_scaling_group.setAttribute("transform-origin", `50px 50px`);
            document.getElementById("board_layer_2").appendChild(new_group);
            explosion_cross = make_SVG_element("path", {
                d : "M45,45 L45,-55 L55,-55 L55,45 L155,45 L155,55 L55,55 L55,155 L45,155 L45,55 L-55,55 L-55,45 Z",
                "fill" : "red"
            });
            new_group.appendChild(new_scaling_group);
            new_scaling_group.appendChild(explosion_cross);
            new_group.style.transform = `translate(${100 * board_action[1]}px,${100 * board_action[2]}px)`;
            break;
    }
}

animation_manager.update_temporary_animation_elements = function(frame_key) {
    // frame_key is an integer index of the current frame

    // Firstly we deal with the by-class elements for which no fancy calculation is needed, such as the causal freedom markers
    show_class_at_state("TAE_causal_freedom_marker", null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key, "boomerang"));
    show_class_at_state("TAE_explosion", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, frame_key));
    show_class_at_state("TAE_explosion_scaling", animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key));

    for (TAE_i = 0; TAE_i < animation_manager.temporary_animation_elements.length; TAE_i++) {
        let cur_TAE = animation_manager.temporary_animation_elements[TAE_i];
        let cur_DOM_element = document.getElementById(cur_TAE["id"]);
        switch(cur_TAE["class"]) {
            case "TAE_sniper_attack":
                let cur_x = animated_scalar_transformation(100 * cur_TAE["x"], 100 * cur_TAE["target_x"], animation_manager.total_frames, frame_key);
                let cur_y = animated_scalar_transformation(100 * cur_TAE["y"], 100 * cur_TAE["target_y"], animation_manager.total_frames, frame_key);
                cur_DOM_element.style.transform = `translate(${cur_x}px,${cur_y}px)`;
                break;
        }
    }
}

// --------------------------- shift_frame methods ----------------------------

// change_process
animation_manager.change_process_preparation = function(animation_args) {
    let round_n = animation_args[0];
    let s_time = animation_args[1];
    let s_process = animation_args[2];
    let play_backwards = animation_args[3];
    // Create causal-freedom-signifiers for all stones destroyed when s_process = canon
    if (s_process == "canon") {
        if (inbetweens[round_n][s_time][s_process]["dest_stones"].length > 0) {
            animation_manager.add_TAE_class("TAE_causal_freedom_marker");
            for (let stone_index = 0; stone_index < inbetweens[round_n][s_time][s_process]["dest_stones"].length; stone_index++) {
                if (stone_endpoints[selected_round][inbetweens[round_n][s_time][s_process]["dest_stones"][stone_index]]["end"]["event"] == "causally_free") {
                    animation_manager.create_causal_freedom_marker(inbetweens[round_n][s_time][s_process]["dest_stones_states"][stone_index][0], inbetweens[round_n][s_time][s_process]["dest_stones_states"][stone_index][1]);
                }
            }
        }
    }

    // Create various markers for stone and board actions when s_process = "tagscreens"
    if (s_process == "tagscreens") {
        for (let stone_action_index = 0; stone_action_index < stone_actions[round_n][s_time].length; stone_action_index++) {
            let cur_stone_action = stone_actions[round_n][s_time][stone_action_index];
            animation_manager.add_TAE_class(`TAE_${cur_stone_action[0]}_${cur_stone_action[1]}`);
            animation_manager.create_stone_action_marker(cur_stone_action);
        }
        for (let board_action_index = 0; board_action_index < board_actions[round_n][s_time].length; board_action_index++) {
            let cur_board_action = board_actions[round_n][s_time][board_action_index];
            animation_manager.add_TAE_class(`TAE_${cur_board_action[0]}`);
            animation_manager.create_board_action_marker(cur_board_action);
        }
    }

    // Prepare time jump markers
    inbetweens[round_n][s_time][s_process]["new_time_jumps"][0].forEach(function(time_jump_mark, index) {
        time_jump_element = document.getElementById(time_jump_mark);
        if (play_backwards) {
            time_jump_element.style.opacity = "1";
        } else {
            time_jump_element.style.opacity = "0";
        }
        time_jump_element.style.fill = `url(#grad_${inbetweens[round_n][s_time][s_process]["new_time_jumps"][1][index]})`;
        time_jump_element.style.visibility = "visible";
    });
    inbetweens[round_n][s_time][s_process]["old_time_jumps"][0].forEach(function(time_jump_mark, index) {
        time_jump_element = document.getElementById(time_jump_mark);
        if (play_backwards) {
            time_jump_element.style.opacity = "0";
        } else {
            time_jump_element.style.opacity = "1";
        }
        time_jump_element.style.fill = `url(#grad_${inbetweens[round_n][s_time][s_process]["old_time_jumps"][1][index]})`;
        time_jump_element.style.visibility = "visible";
    });

}
animation_manager.change_process_get_frame = function(animation_args) {
    let round_n = animation_args[0];
    let s_time = animation_args[1];
    let s_process = animation_args[2];
    let play_backwards = animation_args[3];
    let contextual_frame_key = (play_backwards ? animation_manager.total_frames - animation_manager.current_frame_key : animation_manager.current_frame_key);
    //alert(animated_matrix_transformation(inbetweens[round_n][start_time][start_process]["cont_stones_states"][0], inbetweens[round_n][start_time][start_process]["cont_stones_states"][1], total_frames, cur_frame_key));

    // Update temporary animation elements
    animation_manager.update_temporary_animation_elements(contextual_frame_key);

    show_stones_at_state(inbetweens[round_n][s_time][s_process]["cont_stones"], animated_matrix_transformation(inbetweens[round_n][s_time][s_process]["cont_stones_states"][0], inbetweens[round_n][s_time][s_process]["cont_stones_states"][1], animation_manager.total_frames, contextual_frame_key));
    // Dest stones: if s_process = "canon", the stones will not be placed on "flags", which means they weren't destroyed, but are causally free.
    if (s_process != "canon") {
        show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], animated_scalar_transformation(1, 2, animation_manager.total_frames, contextual_frame_key), animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
    } else {
        show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
        //show_class_at_state("TAE_causal_freedom_marker", null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key, "boomerang"));
    }
    show_stones_at_state(inbetweens[round_n][s_time][s_process]["new_stones"], inbetweens[round_n][s_time][s_process]["new_stones_states"], 1, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key));
    show_ids_at_state(inbetweens[round_n][s_time][s_process]["new_time_jumps"][0], null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key));
    show_ids_at_state(inbetweens[round_n][s_time][s_process]["old_time_jumps"][0], null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
    // If tracking, we find the tracking stone's state
    if (cameraman.tracking_stone != null) {
        if (inbetweens[round_n][s_time][s_process]["new_stones"].includes(cameraman.tracking_stone)) {
            cameraman.apply_tracking(inbetweens[round_n][s_time][s_process]["new_stones_states"][inbetweens[round_n][s_time][s_process]["new_stones"].indexOf(cameraman.tracking_stone)]);
            cameraman.used_by_an_animation = true;
        } else if (inbetweens[round_n][s_time][s_process]["dest_stones"].includes(cameraman.tracking_stone)) {
            cameraman.apply_tracking(inbetweens[round_n][s_time][s_process]["dest_stones_states"][inbetweens[round_n][s_time][s_process]["dest_stones"].indexOf(cameraman.tracking_stone)]);
            cameraman.used_by_an_animation = true;
        } else if (inbetweens[round_n][s_time][s_process]["cont_stones"].includes(cameraman.tracking_stone)) {
            let tracking_stone_index = inbetweens[round_n][s_time][s_process]["cont_stones"].indexOf(cameraman.tracking_stone);
            cameraman.apply_tracking(animated_vector_transformation(inbetweens[round_n][s_time][s_process]["cont_stones_states"][0][tracking_stone_index], inbetweens[round_n][s_time][s_process]["cont_stones_states"][1][tracking_stone_index], animation_manager.total_frames, contextual_frame_key));
            cameraman.used_by_an_animation = true;
        }
    }
}
animation_manager.change_process_cleanup = function(animation_args) {
    let round_n = animation_args[0];
    let s_time = animation_args[1];
    let s_process = animation_args[2];
    let play_backwards = animation_args[3];
    if (play_backwards) {
        show_stones_at_process(round_n, s_time, s_process);
        show_time_jumps_at_time(round_n, s_time);
    } else {
        if (s_process == "canon") {
            show_stones_at_process(round_n, s_time + 1, process_keys[0]);
            show_time_jumps_at_time(round_n, s_time + 1);
        } else {
            show_stones_at_process(round_n, s_time, process_keys[process_keys.indexOf(s_process) + 1]);
            show_time_jumps_at_time(round_n, s_time);
        }
    }
    // Hide time jump markers
    if (play_backwards) {
        inbetweens[round_n][s_time][s_process]["new_time_jumps"][0].forEach(function(new_time_jump_id, index) {
            document.getElementById(new_time_jump_id).style.visibility = "hidden";
        });
    } else {
        inbetweens[round_n][s_time][s_process]["old_time_jumps"][0].forEach(function(new_time_jump_id, index) {
            document.getElementById(new_time_jump_id).style.visibility = "hidden";
        });
    }
    // Update camera
    cameraman.used_by_an_animation = false;
    // Only if the tracking stone changed position or recently appeared, we reset the highlight
    cameraman.apply_tracking();
}

// change_round
animation_manager.change_round_preparation = function(animation_args) {
    let animation_overlay_msg = animation_args[2];
    let transition_direction = animation_args[3];
    // disable timeslice navigation
    set_timeslice_navigation(false);
    // Show the animation overlay
    document.getElementById("board_animation_overlay_text").textContent = animation_overlay_msg;
    document.getElementById("board_animation_overlay_bg").style.fill = "rgb(200, 200, 200)";
    switch (transition_direction) {
        case "down":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${- cameraman.board_dimensions.height}px)`;
            break;
        case "left":
            document.getElementById("board_animation_overlay").style.transform = `translate(${cameraman.board_dimensions.width}px,0px)`;
            break;
        case "up":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${cameraman.board_dimensions.height}px)`;
            break;
        case "right":
            document.getElementById("board_animation_overlay").style.transform = `translate(${-cameraman.board_dimensions.width}px,0px)`;
            break;
    }
    document.getElementById("board_animation_overlay").style.visibility = "visible";
}
animation_manager.change_round_get_frame = function(animation_args) {
    let new_round = animation_args[0];
    let new_timeslice = animation_args[1];
    let transition_direction = animation_args[3];

    // Change the style of animation overlay
    //document.getElementById("board_animation_overlay").style.opacity = animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, animation_manager.current_frame_key, "boomerang");
    switch (transition_direction) {
        case "down":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${animated_scalar_transformation(- cameraman.board_dimensions.height, cameraman.board_dimensions.height, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px)`;
            break;
        case "left":
            document.getElementById("board_animation_overlay").style.transform = `translate(${animated_scalar_transformation(cameraman.board_dimensions.width, -cameraman.board_dimensions.width, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px,0px)`;
            break;
        case "up":
            document.getElementById("board_animation_overlay").style.transform = `translate(0px,${animated_scalar_transformation(cameraman.board_dimensions.height, -cameraman.board_dimensions.height, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px)`;
            break;
        case "right":
            document.getElementById("board_animation_overlay").style.transform = `translate(${animated_scalar_transformation(- cameraman.board_dimensions.width, cameraman.board_dimensions.width, animation_manager.total_frames, animation_manager.current_frame_key, method="linear")}px,0px)`;
            break;
    }

    // If we're halfway done, show the new round
    if (animation_manager.current_frame_key / animation_manager.total_frames > 0.5 && (visible_round != new_round || visible_timeslice != new_timeslice)) {
        if (new_timeslice == 0) {
            // if we move into the zeroth time-slice, we show the board as is on setup, so that the other elements appearing (TJIs, explosions...) can be animated
            show_canon_board_slice(0, new_timeslice);
        } else {
            show_canon_board_slice(new_round, new_timeslice);
        }
    }

}
animation_manager.change_round_cleanup = function(animation_args) {
    // Hide the animation overlay
    document.getElementById("board_animation_overlay").style.visibility = "hidden";
    document.getElementById("board_animation_overlay").style.transform = "";

    set_timeslice_navigation(true);

}

// -------------------- Dictionary of shift_frame methods ---------------------
// shift_frame_dictionary["animation_type"] = [preparation_method, get_frame_method, cleanup_method]
// animation_specs_dictionary["animation_type"] = [total_frames, frame_latency (in ms)]

animation_manager.add_animation("change_process", {
    "preparation" : animation_manager.change_process_preparation,
    "frame" : animation_manager.change_process_get_frame,
    "cleanup" : animation_manager.change_process_cleanup,
    "total_frames" : 40,
    "frame_latency" : 5
});
animation_manager.add_animation("change_round", {
    "preparation" : animation_manager.change_round_preparation,
    "frame" : animation_manager.change_round_get_frame,
    "cleanup" : animation_manager.change_round_cleanup,
    "total_frames" : 100,
    "frame_latency" : 2
});


