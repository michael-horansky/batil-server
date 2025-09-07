
// ----------------------------------------------------------------------------
// --------------------------- Rendering constants ----------------------------
// ----------------------------------------------------------------------------
const board_window_width = 800;
const board_window_height = 700;

const stone_command_btn_width = 140;
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

function base_highlight(base_ID) {
    return `<span class=\"base_highlight\">BASE [P. ${bases[base_ID]["faction"]}]</span>`;
}

function stone_highlight(stone_ID) {
    return `<span class=\"stone_highlight\">${stones[stone_ID]["stone_type"].toUpperCase()} [P. ${stones[stone_ID]["faction"]}]</span>`;
}

function square_highlight(x, y) {
    return `<span class=\"square_highlight\" onclick=\"go_to_square(${x},${y})\">(${x},${y})</tspan>`;
}

// ----------------------------------------------------------------------------
// ---------------------------------- Events ----------------------------------
// ----------------------------------------------------------------------------

function parse_keydown_event(event) {
    //alert(event.key);
    // If the focus is on a textbox, we ignore keypresses
    if (event.target.tagName === "INPUT" ||
        event.target.tagName === "TEXTAREA" ||
        event.target.isContentEditable) {
        return;
    }

    switch(event.key) {
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
            if (inspector.highlighted_square != null) {
                inspector.unselect_all();
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
    "base" : {"title" : null, "containers" : new Object(), "values" : new Object()}
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
inspector.record_inspector_elements("base", ["allegiance"]);

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

// General stone properties

inspector.display_element_info = function(x, y) {
    // Is there even an element present?
    let base_ID = find_base_at_pos(x, y);
    let stone_ID = find_stone_at_pos(x, y);

    if (stone_ID != null) {
        inspector.inspector_elements["stone"]["title"].innerHTML = `A ${stone_highlight(stone_ID)} selected`;
        inspector.display_value_list("stone", "allegiance", [stones[stone_ID]["faction"]]);
        inspector.display_value_list("stone", "stone_type", [stones[stone_ID]["stone_type"].toUpperCase()]);

    } else if (base_ID != null) {
        inspector.inspector_elements["stone"]["title"].innerHTML = `A ${base_highlight(base_ID)} selected`;
        inspector.display_value_list("base", "allegiance", [bases[base_ID]["faction"]]);

    } else {
        inspector.inspector_elements["stone"]["title"].innerHTML = "No element selected";
        inspector.display_value_list("stone", "allegiance", []);
        inspector.display_value_list("stone", "stone_type", []);
    }

    return stone_ID;
}

inspector.hide_stone_info = function() {
    inspector.inspector_elements["stone"]["title"].innerHTML = "No element selected";
    document.getElementById("base_info_table").style.display = "none";
    document.getElementById("stone_info_table").style.display = "none";
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
}


inspector.hide_square_info = function() {

    // Highligh square, reset stone highlight
    inspector.set_square_highlight(null);
    document.getElementById("square_inspector_title").innerHTML = `No square selected`;
}

inspector.board_square_click = function(x, y){
    // We get information about the stone
    inspector.display_element_info(x, y);
    // We get information about the square
    inspector.display_square_info(x, y);
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
