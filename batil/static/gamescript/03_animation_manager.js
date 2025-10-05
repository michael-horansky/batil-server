// ----------------------------- Animation logic ------------------------------
const board_action_marker_TAE_classes = ["explosion", "capture", "tagscreen_lock", "tagscreen_unlock", "tagscreen_hide"];
// board_action_marker_dictionary[TAE_class] = [template_name, base_class, board_layer]
const board_action_marker_dictionary = {
    "explosion" : ["TAE_explosion", 4],
    "capture" : ["TAE_capture", 4],
    "tagscreen_lock" : ["TAE_tagscreen", 4],
    "tagscreen_unlock" : ["TAE_tagscreen", 4],
    "tagscreen_hide" : ["TAE_tagscreen", 4]
}
const board_actions_by_s_process = {
    "flags" : [],
    "pushes" : ["capture"],
    "destructions" : ["tagscreen_lock", "tagscreen_unlock", "tagscreen_hide"],
    "tagscreens" : ["explosion"],
    "canon" : []
}
const required_total_frames = {
    "tagscreen_lock" : 80,
    "tagscreen_unlock" : 80,
    "tagscreen_hide" : 80,
    "explosion" : 60,
    "capture" : 60
}

// A preamble helpful for certain mathematically-heavy animations, such as
// hourglass sand level calculation

const hourglass_height = 70;
const hourglass_width = 56;
const hourglass_contour_thickness = 1;

// Calculated properties of the hourglass
const x_corner_left = 50 - hourglass_width / 2 + hourglass_contour_thickness;
const y_corner_up = 50 - hourglass_height / 2 + hourglass_contour_thickness;
const x_corner_right = 50 + hourglass_width / 2 - hourglass_contour_thickness;
const y_corner_down = 50 + hourglass_height / 2 - hourglass_contour_thickness;

var sand_levels = [[50 - hourglass_width / 2 + hourglass_contour_thickness, 50 + hourglass_height / 2 - hourglass_contour_thickness]]; // [t] = [x, y] for the left corner of the bottom sand pile. Invert x to get the right; invert y to get the top pile.

/*function hourglass_sand_level(total_height, time_slice) {
    let cur_height = 0.0;
    for (let i = 0; i < time_slice; i++) {
        let h_diff = (total_height / 2.0 - cur_height);
        cur_height += ( h_diff - Math.sqrt(h_diff * h_diff - total_height * total_height / (4.0 * (t_dim - 1))) );
    }
    return cur_height;
}

function hourglass_paths_from_height(time_slice) {
    // returns a list [path of bottom, path of top]
    // If either item is null, that part is simply set to invisible
    let x_corner_left = 50 - hourglass_width / 2 + hourglass_contour_thickness;
    let y_corner_up = 50 - hourglass_height / 2 + hourglass_contour_thickness;
    let x_corner_right = 50 + hourglass_width / 2 - hourglass_contour_thickness;
    let y_corner_down = 50 + hourglass_height / 2 - hourglass_contour_thickness;
    if (time_slice == 0) {
        // Triangle up
        return [
            null,
            [[x_corner_left,y_corner_up], [x_corner_right,y_corner_up], [50,50 - hourglass_contour_thickness]]
            ];
    }
    if (time_slice == t_dim - 1) {
        // Triangle down
        return [
            [[x_corner_left,y_corner_down], [x_corner_right,y_corner_down], [50,50 + hourglass_contour_thickness]],
            null
            ];
    }
    // General case
    let bottom_pile_height = hourglass_sand_level(hourglass_height - 2 * hourglass_contour_thickness, time_slice);
    let top_pile_height = hourglass_height / 2 - hourglass_contour_thickness - bottom_pile_height;
    let bottom_pile_half_width = (hourglass_width - 2 * hourglass_contour_thickness) * (1 - 2 * bottom_pile_height / (hourglass_height - 2 * hourglass_contour_thickness)) / 2;
    let top_pile_half_width = (hourglass_width - 2 * hourglass_contour_thickness) * top_pile_height / (hourglass_height - 2 * hourglass_contour_thickness);

    return [
            [[x_corner_left,y_corner_down], [x_corner_right,y_corner_down], [50 + bottom_pile_half_width,y_corner_down - bottom_pile_height], [50 - bottom_pile_half_width,y_corner_down - bottom_pile_height]],
            [[50 - top_pile_half_width,y_corner_up + bottom_pile_height], [50 + top_pile_half_width,y_corner_up + bottom_pile_height], [50,50 - hourglass_contour_thickness]]
        ];

}*/

var cur_height = 0.0;
for (let i = 1; i < t_dim - 1; i++) {
    let h_diff = ((hourglass_height - 2 * hourglass_contour_thickness) / 2.0 - cur_height);
    cur_height += ( h_diff - Math.sqrt(h_diff * h_diff - (hourglass_height - 2 * hourglass_contour_thickness) * (hourglass_height - 2 * hourglass_contour_thickness) / (4.0 * (t_dim - 1))) );

    // i is the right t
    sand_levels.push([50 - (hourglass_width - 2 * hourglass_contour_thickness) * (1 - 2 * cur_height / (hourglass_height - 2 * hourglass_contour_thickness)) / 2, y_corner_down - cur_height]);
}
sand_levels.push([50, 50 + hourglass_contour_thickness]);

function hourglass_paths_from_height(time_slice, clip_prev_time_slice = false) {
    if (time_slice == 0) {
        // Triangle up (cannot clip prev timeslice as there isnt such a thing)
        if (clip_prev_time_slice) {
            return [null, null];
        }
        return [
            null,
            [[x_corner_left,y_corner_up], [x_corner_right,y_corner_up], [50,50 - hourglass_contour_thickness]]
        ];
    }
    if (time_slice == t_dim - 1) {
        // Triangle down
        if (clip_prev_time_slice) {
            return [
                [[100 - sand_levels[time_slice - 1][0], sand_levels[time_slice - 1][1]], [sand_levels[time_slice - 1][0], sand_levels[time_slice - 1][1]], [50,50 + hourglass_contour_thickness]],
                [[sand_levels[time_slice - 1][0], 100 - sand_levels[time_slice - 1][1]], [100 - sand_levels[time_slice - 1][0], 100 - sand_levels[time_slice - 1][1]], [50,50 - hourglass_contour_thickness]]
            ];
        } else {
            return [
                [[x_corner_left,y_corner_down], [x_corner_right,y_corner_down], [50,50 + hourglass_contour_thickness]],
                null
            ];
        }
    }
    if (clip_prev_time_slice) {
        if (time_slice == 1) {
            return [
                [[x_corner_left, y_corner_down], [x_corner_right, y_corner_down], [sand_levels[time_slice][0], sand_levels[time_slice][1]], [100 - sand_levels[time_slice][0], sand_levels[time_slice][1]]],
                [[x_corner_left,y_corner_up], [x_corner_right,y_corner_up], [100 - sand_levels[time_slice][0], 100 - sand_levels[time_slice][1]], [sand_levels[time_slice][0], 100 - sand_levels[time_slice][1]]]
            ];
        }
        return [
            [[100 - sand_levels[time_slice - 1][0], sand_levels[time_slice - 1][1]], [sand_levels[time_slice - 1][0], sand_levels[time_slice - 1][1]], [sand_levels[time_slice][0], sand_levels[time_slice][1]], [100 - sand_levels[time_slice][0], sand_levels[time_slice][1]]],
            [[sand_levels[time_slice - 1][0], 100 - sand_levels[time_slice - 1][1]], [100 - sand_levels[time_slice - 1][0], 100 - sand_levels[time_slice - 1][1]], [100 - sand_levels[time_slice][0], 100 - sand_levels[time_slice][1]], [sand_levels[time_slice][0], 100 - sand_levels[time_slice][1]]]
        ];
    } else {
        return [
            [[x_corner_left, y_corner_down], [x_corner_right, y_corner_down], [100 - sand_levels[time_slice][0], sand_levels[time_slice][1]], [sand_levels[time_slice][0], sand_levels[time_slice][1]]],
            [[sand_levels[time_slice][0], 100 - sand_levels[time_slice][1]], [100 - sand_levels[time_slice][0], 100 - sand_levels[time_slice][1]], [50,50 - hourglass_contour_thickness]]
        ];
    }

}


function list_of_points_to_path(list_of_points) {
    if (list_of_points.length == 0) {
        return "";
    }
    let res = `${list_of_points[0][0]},${list_of_points[0][1]}`;
    list_of_points.forEach(function(point, index) {
        if (index > 0) {
            res += ` ${list_of_points[index][0]},${list_of_points[index][1]}`;
        }
    });
    return res;
}

function flip_vertically(list_of_points) {
    let res = [];
    list_of_points.forEach(function(point, index) {
        res.push([list_of_points[index][0], 100 - list_of_points[index][1]]);
    });
    return res;
}


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
    // Since all bases have the same sand level, we just need to calculate its properties once
    let sand_paths = hourglass_paths_from_height(time);
    for (let base_i = 0; base_i < bases.length; base_i++) {
        let base_ID = bases[base_i];
        let x = base_trajectories[round_n][time][base_ID][0];
        let y = base_trajectories[round_n][time][base_ID][1];
        let allegiance = base_trajectories[round_n][time][base_ID][2];

        // Find the important DOM elements
        let DOM_parent_group = document.getElementById(`base_${base_ID}`);
        let DOM_sand_bottom = document.getElementById(`base_${base_ID}_hourglass_sand_bottom`);
        let DOM_sand_top = document.getElementById(`base_${base_ID}_hourglass_sand_top`);

        DOM_parent_group.style.transform = `translate(${100 * x}px,${100 * y}px)`;
        DOM_parent_group.setAttribute("class", `base ${base_class_for_base(allegiance)}`);

        // Get rid of all animation effects
        DOM_sand_bottom.classList.remove("sand_fading");
        DOM_sand_top.classList.remove("sand_fading");
        DOM_sand_bottom.style.opacity = 1;
        DOM_sand_top.style.opacity = 1;
        document.getElementById(`base_${base_ID}_rotation`).style.transform = "";
        inbetweens[round_n][time]["tagscreens"]["captured_bases"][0].forEach(function(captured_base_ID, index) {
            let base_trans_bottom = document.getElementById(`${captured_base_ID}_hourglass_sand_bottom_transitory`);
            let base_trans_top = document.getElementById(`${captured_base_ID}_hourglass_sand_top_transitory`);
            // We make them visible but transparent, and in the color of the new allegiance
            base_trans_bottom.style.visibility = "hidden";
            base_trans_bottom.setAttribute("class", `hourglass_sand_bottom_transitory`);
            base_trans_top.style.visibility = "hidden";
            base_trans_top.setAttribute("class", `hourglass_sand_top_transitory`);

        });

        // Update sand paths
        if (sand_paths[0] != null) {
            DOM_sand_bottom.setAttribute("points", list_of_points_to_path(sand_paths[0]));
            DOM_sand_bottom.style.visibility = "visible";
        } else {
            DOM_sand_bottom.style.visibility = "hidden";
        }
        if (sand_paths[1] != null) {
            DOM_sand_top.setAttribute("points", list_of_points_to_path(sand_paths[1]));
            DOM_sand_top.style.visibility = "visible";
        } else {
            DOM_sand_top.style.visibility = "hidden";
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

function show_class_at_state(class_name, scale = null, opacity = null, rotation = null) {
    let class_elements = document.getElementsByClassName(class_name);
    for (let class_index = 0; class_index < class_elements.length; class_index++) {
        if (scale != null) {
            class_elements[class_index].style.transform = `scale(${scale})`;
        } else if (rotation != null) {
            class_elements[class_index].style.transform = `rotate(${rotation}deg)`;
        }
        if (opacity != null) {
            class_elements[class_index].style.opacity = `${opacity}`;
        }
        class_elements[class_index].style.display = `inline`;
    }
}

function show_ids_at_state(list_of_ids, scale = null, opacity = null, rotation = null) {
    for (let id_index = 0; id_index < list_of_ids.length; id_index++) {
        cur_element = document.getElementById(list_of_ids[id_index]);
        if (cur_element != undefined) {
            if (scale != null) {
                cur_element.style.transform = `scale(${scale})`;
            } else if (rotation != null) {
                cur_element.style.transform = `rotate(${rotation}deg)`;
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

// --------------------------- elements generators ----------------------------

// Cloners


function clone_unidentified_template_group(template_group_id) {
    const clone = document.getElementById(template_group_id).cloneNode(true);
    return clone;
}

function clone_TAE(TAE_type, base_class, specific_ID) {
    const clone = document.getElementById(`${TAE_type}_template`).cloneNode(true);

    // Helper: update IDs recursively
    function updateIds(node) {
        // Update class
        if (node.classList) {
            let added_class_names = [];
            Array.from(node.classList).forEach(function(class_name, class_index) {
                added_class_names.push(`${base_class}_${class_name}`);
            });
            added_class_names.forEach(function(added_class_name, added_class_name_index) {
                node.classList.add(added_class_name);
            });
        }

        if (node.id) {
            node.id = node.id.replace(`${TAE_type}_template`, `${specific_ID}`);
        }
        // Recurse into children
        for (let child of node.children) {
            updateIds(child);
        }
    }

    updateIds(clone);
    return clone;
}

// Drawers

function add_arc_to_element(element, base_class, x_i, y_i, x_f, y_f, rad_x, rad_y = -1, arc_param = 0) {
    if (rad_y == -1) {
        rad_y = rad_x;
    }
    element.appendChild(make_SVG_element("path", {
        class : `cloud_bg_${base_class}`,
        d : `M 0 0 L ${x_i} ${y_i} A ${rad_x} ${rad_y} 0 ${arc_param} 1 ${x_f} ${y_f} Z`
    }));
    element.appendChild(make_SVG_element("path", {
        class : `cloud_fg_${base_class}`,
        d : `M ${x_i} ${y_i} A ${rad_x} ${rad_y} 0 ${arc_param} 1 ${x_f} ${y_f}`
    }));
}

function make_smoke_cloud(base_class, base_id) {
    let master_group = make_SVG_element("g", {
        class : base_class,
        id : base_id,
        x : 0,
        y : 0
    });

    let cloud_layers = [];
    for (i = 0; i < 4; i++) {
        cloud_layers.push(make_SVG_element("g", {
            class : "cloud_layer",
            x : 0,
            y : 0
        }));
        cloud_layers[i].classList.add(`cloud_layer_${i}`);
    }

    // layer 0
    cloud_layers[0].appendChild(make_SVG_element("path", {
        class : `cloud_canvas_${base_class}`,
        d : "M -20, 70 A 30 30 0 0 1 -70 40 A 45 45 0 0 1 -70, -20 A 35 35 0 0 1 -30 -65 A 45 45 0 0 1 30 -80 A 40 40 0 0 1 60 -20 A 35 35 0 0 1 55 40 A 45 45 0 0 1 -20 70"
    }));

    // layer 1
    add_arc_to_element(cloud_layers[1], base_class, 80, 10, 45, 40, 25);
    add_arc_to_element(cloud_layers[1], base_class, -60, 50, -70, 10, 20);
    add_arc_to_element(cloud_layers[1], base_class, 35, -60, 55, -40, 16, 16, 1);

    // layer 2
    add_arc_to_element(cloud_layers[2], base_class, 10, 70, -22, 65, 15, 20);
    add_arc_to_element(cloud_layers[2], base_class, -70, 20, -60, -50, 40);
    add_arc_to_element(cloud_layers[2], base_class, 10, -70, 35, -50, 20, 20, 1);
    add_arc_to_element(cloud_layers[2], base_class, 75, -20, 70, 15, 15, 15, 1);

    // layer 3
    add_arc_to_element(cloud_layers[3], base_class, -60, -40, -20, -65, 20);
    add_arc_to_element(cloud_layers[3], base_class, 50, -47, 75, -10, 20);

    for (i = 0; i < 4; i++) {
        master_group.appendChild(cloud_layers[i]);
    }

    master_group.setAttribute("opacity", 0.0);

    return master_group;



}



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
    let causal_freedom_marker_group = make_SVG_element("g", {
        class : "TAE_causal_freedom_marker",
        id : `causal_freedom_marker_${pos_x}_${pos_y}`,
        x : 0,
        y : 0,
        width : 100,
        height : 100,
        display : "none"
    });
    document.getElementById("board_layer_4").appendChild(causal_freedom_marker_group);
    let question_mark = make_SVG_element("text", {
        x : 30,
        y : 80,
        "font-size" : "5em"
    });
    question_mark.textContent = "?";
    causal_freedom_marker_group.appendChild(question_mark);
    causal_freedom_marker_group.style.transform = `translate(${100 * pos_x}px,${100 * pos_y}px)`;
    // No need to add a separate TAE, since these are updated by-class
}
animation_manager.create_stone_action_marker = function(stone_action) {
    switch(true) {
        case arrays_equal(stone_action.slice(0,2), ["tank", "attack"]):
            let tank_attack_group = make_SVG_element("g", {
                class : "TAE_tank_attack",
                id : `TAE_tank_attack_${stone_action[2]}_${stone_action[3]}`,
                x : 0,
                y : 0
            });
            document.getElementById("board_layer_2").appendChild(tank_attack_group);
            let tank_laser_outline = make_SVG_element("line", {
                class : "TAE_tank_laser_outline",
                x1 : 50,
                y1 : 50,
                x2 : 50 + 100*(stone_action[4]-stone_action[2]),
                y2 : 50 + 100*(stone_action[5]-stone_action[3]),
                "stroke" : "red",
                "stroke-width" : 7
            });
            tank_laser_outline.setAttribute("opacity", 0.0);
            tank_attack_group.appendChild(tank_laser_outline);
            let tank_laser_line = make_SVG_element("line", {
                id : `TAE_tank_attack_${stone_action[2]}_${stone_action[3]}_line`,
                x1 : 50,
                y1 : 50,
                x2 : 50,// + 100*(stone_action[4]-stone_action[2]),
                y2 : 50,// + 100*(stone_action[5]-stone_action[3]),
                "stroke" : "red",
                "stroke-width" : 7
            });
            tank_attack_group.appendChild(tank_laser_line);
            tank_attack_group.style.transform = `translate(${100 * stone_action[2]}px,${100 * stone_action[3]}px)`;

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
            let sniper_attack_group = make_SVG_element("g", {
                class : "TAE_sniper_attack",
                id : `TAE_sniper_attack_${stone_action[2]}_${stone_action[3]}`,
                x : 0,
                y : 0
            });
            document.getElementById("board_layer_2").appendChild(sniper_attack_group);
            let sniper_laser_line = make_SVG_element("line", {
                x1 : 50 - 2*(stone_action[4]-stone_action[2]),
                y1 : 50 - 2*(stone_action[5]-stone_action[3]),
                x2 : 50 + 2*(stone_action[4]-stone_action[2]),
                y2 : 50 + 2*(stone_action[5]-stone_action[3]),
                "stroke" : "red",
                "stroke-width" : 5
            });
            sniper_attack_group.appendChild(sniper_laser_line);
            sniper_attack_group.style.transform = `translate(${100 * stone_action[2]}px,${100 * stone_action[3]}px)`;

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
animation_manager.create_board_action_marker = function(board_action_type, board_action) {
    // board_action = [x, y] or other contextual data
    let template_name = board_action_marker_dictionary[board_action_type][0];
    let base_class = `TAE_${board_action_type}`;
    let board_layer = board_action_marker_dictionary[board_action_type][1];

    let board_action_marker_element = clone_TAE(template_name, base_class, `${base_class}_${board_action[0]}_${board_action[1]}`);
    board_action_marker_element.setAttribute("class", base_class);
    board_action_marker_element.setAttribute("id", `${base_class}_${board_action[0]}_${board_action[1]}`);
    board_action_marker_element.style.opacity = 0;
    board_action_marker_element.style.transform = `translate(${100 * board_action[0]}px,${100 * board_action[1]}px)`;
    document.getElementById(`board_layer_${board_layer}`).appendChild(board_action_marker_element);
}

animation_manager.update_temporary_animation_elements = function(frame_key) {
    // frame_key is an integer index of the current frame

    // Firstly we deal with the by-class elements for which no fancy calculation is needed, such as the causal freedom markers
    show_class_at_state("TAE_causal_freedom_marker", null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key, "boomerang"));

    // bombardier explosion
    show_class_at_state("TAE_explosion", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, frame_key, "cloud_opacity"));
    show_class_at_state("explosion_flash", animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key));
    for (i = 0; i < 7; i++) {
        show_class_at_state(`explosion_layer_${i}`, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key, `explosion_layer_${i}`));
    }

    // capture explosion
    show_class_at_state("TAE_capture", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, frame_key, "cloud_opacity"));
    //show_class_at_state("capture_flash", animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key));

    show_class_at_state("TAE_tank_laser_outline", null, animated_scalar_transformation(0.0, 0.2, animation_manager.total_frames, frame_key, "boomerang"));

    for (i = 0; i < 4; i++) {
        show_class_at_state(`cloud_layer_${i}`, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, frame_key, `cloud_layer_${i}`));
    }
    show_class_at_state("TAE_tagscreen_lock", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, frame_key, "cloud_opacity"));
    show_class_at_state("TAE_tagscreen_unlock", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, frame_key, "cloud_opacity"));
    show_class_at_state("TAE_tagscreen_hide", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, frame_key, "cloud_opacity"));


    for (TAE_i = 0; TAE_i < animation_manager.temporary_animation_elements.length; TAE_i++) {
        let cur_TAE = animation_manager.temporary_animation_elements[TAE_i];
        let cur_DOM_element = document.getElementById(cur_TAE["id"]);
        switch(cur_TAE["class"]) {
            case "TAE_tank_attack":
                let cur_x_front = animated_scalar_transformation(50, 50 + 100*(cur_TAE["target_x"]-cur_TAE["x"]), animation_manager.total_frames, frame_key, "cloud_layer_3");
                let cur_y_front = animated_scalar_transformation(50, 50 + 100*(cur_TAE["target_y"]-cur_TAE["y"]), animation_manager.total_frames, frame_key, "cloud_layer_3");
                let cur_x_back = animated_scalar_transformation(50 + 100*(cur_TAE["target_x"]-cur_TAE["x"]), 50, animation_manager.total_frames, animation_manager.total_frames - frame_key, "cloud_layer_3");
                let cur_y_back = animated_scalar_transformation(50 + 100*(cur_TAE["target_y"]-cur_TAE["y"]), 50, animation_manager.total_frames, animation_manager.total_frames - frame_key, "cloud_layer_3");
                let laser_line = document.getElementById(`TAE_tank_attack_${cur_TAE["x"]}_${cur_TAE["y"]}_line`);
                laser_line.setAttribute("x1", cur_x_back);
                laser_line.setAttribute("y1", cur_y_back);
                laser_line.setAttribute("x2", cur_x_front);
                laser_line.setAttribute("y2", cur_y_front);
                break;

            case "TAE_sniper_attack":
                let cur_x = animated_scalar_transformation(100 * cur_TAE["x"], 100 * cur_TAE["target_x"], animation_manager.total_frames, frame_key);
                let cur_y = animated_scalar_transformation(100 * cur_TAE["y"], 100 * cur_TAE["target_y"], animation_manager.total_frames, frame_key);
                cur_DOM_element.style.transform = `translate(${cur_x}px,${cur_y}px)`;
                break;
        }
    }
}

// Stone effects

animation_manager.prepare_stone_effect = function(effect_array) {
    let stone_ID = effect_array[0];
    switch(effect_array[1]) {
        case "tagscreen_lock":
            document.getElementById(`${stone_ID}_tagger_face_lock`).classList.add("active");
            document.getElementById(`${stone_ID}_tagger_face_unlock`).classList.add("disabled");
            document.getElementById(`${stone_ID}_tagger_face_hide`).classList.add("disabled");
            break;
        case "tagscreen_unlock":
            document.getElementById(`${stone_ID}_tagger_face_unlock`).classList.add("active");
            document.getElementById(`${stone_ID}_tagger_face_lock`).classList.add("disabled");
            document.getElementById(`${stone_ID}_tagger_face_hide`).classList.add("disabled");
            break;
        case "tagscreen_hide":
            document.getElementById(`${stone_ID}_tagger_face_hide`).classList.add("active");
            document.getElementById(`${stone_ID}_tagger_face_lock`).classList.add("disabled");
            document.getElementById(`${stone_ID}_tagger_face_unlock`).classList.add("disabled");
            break;
    }
}


animation_manager.cleanup_stone_effect = function(effect_array) {
    let stone_ID = effect_array[0];
    switch(effect_array[1]) {
        case "tagscreen_lock":
            document.getElementById(`${stone_ID}_tagger_face_lock`).classList.remove("active");
            document.getElementById(`${stone_ID}_tagger_face_unlock`).classList.remove("disabled");
            document.getElementById(`${stone_ID}_tagger_face_hide`).classList.remove("disabled");
            break;
        case "tagscreen_unlock":
            document.getElementById(`${stone_ID}_tagger_face_unlock`).classList.remove("active");
            document.getElementById(`${stone_ID}_tagger_face_lock`).classList.remove("disabled");
            document.getElementById(`${stone_ID}_tagger_face_hide`).classList.remove("disabled");
            break;
        case "tagscreen_hide":
            document.getElementById(`${stone_ID}_tagger_face_hide`).classList.remove("active");
            document.getElementById(`${stone_ID}_tagger_face_lock`).classList.remove("disabled");
            document.getElementById(`${stone_ID}_tagger_face_unlock`).classList.remove("disabled");
            break;
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
                if (stone_endpoints[visible_round][inbetweens[round_n][s_time][s_process]["dest_stones"][stone_index]]["end"]["event"] == "causally_free") {
                    animation_manager.create_causal_freedom_marker(inbetweens[round_n][s_time][s_process]["dest_stones_states"][stone_index][0], inbetweens[round_n][s_time][s_process]["dest_stones_states"][stone_index][1]);
                }
            }
        }
    }

    // Create markers for tags when end_process = "tagscreens"
    board_actions_by_s_process[s_process].forEach(function(board_action_type, index) {
        for (let board_action_index = 0; board_action_index < board_actions[round_n][s_time][board_action_type].length; board_action_index++) {
            if (board_action_marker_TAE_classes.includes(board_action_type)) {
                animation_manager.add_TAE_class(`TAE_${board_action_type}`);
                animation_manager.create_board_action_marker(board_action_type, board_actions[round_n][s_time][board_action_type][board_action_index]);
                if (required_total_frames[board_action_type] > animation_manager.total_frames) {
                    animation_manager.total_frames = required_total_frames[board_action_type];
                }
            }
        }
    });
    // Create various markers for stone actions when end_process = "canon"
    if (s_process == "tagscreens") {
        for (let stone_action_index = 0; stone_action_index < stone_actions[round_n][s_time].length; stone_action_index++) {
            let cur_stone_action = stone_actions[round_n][s_time][stone_action_index];
            animation_manager.add_TAE_class(`TAE_${cur_stone_action[0]}_${cur_stone_action[1]}`);
            animation_manager.create_stone_action_marker(cur_stone_action);
        }
    }
    // Notify stones which have effects associated
    if (s_process != "setup") {
        stone_effects[round_n][s_time][s_process].forEach(function(effect_array, effect_index) {
            animation_manager.prepare_stone_effect(effect_array);
        });
    }

    // Prepare time jump markers
    inbetweens[round_n][s_time][s_process]["new_time_jumps"][0].forEach(function(time_jump_mark, index) {
        let new_time_jump_element = document.getElementById(time_jump_mark);
        if (play_backwards) {
            new_time_jump_element.style.opacity = "1";
        } else {
            new_time_jump_element.style.opacity = "0";
        }
        new_time_jump_element.style.fill = `url(#grad_${inbetweens[round_n][s_time][s_process]["new_time_jumps"][1][index]})`;
        new_time_jump_element.style.visibility = "visible";
    });
    inbetweens[round_n][s_time][s_process]["old_time_jumps"][0].forEach(function(time_jump_mark, index) {
        let old_time_jump_element = document.getElementById(time_jump_mark);
        if (play_backwards) {
            old_time_jump_element.style.opacity = "0";
        } else {
            old_time_jump_element.style.opacity = "1";
        }
        old_time_jump_element.style.fill = `url(#grad_${inbetweens[round_n][s_time][s_process]["old_time_jumps"][1][index]})`;
        old_time_jump_element.style.visibility = "visible";
    });

    // Prepare base capture markers
    if (s_process == "tagscreens") {

        // We set the underlying hourglass to its previous state
        if (s_time == 0) {
            show_bases_at_time(0, 0);
        } else {
            show_bases_at_time(round_n, s_time - 1);
        }

        let next_sand_paths = hourglass_paths_from_height(s_time);
        let clipped_sand_paths = hourglass_paths_from_height(s_time, true);

        inbetweens[round_n][s_time][s_process]["captured_bases"][0].forEach(function(captured_base_ID, index) {
            let captured_base_trans_bottom = document.getElementById(`${captured_base_ID}_hourglass_sand_bottom_transitory`);
            let captured_base_trans_top = document.getElementById(`${captured_base_ID}_hourglass_sand_top_transitory`);
            // We make them visible but transparent, and in the color of the new allegiance

            document.getElementById(captured_base_ID).setAttribute("class", `base ${base_class_for_base(inbetweens[round_n][s_time][s_process]["captured_bases"][1][index])}`);
            if (play_backwards) {
                document.getElementById(`${captured_base_ID}_hourglass_sand_bottom`).opacity = 0;
                document.getElementById(`${captured_base_ID}_hourglass_sand_top`).opacity = 0;
                document.getElementById(`${captured_base_ID}_rotation`).style.transform = "rotate(180)";
            }

            // Update sand paths
            if (next_sand_paths[0] != null) {
                captured_base_trans_bottom.setAttribute("points", list_of_points_to_path(flip_vertically(next_sand_paths[0])));
                captured_base_trans_bottom.style.visibility = "visible";
            } else {
                captured_base_trans_bottom.style.visibility = "hidden";
            }
            if (next_sand_paths[1] != null) {
                captured_base_trans_top.setAttribute("points", list_of_points_to_path(flip_vertically(next_sand_paths[1])));
                captured_base_trans_top.style.visibility = "visible";
            } else {
                captured_base_trans_top.style.visibility = "hidden";
            }

            captured_base_trans_bottom.setAttribute("class", `hourglass_sand_bottom_transitory_active ${inbetweens[round_n][s_time][s_process]["captured_bases"][2][index]}_hourglass_sand_bottom_transitory`);
            captured_base_trans_top.setAttribute("class", `hourglass_sand_top_transitory_active ${inbetweens[round_n][s_time][s_process]["captured_bases"][2][index]}_hourglass_sand_top_transitory`);

            captured_base_trans_bottom.style.opacity = play_backwards ? 1 : 0;
            captured_base_trans_top.style.opacity = play_backwards ? 1 : 0;

            document.getElementById(`${captured_base_ID}_hourglass_sand_bottom`).classList.add("sand_fading");
            document.getElementById(`${captured_base_ID}_hourglass_sand_top`).classList.add("sand_fading");

        });

        inbetweens[round_n][s_time][s_process]["stable_bases"][0].forEach(function(stable_base_ID, index) {
            // These just need their transitory sands unflipped and ready to crossfade
            let stable_base_trans_bottom = document.getElementById(`${stable_base_ID}_hourglass_sand_bottom_transitory`);
            let stable_base_trans_top = document.getElementById(`${stable_base_ID}_hourglass_sand_top_transitory`);
            if (play_backwards) {
                document.getElementById(`${stable_base_ID}_hourglass_sand_bottom`).opacity = 0;
                document.getElementById(`${stable_base_ID}_hourglass_sand_top`).opacity = 0;
            }

            // Update sand paths
            if (clipped_sand_paths[0] != null) {
                stable_base_trans_bottom.setAttribute("points", list_of_points_to_path(clipped_sand_paths[0]));
                stable_base_trans_bottom.style.visibility = "visible";
            } else {
                stable_base_trans_bottom.style.visibility = "hidden";
            }
            if (clipped_sand_paths[1] != null) {
                stable_base_trans_top.setAttribute("points", list_of_points_to_path(clipped_sand_paths[1]));
                stable_base_trans_top.style.visibility = "visible";
            } else {
                stable_base_trans_top.style.visibility = "hidden";
            }

            stable_base_trans_bottom.setAttribute("class", `hourglass_sand_bottom_transitory_active ${inbetweens[round_n][s_time][s_process]["stable_bases"][1][index]}_hourglass_sand_bottom_transitory`);
            stable_base_trans_top.setAttribute("class", `hourglass_sand_top_transitory_active negative_hourglass_sand_top_transitory`);

            stable_base_trans_bottom.style.opacity = play_backwards ? 1 : 0;
            stable_base_trans_top.style.opacity = play_backwards ? 1 : 0;

            //document.getElementById(`${stable_base_ID}_hourglass_sand_bottom`).classList.add("sand_fading");
            //document.getElementById(`${stable_base_ID}_hourglass_sand_top`).classList.add("sand_fading");

        });

    }

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
    //              if s_process = "destructions", the stones have vanished as tagscreens were being resolved, which means they were hidden, and shouldn't engorge
    switch(s_process) {
        case "canon":
            show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
            break;
        case "destructions":
            show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
            break;
        default:
            show_stones_at_state(inbetweens[round_n][s_time][s_process]["dest_stones"], inbetweens[round_n][s_time][s_process]["dest_stones_states"], animated_scalar_transformation(1, 2, animation_manager.total_frames, contextual_frame_key), animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));
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

    // Show captured bases turning over and changing color
    show_ids_at_state(append_to_list_of_strings(inbetweens[round_n][s_time][s_process]["captured_bases"][0], "_rotation"), null, null, animated_scalar_transformation(0, 180, animation_manager.total_frames, contextual_frame_key));
    show_class_at_state("hourglass_sand_bottom_transitory_active", null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key));
    show_class_at_state("hourglass_sand_top_transitory_active", null, animated_scalar_transformation(0.0, 1.0, animation_manager.total_frames, contextual_frame_key));
    show_class_at_state("sand_fading", null, animated_scalar_transformation(1.0, 0.0, animation_manager.total_frames, contextual_frame_key));

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
    // Notify stones which have effects associated
    if (s_process != "setup") {
        stone_effects[round_n][s_time][s_process].forEach(function(effect_array, effect_index) {
            animation_manager.cleanup_stone_effect(effect_array);
        });
    }
    // Hide base capture markers
    inbetweens[round_n][s_time][s_process]["captured_bases"][0].forEach(function(captured_base_ID, index) {
        document.getElementById(`${captured_base_ID}_hourglass_sand_bottom`).classList.remove("sand_fading");
        document.getElementById(`${captured_base_ID}_hourglass_sand_top`).classList.remove("sand_fading");
        document.getElementById(`${captured_base_ID}_hourglass_sand_bottom`).style.opacity = 1;
        document.getElementById(`${captured_base_ID}_hourglass_sand_top`).style.opacity = 1;

        let base_trans_bottom = document.getElementById(`${captured_base_ID}_hourglass_sand_bottom_transitory`);
        let base_trans_top = document.getElementById(`${captured_base_ID}_hourglass_sand_top_transitory`);
        // We make them visible but transparent, and in the color of the new allegiance
        base_trans_bottom.style.visibility = "hidden";
        base_trans_bottom.setAttribute("class", `hourglass_sand_bottom_transitory`);
        base_trans_top.style.visibility = "hidden";
        base_trans_top.setAttribute("class", `hourglass_sand_top_transitory`);

        if (play_backwards) {
            document.getElementById(captured_base_ID).setAttribute("class", `base ${base_class_for_base(inbetweens[round_n][s_time][s_process]["captured_bases"][1][index])}`);
        } else {
            document.getElementById(captured_base_ID).setAttribute("class", `base ${base_class_for_base(inbetweens[round_n][s_time][s_process]["captured_bases"][2][index])}`);
        }

    });
    inbetweens[round_n][s_time][s_process]["stable_bases"][0].forEach(function(stable_base_ID, index) {
        document.getElementById(`${stable_base_ID}_hourglass_sand_bottom`).classList.remove("sand_fading");
        document.getElementById(`${stable_base_ID}_hourglass_sand_top`).classList.remove("sand_fading");
        document.getElementById(`${stable_base_ID}_hourglass_sand_bottom`).style.opacity = 1;
        document.getElementById(`${stable_base_ID}_hourglass_sand_top`).style.opacity = 1;

        let stable_base_trans_bottom = document.getElementById(`${stable_base_ID}_hourglass_sand_bottom_transitory`);
        let stable_base_trans_top = document.getElementById(`${stable_base_ID}_hourglass_sand_top_transitory`);
        // We make them visible but transparent, and in the color of the new allegiance
        stable_base_trans_bottom.style.visibility = "hidden";
        stable_base_trans_bottom.setAttribute("class", `hourglass_sand_bottom_transitory`);
        stable_base_trans_top.style.visibility = "hidden";
        stable_base_trans_top.setAttribute("class", `hourglass_sand_top_transitory`);
    });
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
    "total_frames" : 150,
    "frame_latency" : 2
});


