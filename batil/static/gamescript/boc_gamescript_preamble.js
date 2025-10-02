// ----------------------------------------------------------------------------
// --------------------------- Rendering constants ----------------------------
// ----------------------------------------------------------------------------

const stone_command_btn_width = 100;
const stone_command_btn_height = 83;

const choice_option_btn_width = 120;
const choice_option_btn_height = 83;

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

function round_from_turn(turn_index) {
    if (turn_index == 0) {
        return [0, -1];
    }
    let current_round_number = Math.floor((turn_index - 1) / t_dim);
    let current_timeslice    = (turn_index - 1) % t_dim;
    return [current_round_number, current_timeslice];
}

function is_flag_at_pos(flag_ID, t, x, y) {
    if (reverse_causality_flag_properties[flag_ID] == undefined) {
        alert(`[Flag ID: ${flag_ID}] properties requested at (${t},${x},${y}) but flag does not exist.`);
    }
    return (reverse_causality_flag_properties[flag_ID]["t"] == t && reverse_causality_flag_properties[flag_ID]["x"] == x && reverse_causality_flag_properties[flag_ID]["y"] == y);
}

function find_stone_at_pos(x, y) {
    for (let faction_i = 0; faction_i < all_factions.length; faction_i++) {
        for (let stone_i = 0; stone_i < faction_armies[all_factions[faction_i]].length; stone_i++) {
            if (stone_trajectories[selected_round][visible_timeslice]["canon"][faction_armies[all_factions[faction_i]][stone_i]] != null) {
                if (arrays_equal(stone_trajectories[selected_round][visible_timeslice]["canon"][faction_armies[all_factions[faction_i]][stone_i]].slice(0,2), [x, y])) {
                    return faction_armies[all_factions[faction_i]][stone_i];
                }
            }
        }
    }
    return null;
}

function bound(val, lower_bound, upper_bound) {
    return Math.max(lower_bound, Math.min(val, upper_bound));
}

function cubic_bezier(t, params) {
    // t = 0 => 0
    // t = 1 => 1
    return (t*(t*(t+(1-t)*params[1])+(1-t)*(t*params[1]+(1-t)*params[0]))+(1-t)*(t*(t*params[1]+(1-t)*params[0])+(1-t)*(t*params[0])));
}
function cubic_bezier_boomerang(t, params) {
    // t = 0 => 0
    // t = 1 => 0
    return (1-t)*((1-t)*(t*params[0])+t*((1-t)*params[0]+t*params[1]))+t*((1-t)*((1-t)*params[0]+t*params[1])+t*((1-t)*params[1]));
}

function arrays_equal(arr1, arr2) {
    return arr1.every((value, index) => value == arr2[index]);
}

// Vector algebra
function vec_add(vec1, vec2){
    return vec1.map((e,i) => e + vec2[i]);
}

function vec_sub(vec1, vec2){
    return vec1.map((e,i) => e - vec2[i]);
}

function vec_scale(vec, coef){
    return vec.map((e,i) => e * coef);
}

function vec_round(vec) {
    return vec.map((e,i) => Math.round(e));
}

// Matrix algebra
function mat_add(mat1,mat2){
    return mat1.map((row_vec,row_i) => (row_vec.map((e, col_i) => ([e,mat2[row_i][col_i]].includes(null) ? null : e + mat2[row_i][col_i]  ))));
}

function mat_sub(mat1,mat2){
    return mat1.map((row_vec,row_i) => (row_vec.map((e, col_i) => ([e,mat2[row_i][col_i]].includes(null) ? null : e - mat2[row_i][col_i]))));
}

function mat_scale(mat, coef){
    return mat.map((row_vec,row_i) => (row_vec.map((e, col_i) => (e == null ? null : e * coef))));
}

function mat_round(mat) {
    return mat.map((row_vec,row_i) => (row_vec.map((e, col_i) => (e == null ? null : Math.round(e)))));
}

function animated_scalar_transformation(val_start, val_end, total_frames, frame_key, method="traverse") {
    // val_start, val_end are numbers which denote the parameter to be animated
    // total_frames is the number of frames, frame_key is the current frame id.
    switch (method) {
        case "traverse":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.1, 1]);
        case "boomerang":
            return val_start + (val_end - val_start) * cubic_bezier_boomerang(frame_key / total_frames, [0.2, 2.1]);
        case "linear":
            return val_start + (val_end - val_start) * frame_key / total_frames;
    }
    /*if (method == "traverse") {
        return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.1, 1]);
    }
    if (method == "boomerang") {
        return val_start + (val_end - val_start) * cubic_bezier_boomerang(frame_key / total_frames, [0.2, 2.1]);
    }*/

}

function animated_vector_transformation(vec_start, vec_end, total_frames, frame_key) {
    // vec_start, vec_end are vectors which denote the parameter to be animated
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return vec_add(vec_start, vec_scale(vec_sub(vec_end, vec_start), cubic_bezier(frame_key / total_frames, [0.1, 1])));
}

function animated_matrix_transformation(mat_start, mat_end, total_frames, frame_key) {
    // mat_start, mat_end are matrices encoding the parameters to be animated.
    // total_frames is the number of frames, frame_key is the current frame id.

    // linear method: replace with easening!
    return mat_add(mat_start, mat_scale(mat_sub(mat_end, mat_start), cubic_bezier(frame_key / total_frames, [0.1, 1])));
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

// ----------------------------- Stone highlight ------------------------------

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


function stone_highlight(stone_ID) {
    return `<span class=\"stone_highlight\" onmouseenter=\"set_stone_highlight(${stone_ID})\" onmouseleave=\"set_stone_highlight(null)\" onclick=\"cameraman.track_stone(${stone_ID})\">${stone_properties[stone_ID]["stone_type"].toUpperCase()} [P. ${stone_properties[stone_ID]["allegiance"]}]</span>`;
}

function square_highlight(t, x, y) {
    return `<span class=\"square_highlight\" onclick=\"go_to_square(${t},${x},${y})\">(${t},${x},${y})</tspan>`;
}

