
const client_access_context = "BOARD_EDITOR_READ_ONLY";


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
