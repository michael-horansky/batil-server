
const client_access_context = "BOARD_EDITOR";



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
