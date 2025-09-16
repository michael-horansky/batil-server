
// ----------------------------------------------------------------------------
// --------------------------- Rendering constants ----------------------------
// ----------------------------------------------------------------------------
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
    reset_board_dimensions_form();
    if (inspector.selection_mode_enabled) {
        // We take care of the selection choice highlighting
        for (x = 0; x < x_dim; x++) {
            for (y = 0; y < y_dim; y++) {
                document.getElementById(`selection_mode_highlight_${x}_${y}`).style.fill = "grey";
            }
        }
        for (i = 0; i < inspector.selection_mode_squares.length; i++) {
            document.getElementById(`selection_mode_highlight_${inspector.selection_mode_squares[i]["x"]}_${inspector.selection_mode_squares[i]["y"]}`).style.fill = "green";
        }
        // If a choice has been made, we place the selection mode dummy at its appropriate place
        selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
        for (i = 0; i < selection_mode_dummies.length; i++) {
            selection_mode_dummies[i].style.display = "none";
        }
        if (inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false) {
            let selected_square = inspector.selection_mode_squares[inspector.selection["square"]];
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

function reset_board_dimensions_form() {
    document.getElementById("board_dimensions_t_input").value = t_dim;
    document.getElementById("board_dimensions_x_input").value = x_dim;
    document.getElementById("board_dimensions_y_input").value = y_dim;

    document.getElementById("board_dimensions_update_btn").hidden = true;
    document.getElementById("board_dimensions_reset_btn").hidden = true;
}

function toggle_board_dimensions_buttons() {
    if (Number(document.getElementById("board_dimensions_t_input").value) != t_dim
        || Number(document.getElementById("board_dimensions_x_input").value) != x_dim
        || Number(document.getElementById("board_dimensions_y_input").value) != y_dim) {
        document.getElementById("board_dimensions_update_btn").hidden = false;
        document.getElementById("board_dimensions_reset_btn").hidden = false;
    } else {
        document.getElementById("board_dimensions_update_btn").hidden = true;
        document.getElementById("board_dimensions_reset_btn").hidden = true;
    }
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
    new_square.setAttribute('x', x * 100);
    new_square.setAttribute('y', y * 100);
    new_square.setAttribute("onclick", `inspector.board_square_click(${x},${y})`);
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
        for (let child of node.children) {
            updateIds(child);
        }
    }

    updateIds(clone);
    return clone;
}

function render_stones(){
    let parent_node = document.getElementById('group_stones');
    for (let stone_i = 0; stone_i < stones.length; stone_i++) {
        let x = stones[stone_i]["x"];
        let y = stones[stone_i]["y"];
        let stone_allegiance = stones[stone_i]["faction"];
        let stone_type = stones[stone_i]["stone_type"];

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

// Board window dimensions
cameraman.board_window = document.getElementById("board_window_svg");
cameraman.board_dimensions = {"width" : 0, "height" : 0};


cameraman.resize_observer = new ResizeObserver(entries => {
  for (let entry of entries) {
    cameraman.update_board_dimension();
  }
});

cameraman.resize_observer.observe(cameraman.board_window);

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

cameraman.update_board_dimension = function() {
    const rect = cameraman.board_window.getBoundingClientRect();
    cameraman.board_dimensions.width = rect.width;
    cameraman.board_dimensions.height = rect.height;

    // Now for what needs to update.
    // 1. tripod readjustment
    cameraman.put_down_tripod();
    // 2. repositioning of azimuth indicators
    cameraman.reposition_board_elements();
    // 3. apply camera
    cameraman.apply_camera();
}

cameraman.put_down_tripod = function() {
    // Find the default setting, which just about displays the entire board
    let default_width_fov_coef = cameraman.board_dimensions.width / (x_dim * 100);
    let default_height_fov_coef = cameraman.board_dimensions.height / (y_dim * 100);
    cameraman.default_fov_coef = Math.min(default_width_fov_coef, default_height_fov_coef); // This is also the max value!
    cameraman.max_fov_coef = Math.max(cameraman.board_dimensions.width / 400, 1.0);
    // Find an offset which places the middle of the board into the middle of the board window
    cameraman.offset_x = cameraman.board_dimensions.width * 0.5 - x_dim * 50;
    cameraman.offset_y = cameraman.board_dimensions.height * 0.5 - y_dim * 50;

    // Find and store the element which is target to camera's transformations
    cameraman.subject = document.getElementById("camera_subject");
    cameraman.subject.setAttribute("transform-origin", `${x_dim * 50}px ${y_dim * 50}px`);
}

cameraman.reposition_board_elements = function() {
    // azimuth indicators
    const triangle_offset = 0.1;
    for (azimuth = 0; azimuth < 4; azimuth++) {
        let offset_x = 0;
        let offset_y = 0;
        if (azimuth == 0) {
            offset_x = cameraman.board_dimensions.width / 2;
            offset_y = cameraman.board_dimensions.height * triangle_offset;
        } else if (azimuth == 1) {
            offset_x = cameraman.board_dimensions.width * (1 - triangle_offset);
            offset_y = cameraman.board_dimensions.height / 2;
        } else if (azimuth == 2) {
            offset_x = cameraman.board_dimensions.width / 2;
            offset_y = cameraman.board_dimensions.height * (1 - triangle_offset);
        } else if (azimuth == 3) {
            offset_x = cameraman.board_dimensions.width * triangle_offset;
            offset_y = cameraman.board_dimensions.height / 2;
        }
        document.getElementById(`azimuth_indicator_${azimuth}`).style.transform = `translate(${offset_x}px,${offset_y}px)`;
    }
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
        cameraman.fov_coef = Math.max(cameraman.fov_coef / cameraman.zoom_speed, Math.min(cameraman.default_fov_coef, 1.0));
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
    return `<span class=\"base_highlight\" >BASE [P. ${bases[base_ID]["faction"]}]</span>`;
}

function stone_highlight(stone_ID) {
    return `<span class=\"stone_highlight\" >${stones[stone_ID]["stone_type"].toUpperCase()} [P. ${stones[stone_ID]["faction"]}]</span>`;
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
        case "ArrowRight":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(1);
                document.getElementById(`azimuth_indicator_1`).style["fill-opacity"] = 0.7;
            }
            break;
        case "ArrowLeft":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(3);
                document.getElementById(`azimuth_indicator_3`).style["fill-opacity"] = 0.7;
            }
            break;
        case "ArrowUp":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(0);
                document.getElementById(`azimuth_indicator_0`).style["fill-opacity"] = 0.7;
            }
            break;
        case "ArrowDown":
            if (inspector.selection_mode_enabled) {
                inspector.select_azimuth(2);
                document.getElementById(`azimuth_indicator_2`).style["fill-opacity"] = 0.7;
            }
            break;
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

// Selection mode methods
// This is for placing objects from inventory onto the board

// Information level: for every "true", the user needs to specify the value of
// the corresponding arg key before submitting the command and exiting sel. m.
inspector.selection_mode_enabled = false;
inspector.selection_mode_element = null;
inspector.selection_mode_information_level = {"square" : false, "azimuth" : false};
inspector.selection = {"square" : "NOT_SELECTED", "azimuth" : "NOT_SELECTED"};
inspector.selection_submission = null;

inspector.selection_mode_squares = null;

inspector.selection_keywords = [
            "element",  // base or stone
            "faction", // GM, A, B
            "stone_type",    // [stones only]
            "x",
            "y",
            "a"        // [orientable stones only]
        ];

// inspector methods for inputting elements

inspector.place_shadow_on_cursor = function(e) {
    if (inspector.selection_mode_element["element"] == "base") {
        let el = document.getElementById(`base_${inspector.selection_mode_element["faction"]}_input_icon_shadow`);
        el.style.transform = `translate(${e.clientX - 50}px, ${e.clientY - 50}px)`;
    } else if (inspector.selection_mode_element["element"] == "stone") {
        let el = document.getElementById(`${inspector.selection_mode_element["faction"]}_${inspector.selection_mode_element["stone_type"]}_input_icon_shadow`);
        el.style.transform = `translate(${e.clientX - 50}px, ${e.clientY - 50}px)`;
    }
}

inspector.start_input_mode = function(cur_selection_mode_squares = null) {
    if (inspector.selection_mode_element["element"] == "base") {
        document.getElementById(`base_${inspector.selection_mode_element["faction"]}_input_icon_shadow`).classList.toggle("active");
    } else if (inspector.selection_mode_element["element"] == "stone") {
        document.getElementById(`${inspector.selection_mode_element["faction"]}_${inspector.selection_mode_element["stone_type"]}_input_icon_shadow`).classList.toggle("active");
    }
    document.addEventListener("mousemove", inspector.place_shadow_on_cursor);

    inspector.selection_mode_enabled = true;

    inspector.selection_mode_information_level["square"] = true;
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.selection_mode_information_level["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = "NOT_SELECTED";

    // Show selection highlights
    inspector.set_square_highlight(null);
    document.getElementById("selection_mode_highlights").style.visibility = "visible";

    // Prepare selection mode options
    let azimuth_options = null;
    if (inspector.selection_mode_element["element"] == "stone") {
        if (static_stone_data[inspector.selection_mode_element["stone_type"]]["orientable"]) {
            azimuth_options = [0, 1, 2, 3];
        }
    }
    if (cur_selection_mode_squares == null) {
        inspector.selection_mode_squares = [];
        for (x = 1; x < x_dim - 1; x++) {
            for (y = 1; y < y_dim - 1; y++) {
                inspector.selection_mode_squares.push({"x" : x, "y" : y, "a" : azimuth_options});
            }
        }
    } else {
        inspector.selection_mode_squares = cur_selection_mode_squares;
    }

    if (inspector.selection_mode_squares.length == 1) {
        // The square is chosen automatically
        inspector.select_square(inspector.selection_mode_squares[0]["x"], inspector.selection_mode_squares[0]["y"]);
    }

    // Remove command buttons, create abort button
    document.getElementById("base_inspector_buttons_svg").style.display = "none";
    document.getElementById("stone_inspector_buttons_svg").style.display = "none";
    document.getElementById("selection_mode_abort_svg").style.display = "block";

    render_board();

}

inspector.select_input_element = function(element, allegiance, stone_type) {
    // if input mode is off, select the clicked element and turn on input mode
    if (inspector.selection_mode_enabled == false) {
        inspector.selection_mode_element = {"element" : element, "faction" : allegiance, "stone_type" : stone_type};
        inspector.start_input_mode();
    } else {
        inspector.turn_off_selection_mode();
    }
}

inspector.turn_off_selection_mode = function() {

    let x = inspector.selection_mode_squares[inspector.selection["square"]]["x"];
    let y = inspector.selection_mode_squares[inspector.selection["square"]]["y"];

    // Remove cursor shadow
    document.querySelectorAll('.input_icon_shadow').forEach(el => {
        el.classList.remove('active');
    });
    inspector.selection_mode_element = null;
    document.removeEventListener("mousemove", inspector.place_shadow_on_cursor);

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
    document.getElementById("selection_mode_abort_svg").style.display = "none";

    // Replace selectors with trackers
    //document.getElementById("choice_selector").style.display = "none";
    //document.getElementById("swap_effect_selector").style.display = "none";
    //document.getElementById("faction_inspector").style.display = "block";
    //document.getElementById("square_inspector").style.display = "block";


    inspector.selection_mode_enabled = false;

    render_board();

    // Clear cache
    inspector.selection_mode_squares = null;
    inspector.selection_submission = null;
    inspector.selection_mode_element = null;

    inspector.board_square_click(x, y);

}

inspector.submit_if_complete = function() {
    if (inspector.selection_mode_enabled && inspector.selection_mode_information_level["square"] == false && inspector.selection_mode_information_level["azimuth"] == false) {
        inspector.submit_selection();
    }
}

inspector.select_square = function(x, y) {
    // We find the correct element of squares
    for (let i = 0; i < inspector.selection_mode_squares.length; i++) {
        if (inspector.selection_mode_squares[i]["x"] == x && inspector.selection_mode_squares[i]["y"] == y) {
            render_board();
            let cur_square = inspector.selection_mode_squares[i];
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

            //inspector.submit_if_complete();
            render_board();

            // Now, based on what we know and what is yet to be inputted, we show and hide the azimuth dialogue
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
        if (inspector.selection_mode_enabled == false) {
            break;
        }
    }
}

inspector.unselect_square = function() {
    inspector.selection["square"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["square"] = true;
    inspector.set_square_highlight(null);
    let selection_mode_dummies = document.getElementsByClassName("selection_mode_dummy");
    for (i = 0; i < selection_mode_dummies.length; i++) {
        selection_mode_dummies[i].style.display = "none";
    }
    inspector.selection["azimuth"] = "NOT_SELECTED";
    inspector.selection_mode_information_level["azimuth"] = true;
    inspector.submit_if_complete();
}

inspector.select_azimuth = function(target_azimuth) {
    if (inspector.selection_mode_squares[inspector.selection["square"]]["a"] == null) {
        target_azimuth = null;
    }
    if (target_azimuth == null || inspector.selection_mode_squares[inspector.selection["square"]]["a"].includes(target_azimuth)) {
        inspector.selection["azimuth"] = target_azimuth;
        inspector.selection_mode_information_level["azimuth"] = false;
        inspector.submit_if_complete();
        render_board();
    }
}

// Methods for editing element trackers

inspector.add_element = function(new_element) {
    // Firstly, if board_static is a wall, we force it to be empty
    if (board_static[new_element["x"]][new_element["y"]] == "X") {
        board_static[new_element["x"]][new_element["y"]] = " ";
    }

    // Then, if there already is an element of the same type on this square, we remove it, too

    let was_element_replaced = false;
    switch (new_element["element"]) {
        case "base":
            for (i = 0; i < bases.length; i++) {
                if (bases[i]["x"] == new_element["x"] && bases[i]["y"] == new_element["y"]) {
                    bases[i]["faction"] = new_element["faction"];
                    was_element_replaced = true;
                }
            }
            break;
        case "stone":
            for (i = 0; i < stones.length; i++) {
                if (stones[i]["x"] == new_element["x"] && stones[i]["y"] == new_element["y"]) {
                    stones[i]["faction"] = new_element["faction"];
                    stones[i]["stone_type"] = new_element["stone_type"];
                    stones[i]["a"] = new_element["a"];
                    was_element_replaced = true;
                }
            }
            break;
    }

    // Then, we add the relevant element to the tracker
    if (was_element_replaced == false) {
        switch (new_element["element"]) {
            case "base":
                bases.push({"faction" : new_element["faction"], "x" : new_element["x"], "y" : new_element["y"]});
                break;
            case "stone":
                stones.push({"faction" : new_element["faction"], "stone_type" : new_element["stone_type"], "x" : new_element["x"], "y" : new_element["y"], "a" : new_element["a"]});
                break;
        }
    }
    inspector.update_submission_form();
}

inspector.update_submission_form = function() {
    // This function updates the hidden form so that it accurately represents the static board, the bases, and the stones as they are.

    // Update global data
    document.getElementById("h_t_dim").value = t_dim;
    document.getElementById("h_x_dim").value = x_dim;
    document.getElementById("h_y_dim").value = y_dim;
    document.getElementById("h_number_of_bases").value = bases.length;
    document.getElementById("h_number_of_stones").value = stones.length;

    // For the remaining fieldsets, we purge the children nodes and rebuild them
    fs_squares_data = document.getElementById("squares_data");
    fs_bases_data = document.getElementById("bases_data");
    fs_stones_data = document.getElementById("stones_data");

    while (fs_squares_data.firstChild) {
        fs_squares_data.removeChild(fs_squares_data.lastChild);
    }
    for (y = 0; y < y_dim; y++) {
        for (x = 0; x < x_dim; x++) {
            const new_square_input = document.createElement("input");
            new_square_input.type = "hidden";
            new_square_input.name = `square_${x}_${y}`;
            new_square_input.id = `square_${x}_${y}`;
            new_square_input.value = board_static[x][y];
            fs_squares_data.appendChild(new_square_input);
        }
    }

    while (fs_bases_data.firstChild) {
        fs_bases_data.removeChild(fs_bases_data.lastChild);
    }
    for (base_i = 0; base_i < bases.length; base_i++) {
        for (base_kw_i = 0; base_kw_i < bases_keywords.length; base_kw_i++) {
            const new_base_input = document.createElement("input");
            new_base_input.type = "hidden";
            new_base_input.name = `base_${base_i}_${bases_keywords[base_kw_i]}`;
            new_base_input.id = `base_${base_i}_${bases_keywords[base_kw_i]}`;
            new_base_input.value = bases[base_i][bases_keywords[base_kw_i]];
            fs_bases_data.appendChild(new_base_input);
        }
    }

    while (fs_stones_data.firstChild) {
        fs_stones_data.removeChild(fs_stones_data.lastChild);
    }
    for (stone_i = 0; stone_i < stones.length; stone_i++) {
        for (stone_kw_i = 0; stone_kw_i < stones_keywords.length; stone_kw_i++) {
            const new_stone_input = document.createElement("input");
            new_stone_input.type = "hidden";
            new_stone_input.name = `stone_${stone_i}_${stones_keywords[stone_kw_i]}`;
            new_stone_input.id = `stone_${stone_i}_${stones_keywords[stone_kw_i]}`;
            new_stone_input.value = stones[stone_i][stones_keywords[stone_kw_i]];
            fs_stones_data.appendChild(new_stone_input);
        }
    }


}

inspector.submit_selection = function() {
    // edits the board by adding element as specified
    //inspector.selection_submission["target_x"] = inspector.selection_mode_squares[inspector.selection["square"]]["x"];
    //inspector.selection_submission["target_y"] = inspector.selection_mode_squares[inspector.selection["square"]]["y"];
    //inspector.selection_submission["target_a"] = inspector.selection["azimuth"];

    let x = inspector.selection_mode_squares[inspector.selection["square"]]["x"];
    let y = inspector.selection_mode_squares[inspector.selection["square"]]["y"];
    let a = inspector.selection["azimuth"];

    inspector.add_element({"element" : inspector.selection_mode_element["element"], "faction" : inspector.selection_mode_element["faction"], "stone_type" : inspector.selection_mode_element["stone_type"], "x" : x, "y" : y, "a" : a});

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

// Element commands

inspector.execute_command = function(element, element_ID, command) {
    // Prompts user further to specify the arguments for the command
    let x = null;
    let y = null;

    switch(element) {
        case "base":
            x = bases[element_ID]["x"];
            y = bases[element_ID]["y"];
            switch(command) {
                case "remove":
                    bases.splice(element_ID, 1);
                    inspector.update_submission_form();
                    render_board();
                    inspector.board_square_click(x, y);
                    break;
            }
            break;

        case "stone":
            x = stones[element_ID]["x"];
            y = stones[element_ID]["y"];
            switch(command) {
                case "remove":
                    stones.splice(element_ID, 1);
                    inspector.update_submission_form();
                    render_board();
                    inspector.board_square_click(x, y);
                    break;
                case "rotate":
                    let faction = stones[element_ID]["faction"];
                    let stone_type = stones[element_ID]["stone_type"];
                    /*stones.splice(element_ID, 1);
                    inspector.update_submission_form();
                    render_board();*/
                    inspector.selection_mode_element = {"element" : "stone", "faction" : faction, "stone_type" : stone_type};
                    inspector.start_input_mode([{"x" : x, "y" : y, "a" : [0, 1, 2, 3]}]);
                    break;
            }
            break;
    }

}

inspector.get_available_commands = function(element, element_ID) {
    // Depends purely on static data
    switch(element) {
        case "base":
            return [["remove", "Remove base"]];
            break;
        case "stone":
            stone_faction = stones[element_ID]["faction"];
            stone_type = stones[element_ID]["stone_type"];
            let available_commands = [["remove", "Remove stone"]];
            if (static_stone_data[stone_type]["orientable"]) {
                available_commands.push(["rotate", "Change azimuth"]);
            }
            return available_commands;
            break;
    }
}

inspector.display_element_commands = function(element, element_ID) {
    // If select square has an element, we display the relevant buttons

    switch(element) {
        case "base":
            document.getElementById("base_inspector_buttons_svg").style.display = "block";
            document.getElementById("stone_inspector_buttons_svg").style.display = "none";
            document.getElementById("base_info_table").style.display = "inline";
            document.getElementById("stone_info_table").style.display = "none";
            break;
        case "stone":
            document.getElementById("base_inspector_buttons_svg").style.display = "none";
            document.getElementById("stone_inspector_buttons_svg").style.display = "block";
            document.getElementById("base_info_table").style.display = "none";
            document.getElementById("stone_info_table").style.display = "inline";
            break;
    }
    let element_inspector_buttons_svg = document.getElementById(`${element}_inspector_buttons_svg`);
    if (element_ID == null) {
        while (element_inspector_buttons_svg.firstChild) {
            element_inspector_buttons_svg.removeChild(element_inspector_buttons_svg.lastChild);
        }
    } else {
        // First, we delete everything
        inspector.display_element_commands(element, null);

        // Now, we find the list of commands
        let list_of_commands = inspector.get_available_commands(element, element_ID);

        // We draw every button
        offset_x = 0;
        offset_y = 0;
        for (let i = 0; i < list_of_commands.length; i++) {
            let new_button = make_SVG_element("rect", {
                class : "stone_command_panel_button",
                id : `${element}_command_${list_of_commands[i][0]}`,
                onclick : `inspector.execute_command(\'${element}\', ${element_ID}, \"${list_of_commands[i][0]}\")`,
                x : offset_x,
                y : 0,
                width : stone_command_btn_width,
                height : stone_command_btn_height
            });
            let new_button_label = make_SVG_element("text", {
                class : "button_label",
                id : `${element}_command_${list_of_commands[i][0]}_label`,
                x : offset_x + stone_command_btn_width / 2,
                y : stone_command_btn_height / 2,
                "text-anchor" : "middle"
            });
            new_button_label.textContent = list_of_commands[i][1];
            element_inspector_buttons_svg.appendChild(new_button);
            element_inspector_buttons_svg.appendChild(new_button_label);
            offset_x += stone_command_btn_width + 10;

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

    if (stone_ID != null) {
        inspector.inspector_elements["stone"]["title"].innerHTML = `A ${stone_highlight(stone_ID)} selected`;
        inspector.display_value_list("stone", "allegiance", [stones[stone_ID]["faction"]]);
        inspector.display_value_list("stone", "stone_type", [stones[stone_ID]["stone_type"].toUpperCase()]);

        inspector.display_element_commands("stone", stone_ID);

    } else if (base_ID != null) {
        inspector.inspector_elements["stone"]["title"].innerHTML = `A ${base_highlight(base_ID)} selected`;
        inspector.display_value_list("base", "allegiance", [bases[base_ID]["faction"]]);

        inspector.display_element_commands("base", base_ID);

    } else {
        inspector.inspector_elements["stone"]["title"].innerHTML = "No element selected";
        inspector.display_value_list("stone", "allegiance", []);
        inspector.display_value_list("stone", "stone_type", []);
        inspector.display_element_commands("stone", null);
    }

    return stone_ID;
}

inspector.hide_stone_info = function() {
    inspector.inspector_elements["stone"]["title"].innerHTML = "No element selected";
    //inspector.display_value_list("stone", "allegiance", []);
    //inspector.display_value_list("stone", "stone_type", []);
    document.getElementById("base_inspector_buttons_svg").style.display = "none";
    document.getElementById("stone_inspector_buttons_svg").style.display = "none";
    document.getElementById("base_info_table").style.display = "none";
    document.getElementById("stone_info_table").style.display = "none";
}

// ------------------------- Board dimensions methods -------------------------

inspector.get_added_board_symbol = function(new_width, new_height, x, y) {
    if (x == 0 || x == new_width - 1 || y == 0 || y == new_height - 1) {
        return "X";
    } else {
        return " ";
    }
}

inspector.update_board_dimensions = function() {
    inspector.unselect_all(); // safety

    new_t_dim = Number(document.getElementById("board_dimensions_t_input").value);
    new_x_dim = Number(document.getElementById("board_dimensions_x_input").value);
    new_y_dim = Number(document.getElementById("board_dimensions_y_input").value);

    t_dim = new_t_dim;
    // if the width decreased, we delete rightmost columns except for the border column. Analogously for bottom rows on decreased height
    if (new_x_dim < x_dim) {
        board_static.splice(new_x_dim - 1, x_dim - new_x_dim);
    } else {
        for (i_x = 0; i_x < new_x_dim - x_dim; i_x++) {
            board_static.splice(x_dim - 1, 0, []);
            for (i_x_y = 0; i_x_y < y_dim; i_x_y++) {
                board_static[x_dim - 1].push(inspector.get_added_board_symbol(new_x_dim, y_dim, x_dim - 2, i_x_y));
            }
        }
    }

    if (new_y_dim < y_dim) {
        for (i_y_x = 0; i_y_x < new_x_dim; i_y_x++) {
            board_static[i_y_x].splice(new_y_dim - 1, y_dim - new_y_dim);
        }
    } else {
        for (i_y_x = 0; i_y_x < new_x_dim; i_y_x++) {
            for (i_y = 0; i_y < new_y_dim - y_dim; i_y++) {
                board_static[i_y_x].splice(y_dim - 1, 0, inspector.get_added_board_symbol(new_x_dim, new_y_dim, i_y_x, y_dim - 2));
            }
        }
    }

    x_dim = new_x_dim;
    y_dim = new_y_dim;

    // We delete all the sussy elements
    new_bases = []
    new_stones = []
    for (i_base = 0; i_base < bases.length; i_base++) {
        if (bases[i_base]["x"] < x_dim - 1 && bases[i_base]["y"] < y_dim - 1) {
            new_bases.push(bases[i_base]);
        }
    }
    for (i_stone = 0; i_stone < stones.length; i_stone++) {
        if (stones[i_stone]["x"] < x_dim - 1 && stones[i_stone]["y"] < y_dim - 1) {
            new_stones.push(stones[i_stone]);
        }
    }
    stones = new_stones;
    bases = new_bases;

    // Update selection mode highlighters
    selection_mode_highlights = document.getElementById("selection_mode_highlights");
    while (selection_mode_highlights.firstChild) {
        selection_mode_highlights.removeChild(selection_mode_highlights.firstChild);
    }
    for (cur_x = 0; cur_x < x_dim; cur_x++) {
        for (cur_y = 0; cur_y < y_dim; cur_y++) {
            new_highlight = make_SVG_element("rect", {
                "width" : 100,
                "height" : 100,
                "x" : 100 * cur_x,
                "y" : 100 * cur_y,
                "class" : "selection_mode_highlight",
                "id" : `selection_mode_highlight_${cur_x}_${cur_y}`
            });
            selection_mode_highlights.appendChild(new_highlight);
        }
    }

    // Reset camera
    cameraman.put_down_tripod();
    cameraman.reset_camera();

    inspector.update_submission_form();
    render_board();



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

    // Update visibility of square type changing buttons
    // Note that the bordering squares don't have any buttons, since they are fixed as walls
    if (x == 0 || x == x_dim - 1 || y == 0 || y == y_dim - 1) {
        for (i = 0; i < board_square_types.length; i++) {
            document.getElementById(`change_square_to_${board_square_info[board_square_types[i]]}`).style.display = "none";
        }
    } else {
        for (i = 0; i < board_square_types.length; i++) {
            if (board_static[x][y] == board_square_types[i]) {
                document.getElementById(`change_square_to_${board_square_info[board_square_types[i]]}`).style.display = "none";
            } else {
                document.getElementById(`change_square_to_${board_square_info[board_square_types[i]]}`).style.display = "block";
            }
        }
    }
}


inspector.hide_square_info = function() {

    // Highligh square, reset stone highlight
    inspector.set_square_highlight(null);
    document.getElementById("square_inspector_title").innerHTML = `No square selected`;
    for (i = 0; i < board_square_types.length; i++) {
        document.getElementById(`change_square_to_${board_square_info[board_square_types[i]]}`).style.display = "none";
    }
}

inspector.change_square_type = function(new_type_symbol) {
    if (inspector.highlighted_square == null) {
        return null;
    }
    // If changing to wall, we delete every element on this square
    let x = inspector.highlighted_square[0];
    let y = inspector.highlighted_square[1];
    if (new_type_symbol == "X") {
        for (base_i = 0; base_i < bases.length; base_i++) {
            if (bases[base_i]["x"] == x && bases[base_i]["y"] == y) {
                bases.splice(base_i, 1);
                break;
            }
        }
        for (stone_i = 0; stone_i < stones.length; stone_i++) {
            if (stones[stone_i]["x"] == x && stones[stone_i]["y"] == y) {
                stones.splice(stone_i, 1);
                break;
            }
        }
    }

    board_static[x][y] = new_type_symbol;
    inspector.update_submission_form();
    render_board();
    inspector.board_square_click(x, y);
}

inspector.board_square_click = function(x, y){
    if (inspector.selection_mode_enabled) {
        /*for (let i = 0; i < inspector.selection_mode_squares.length; i++) {
            if (inspector.selection_mode_squares[i]["x"] == x && inspector.selection_mode_squares[i]["y"] == y) {
                inspector.select_square(x, y);
            }
        }*/
        inspector.select_square(x, y);
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
cameraman.update_board_dimension();
cameraman.reset_camera();

// Set up commander if game in progress

// Set up inspector
inspector.hide_stone_info();
inspector.hide_square_info();

reset_board_dimensions_form();
