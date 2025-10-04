// --------------------------- Rendering constants ----------------------------

const stone_command_btn_width = 140;
const stone_command_btn_height = 83;

const choice_option_btn_width = 120;
const choice_option_btn_height = 83;

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


// ----------------------------------------------------------------------------
// -------------------------------- Inspector ---------------------------------
// ----------------------------------------------------------------------------

const inspector = new Object();
inspector.selection_mode_enabled = false;
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

