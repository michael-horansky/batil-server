

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
            break;
        case "boomerang":
            return val_start + (val_end - val_start) * cubic_bezier_boomerang(frame_key / total_frames, [0.2, 2.1]);
            break;
        case "linear":
            return val_start + (val_end - val_start) * frame_key / total_frames;
            break;
        case "cloud_layer_0":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.0, 2.0]);
            break;
        case "cloud_layer_1":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.0, 1.75]);
            break;
        case "cloud_layer_2":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.0, 1.5]);
            break;
        case "cloud_layer_3":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.0, 1.2]);
            break;
        case "cloud_opacity":
            return val_start + (val_end - val_start) * cubic_bezier(frame_key / total_frames, [0.1, 0.0]);
            break;

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

// String logic

function append_to_list_of_strings(list_of_strings, suffix) {
    let res = [];
    list_of_strings.forEach(function(string_element, index) {
        res.push(`${string_element}${suffix}`);
    });
    return res;
}

// Standard converters

function base_class_for_base(allegiance) {
    return `base_${allegiance}`;
}

