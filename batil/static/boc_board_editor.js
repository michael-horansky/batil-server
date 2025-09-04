
// ----------------------------------------------------------------------------
// --------------------------- Rendering constants ----------------------------
// ----------------------------------------------------------------------------
const board_window_width = 800;
const board_window_height = 700;

const stone_command_btn_width = 100;
const stone_command_btn_height = 83;

const choice_option_btn_width = 120;
const choice_option_btn_height = 83;

const is_orientable = {
    "tank" : true,
    "bombardier" : false,
    "tagger" : false,
    "sniper" : true,
    "wildcard" : false
};

// ----------------------------------------------------------------------------
// --------------------------- HTML DOM management ----------------------------
// ----------------------------------------------------------------------------

function write_to_html(html_object){
    // If html_object is a string, it is printed into the html document
    // If it is an array of strings, all elements are printed into the html document sequentially, flattening the array (levels can be multiple)
    if(typeof html_object === 'string') {
        document.write(html_object);
    } else {
        for (let i = 0; i < html_object.length; i++) {
            write_to_html(html_object[i]);
        }
    }

}

function make_SVG_element(tag, attrs) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs) {
      el.setAttribute(k, attrs[k]);
    }
    return el;
}

function remove_elements_by_class(class_name){
    const elements = document.getElementsByClassName(class_name);
    while(elements.length > 0){
        elements[0].parentNode.removeChild(elements[0]);
    }
}

// ----------------------------------------------------------------------------
// ---------------------------------- Logic -----------------------------------
// ----------------------------------------------------------------------------


function find_base_at_pos(x, y) {
    for (let base_i = 0; base_i < bases.length; base_i++) {
        if (bases[base_i]["x"] == x && bases[base_i]["y"] == y) {
            return base_i;
        }
    }
    return null;
}

function find_stone_at_pos(x, y) {
    for (let stone_i = 0; stone_i < stones.length; stone_i++) {
        if (stones[stone_i]["x"] == x && stones[stone_i]["y"] == y) {
            return stone_i;
        }
    }
    return null;
}

function bound(val, lower_bound, upper_bound) {
    return Math.max(lower_bound, Math.min(val, upper_bound));
}

function arrays_equal(arr1, arr2) {
    return arr1.every((value, index) => value == arr2[index]);
}

function inds(obj, inds, to_str = true) {
    // accesses an element of object from a stack of indices, or returns undefined if indices don't exist
    // if to_str, indices are automatically converted to strings
    let obj_stack = [obj];
    if (to_str) {
        for (inds_i = 0; inds_i < inds.length; inds_i++) {
            if (obj_stack[inds_i][inds[inds_i].toString()] == undefined) {
                return undefined;
            }
            obj_stack.push(obj_stack[inds_i][inds[inds_i].toString()]);
        }
    } else {
        for (inds_i = 0; inds_i < inds.length; inds_i++) {
            if (obj_stack[inds_i][inds[inds_i]] == undefined) {
                return undefined;
            }
            obj_stack.push(obj_stack[inds_i][inds[inds_i]]);
        }
    }
    return obj_stack[inds.length];
}

// ----------------------------------------------------------------------------
// ---------------------- Graphical attribute management ----------------------
// ----------------------------------------------------------------------------


function render_board(){
    purify_board();
    render_board_static();
    render_bases();
    render_stones();
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

function purify_board() {
    // Deletes all bases, stones, and board squares from their respective groups
    document.getElementById('group_stones').replaceChildren();
    document.getElementById('group_bases').replaceChildren();
    document.getElementById('group_squares').replaceChildren();
}

// Square rendering

function encode_board_square_class(square_type) {
    switch (square_type) {
        case " ":
            return "board_square_empty";
        case "X":
            return "board_square_wall";
        default:
            return "board_square_unknown";
    }
}

function clone_square(square_class, x, y) {
    // Deep clone
    const clone = document.getElementById(`${square_class}_template`).cloneNode(true);

    // Helper: update IDs recursively
    function updateIds(node) {
        node.id = `board_square_${x}_${y}`;
    }

    updateIds(clone);
    return clone;
}

function make_square(x, y, square_type) {
    /*let new_square = make_SVG_element("rect", {
        class : encode_board_square_class(square_type),
        id : `board_square_${x}_${y}`,
        x : x * 100,
        y : y * 100,
        width : 100,
        height : 100,
        onclick : `inspector.board_square_click(${x},${y})`
    });*/
    let new_square = clone_square(encode_board_square_class(square_type), x, y);
    new_square.onclick = `inspector.board_square_click(${x},${y})`;
    document.getElementById("group_squares").appendChild(new_square);
}

function render_board_static() {
    for (x = 0; x < x_dim; x++) {
        for (y = 0; y < y_dim; y++) {
            make_square(x, y, board_static[x][y]);
            document.getElementById(`board_square_${x}_${y}`).style.display = "inline";
        }
    }
}

// Base rendering

function clone_base(base_allegiance, x, y) {
    const clone = document.getElementById(`base_${base_allegiance}_template`).cloneNode(true);

    // Helper: update IDs recursively
    function updateIds(node) {
        if (node.id) {
            node.id = node.id.replace(`base_${base_allegiance}_template`, `base_${x}_${y}`);
        }
        // Recurse into children
        for (let child of node.children) {
            updateIds(child);
        }
    }

    updateIds(clone);
    return clone;
}

function render_bases() {
    let parent_node = document.getElementById('group_bases');
    for (let base_i = 0; base_i < bases.length; base_i++) {
        let x = bases[base_i]["x"];
        let y = bases[base_i]["y"];
        let allegiance = bases[base_i]["faction"];

        let new_base = clone_base(allegiance, x, y);
        parent_node.appendChild(new_base);

        document.getElementById(`base_${x}_${y}`).style.transform = `translate(${100 * x}px,${100 * y}px)`;
        document.getElementById(`base_${x}_${y}`).style.display = "inline";
    }
}

// Stone rendering

function clone_stone(stone_allegiance, stone_type, x, y) {
    const clone = document.getElementById(`${stone_allegiance}_${stone_type}_template`).cloneNode(true);

    // Helper: update IDs recursively
    function updateIds(node) {
        if (node.id) {
            node.id = node.id.replace(`${stone_allegiance}_${stone_type}_template`, `stone_${x}_${y}`);
        }
        // Recurse into children
        for (let child of node.basechildren) {
            updateIds(child);
        }
    }

    updateIds(clone);
    return clone;
}

function render_stones(){
    for (let stone_i = 0; stone_i < stones.length; stone_i++) {
        let x = stones[stone_i]["x"];
        let y = stones[stone_i]["y"];
        let stone_allegiance = stones[stone_i]["faction"];
        let stone_type = stones[stone_i]["type"];

        let new_stone = clone_stone(stone_allegiance, stone_type, x, y);
        parent_node.appendChild(new_stone);

        document.getElementById(`stone_${x}_${y}`).style.transform = `translate(${100 * x}px,${100 * y}px)`;
        if (is_orientable[stone_type]) {
            document.getElementById(`stone_${x}_${y}_rotation`).style.transform = `rotate(${90 * stones[stone_i]["a"]}deg)`;
        }
        document.getElementById(`stone_${x}_${y}`).style.display = "inline";
    }
}

// ----------------------------------------------------------------------------
// -------------------------------- Cameraman ---------------------------------
// ----------------------------------------------------------------------------
// This object is concerned with repositioning all the objects in board_window
// as the camera moves.

const cameraman = new Object();
cameraman.camera_zoom_status = "idle";
cameraman.camera_move_keys_pressed = 0;
cameraman.camera_move_directions = {"w" : false, "d" : false, "s" : false, "a" : false};
cameraman.camera_zoom_daemon = null;
cameraman.camera_zoom_directions = {"in" : false, "out" : false};
cameraman.camera_move_daemon = null;
// Manimpulation constants
cameraman.zoom_speed = 1.01;
cameraman.movement_speed = 0.003;
cameraman.refresh_rate = 5; // ms
// Position of the camera centre
cameraman.cx = 0.5;
cameraman.cy = 0.5;
// The camera forces a square aspect ratio, and hence the field-of-view size is
// parametrised by a single parameter, here chosen to represent the coefficient
// of the base length of a board square
cameraman.fov_coef = 1.0;
// --------------------------------- Methods ----------------------------------

cameraman.put_down_tripod = function() {
    // Find the default setting, which just about displays the entire board
    let default_width_fov_coef = board_window_width / (x_dim * 100);
    let default_height_fov_coef = board_window_height / (y_dim * 100);
    cameraman.default_fov_coef = Math.min(default_width_fov_coef, default_height_fov_coef); // This is also the max value!
    cameraman.max_fov_coef = board_window_width / 400;
    // Find an offset which places the middle of the board into the middle of the board window
    cameraman.offset_x = board_window_width * 0.5 - x_dim * 50;
    cameraman.offset_y = board_window_height * 0.5 - y_dim * 50;

    // Find and store the element which is target to camera's transformations
    cameraman.subject = document.getElementById("camera_subject");
}

cameraman.apply_camera = function() {
    cameraman.subject.style.transform = `translate(${cameraman.offset_x + x_dim * 100 * (0.5 - cameraman.cx) * cameraman.fov_coef}px,${cameraman.offset_y + y_dim * 100 * (0.5 - cameraman.cy) * cameraman.fov_coef}px) scale(${cameraman.fov_coef})`;
}

cameraman.reset_camera = function() {
    cameraman.fov_coef = cameraman.default_fov_coef;
    cameraman.cx = 0.5;
    cameraman.cy = 0.5;
    cameraman.apply_camera();
}


// ------------------------------ Camera zooming ------------------------------

cameraman.zoom_camera = function() {
    if (cameraman.camera_zoom_directions["in"] && (! cameraman.camera_zoom_directions["out"])) {
        cameraman.fov_coef = Math.min(cameraman.fov_coef * cameraman.zoom_speed, cameraman.max_fov_coef);
    } else if (cameraman.camera_zoom_directions["out"] && (! cameraman.camera_zoom_directions["in"])) {
        cameraman.fov_coef = Math.max(cameraman.fov_coef / cameraman.zoom_speed, cameraman.default_fov_coef);
    }
    if (!cameraman.used_by_an_animation) {
        cameraman.apply_camera();
    }
}

// ----------------------------- Camera movement ------------------------------

cameraman.move_camera = function() {
    if (cameraman.camera_move_directions["w"]) {
        cameraman.cy -= cameraman.movement_speed / cameraman.fov_coef;
    }
    if (cameraman.camera_move_directions["d"]) {
        cameraman.cx += cameraman.movement_speed / cameraman.fov_coef;
    }
    if (cameraman.camera_move_directions["s"]) {
        cameraman.cy += cameraman.movement_speed / cameraman.fov_coef;
    }
    if (cameraman.camera_move_directions["a"]) {
        cameraman.cx -= cameraman.movement_speed / cameraman.fov_coef;
    }
    cameraman.cx = Math.max(0.0, Math.min(1.0, cameraman.cx));
    cameraman.cy = Math.max(0.0, Math.min(1.0, cameraman.cy));
    cameraman.apply_camera();
}

cameraman.show_square = function(x, y) {
    cameraman.cx = (x + 0.5) / x_dim;
    cameraman.cy = (y + 0.5) / y_dim;
    cameraman.apply_camera();
}

// --------------------------- Camera event parsers ---------------------------

cameraman.move_key_down = function(move_key) {
    if (cameraman.camera_move_keys_pressed == 0) {
        cameraman.camera_move_daemon = setInterval(cameraman.move_camera, cameraman.refresh_rate);
    }
    if (!(cameraman.camera_move_directions[move_key])) {
        cameraman.camera_move_keys_pressed += 1;
        cameraman.camera_move_directions[move_key] = true;
    }
}

cameraman.move_key_up = function(move_key) {
    if (cameraman.camera_move_directions[move_key]) {
        cameraman.camera_move_keys_pressed -= 1;
        cameraman.camera_move_directions[move_key] = false;
    }
    if (cameraman.camera_move_keys_pressed == 0) {
        clearInterval(cameraman.camera_move_daemon);
    }
}

cameraman.zoom_key_down = function(zoom_key) {
    if (!(cameraman.camera_zoom_directions["in"] || cameraman.camera_zoom_directions["out"])) {
        cameraman.camera_zoom_daemon = setInterval(cameraman.zoom_camera, cameraman.refresh_rate);
    }
    if (!(cameraman.camera_zoom_directions[zoom_key])) {
        cameraman.camera_zoom_directions[zoom_key] = true;
    }
}

cameraman.zoom_key_up = function(zoom_key) {
    if (cameraman.camera_zoom_directions[zoom_key]) {
        cameraman.camera_zoom_directions[zoom_key] = false;
    }
    if (!(cameraman.camera_zoom_directions["in"] || cameraman.camera_zoom_directions["out"])) {
        clearInterval(cameraman.camera_zoom_daemon);
    }
}

var highlighted_stone = null;
function set_stone_highlight(stone_ID) {
    if (stone_ID != highlighted_stone && highlighted_stone != null) {
        // Change of the guard
        document.getElementById(`stone_${highlighted_stone}`).style.filter = "";
    }
    highlighted_stone = stone_ID
    if (stone_ID != null) {
        document.getElementById(`stone_${stone_ID}`).style.filter = "url(#spotlight)";
    }
}


function base_highlight(base_ID) {
    return `<span class=\"base_highlight\" onmouseenter=\"set_base_highlight(${base_ID})\" onmouseleave=\"set_base_highlight(null)\" \">BASE [P. ${bases[base_ID]["faction"]}]</span>`;
}

function stone_highlight(stone_ID) {
    return `<span class=\"stone_highlight\" onmouseenter=\"set_stone_highlight(${stone_ID})\" onmouseleave=\"set_stone_highlight(null)\" \">${stones[stone_ID]["type"].toUpperCase()} [P. ${stones[stone_ID]["faction"]}]</span>`;
}

function square_highlight(x, y) {
    return `<span class=\"square_highlight\" onclick=\"go_to_square(${x},${y})\">(${x},${y})</tspan>`;
}

// ----------------------------------------------------------------------------
// ---------------------------------- Events ----------------------------------
// ----------------------------------------------------------------------------

function parse_keydown_event(event) {
    //alert(event.key);
    switch(event.key) {
        case "ArrowRight":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(1);
                document.getElementById(`azimuth_indicator_1`).style["fill-opacity"] = 0.7;
            }
            break
        case "ArrowLeft":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(3);
                document.getElementById(`azimuth_indicator_3`).style["fill-opacity"] = 0.7;
            }
            break
        case "ArrowUp":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(0);
                document.getElementById(`azimuth_indicator_0`).style["fill-opacity"] = 0.7;
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
        case "Escape":
            // The "Escape" behaviour is highly contextual, and the different
            // contexts it affects are sorted by priority as follows:
            //   1. Exits selection mode if board is in selection mode--otherwise,
            //   2. unselects square if selected
            if (inspector.selection_mode_enabled) {
                inspector.turn_off_selection_mode();
            } else if (inspector.highlighted_square != null) {
                inspector.unselect_all();
            }
            break;
        case "Enter":
            if (inspector.selection_mode_enabled && (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false && inspector.selection_mode_information_level["swap_effect"] == false)) {
                inspector.submit_selection();
            }
            break;

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



// -------------------------------- Commander ---------------------------------
// Commander updates the hidden board save form every time one of the board
// properties is updated, which entails deleting and adding input elements.

const commander = new Object();

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


inspector.record_inspector_elements("stone", ["allegiance", "stone_type"]);
//inspector.record_inspector_elements("square", []);

// ----------------------- Human readable text methods ------------------------

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
// This is for placing objects from inventory onto the board

// Information level: for every "true", the user needs to specify the value of
// the corresponding arg key before submitting the command and exiting sel. m.
inspector.selection_mode_enabled = false;
inspector.selection_mode_stone_ID = null;
inspector.selection_mode_information_level = {"square" : false, "azimuth" : false, "choice_option" : false};
inspector.selection = {"square" : "NOT_SELECTED", "azimuth" : "NOT_SELECTED", "choice_option" : "NOT_SELECTED"};
inspector.selection_submission = null;

inspector.selection_mode_options = new Object();

inspector.selection_keywords = [
            "object",  // base or stone
            "faction", // GM, A, B
            "type",    // [stones only]
            "x",
            "y",
            "a"        // [orientable stones only]
        ];

inspector.turn_on_selection_mode = function(placing_object, selection_mode_props) {
    inspector.selection_mode_enabled = true;
    // Commit current selection options to cache
    inspector.selection_mode_options = selection_mode_props;

    inspector.selection_mode_information_level["square"] = true;
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.selection_mode_information_level["choice_option"] = true;
    inspector.selection_mode_information_level["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["choice_option"] = "NOT_SELECTED";

    // Show selection highlights
    inspector.set_square_highlight(null);
    document.getElementById("selection_mode_highlights").style.visibility = "visible";

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


    render_board();

}

inspector.turn_off_selection_mode = function() {

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
    //document.getElementById("choice_selector").style.display = "none";
    //document.getElementById("swap_effect_selector").style.display = "none";
    document.getElementById("faction_inspector").style.display = "block";
    document.getElementById("square_inspector").style.display = "block";


    inspector.selection_mode_enabled = false;

    render_board();

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
            render_board();
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
            render_board();

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
        render_board();
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
    inspector.display_element_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
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

inspector.get_available_commands = function(stone_ID) {
    // Depends purely on static stone data
    stone_faction = stones[stone_ID]["faction"];
    stone_type = stones[stone_ID]["type"];
    let available_commands = [["remove", "Remove stone"]];
    if (static_stone_data[stone_type]["orientable"]) {
        available_commands.push(["rotate", "Change azimuth"]);
    }
    return available_commands;
}

inspector.display_stone_commands = function(stone_ID) {
    // If select square has a stone, we display the relevant buttons


    //document.getElementById("base_inspector_buttons_svg").style.display = "none";
    document.getElementById("stone_inspector_buttons_svg").style.display = "block";
    // if stone_ID = null, hides stone commands
    let stone_inspector_buttons_svg = document.getElementById("stone_inspector_buttons_svg");
    if (stone_ID == null) {
        while (stone_inspector_buttons_svg.firstChild) {
            stone_inspector_buttons_svg.removeChild(stone_inspector_buttons_svg.lastChild);
        }
    } else {
        // First, we delete everything
        inspector.display_stone_commands(null);

        // Now, we find the list of commands
        let list_of_commands = inspector.get_available_commands(stone_ID);

        // We draw every button
        offset_x = 0;
        offset_y = 0;
        for (let i = 0; i < list_of_commands.length; i++) {
            let new_button = make_SVG_element("rect", {
                class : "stone_command_panel_button",
                id : `stone_command_${list_of_commands[i][0]}`,
                onclick : `inspector.prepare_command(${stone_ID}, \"${list_of_commands[i][0]}\")`,
                x : offset_x,
                y : 0,
                width : stone_command_btn_width,
                height : stone_command_btn_height
            });
            let new_button_label = make_SVG_element("text", {
                class : "button_label",
                id : `stone_command_${list_of_commands[i][0]}_label`,
                x : offset_x + stone_command_btn_width / 2,
                y : stone_command_btn_height / 2,
                "text-anchor" : "middle"
            });
            new_button_label.textContent = list_of_commands[i][1];
            stone_inspector_buttons_svg.appendChild(new_button);
            stone_inspector_buttons_svg.appendChild(new_button_label);
            offset_x += 110;

        }
    }
}

inspector.display_undo_button = function() {
    document.getElementById("stone_inspector_buttons_svg").style.display = "none";
    document.getElementById("undo_command_button_svg").style.display = "block";
}



// General stone properties

inspector.display_element_info = function(x, y) {
    // Is there even an element present?
    let base_ID = find_base_at_pos(x, y);
    let stone_ID = find_stone_at_pos(x, y);
    inspector.inspector_elements["stone"]["title"].innerHTML = (stone_ID == null ? "No stone selected" : `A ${stone_highlight(stone_ID)} selected`);

    if (stone_ID != null) {
        inspector.display_value_list("stone", "allegiance", [stones[stone_ID]["faction"]]);
        inspector.display_value_list("stone", "stone_type", [stones[stone_ID]["type"].toUpperCase()]);

        inspector.display_stone_commands(stone_ID);

    } else {
        inspector.display_value_list("stone", "allegiance", []);
        inspector.display_value_list("stone", "stone_type", []);
        inspector.display_stone_commands(null);
    }

    return stone_ID;
}

inspector.hide_stone_info = function() {
    inspector.inspector_elements["stone"]["title"].innerHTML = "No stone selected";
    inspector.display_value_list("stone", "allegiance", []);
    inspector.display_value_list("stone", "stone_type", []);
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

    // Highligh square, reset stone highlight
    inspector.set_square_highlight([x, y]);
    document.getElementById("square_inspector_title").innerHTML = `${inspector.square_type_description(board_static[x][y])} selected`;
    set_stone_highlight(null);
}


inspector.hide_square_info = function() {

    // Highligh square, reset stone highlight
    inspector.set_square_highlight(null);
    document.getElementById("square_inspector_title").innerHTML = `No square selected`;
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
        inspector.display_element_info(x, y);
        // We get information about the square
        inspector.display_square_info(x, y);
    }
}

inspector.display_highlighted_info = function() {
    inspector.display_element_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
    inspector.display_square_info(inspector.highlighted_square[0], inspector.highlighted_square[1]);
}

inspector.unselect_all = function() {
    inspector.hide_stone_info();
    inspector.hide_square_info();
}


function go_to_square(x, y) {
    if (!inspector.selection_mode_enabled) {
        cameraman.show_square(x, y);
        inspector.display_element_info(x, y);
        inspector.display_square_info(x, y);
    }
}

// ----------------------------------------------------------------------------
// ------------------------------ Document setup ------------------------------
// ----------------------------------------------------------------------------

var all_factions = ["GM", "A", "B"];

// -------------------------- Initial display setup ---------------------------
var selection_mode = false;

// Set up the camera
cameraman.put_down_tripod();
cameraman.reset_camera();

// Set up commander if game in progress

// Set up inspector
inspector.hide_stone_info();
inspector.hide_square_info();

