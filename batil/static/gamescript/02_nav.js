// ----------------------------------------------------------------------------
// ---------------------- Graphical attribute management ----------------------
// ----------------------------------------------------------------------------

function update_game_log_nav(timeslice, round) {
    document.getElementById("game_log_nav_timeslice_value").textContent = `${timeslice} / ${t_dim - 1}`;
    document.getElementById("game_log_nav_round_value").textContent = `${round} / ${active_round}`;
    // If this is the active turn, we highlight the background of the game log section.
    if (timeslice == active_timeslice && round == active_round) {
        document.getElementById("game_log").classList.add("active");
    } else {
        document.getElementById("game_log").classList.remove("active");
    }
}

function select_timeslice(new_timeslice) {
    selected_timeslice = new_timeslice;
    //document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}, selected round ${selected_round}`;
    update_game_log_nav(selected_timeslice, selected_round);
}

function select_round(new_round_n, new_timeslice = null) {
    selected_round = new_round_n;
    if (new_timeslice != null) {
        selected_timeslice = new_timeslice;
    }
    //document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}, selected round ${selected_round}`;
    update_game_log_nav(selected_timeslice, selected_round);
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

