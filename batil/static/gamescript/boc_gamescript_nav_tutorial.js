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

function update_tutorial_comment_form(timeslice, round) {
    let selected_turn_index = selected_round * t_dim + selected_timeslice + 1;

    document.getElementById("tcf_turn_index").value = selected_turn_index;
    if (tutorial_populated_turns.includes(selected_turn_index)) {
        document.getElementById("tcf_textarea").value = tutorial_comments[selected_turn_index];
    } else {
        document.getElementById("tcf_textarea").value = "";
    }
    document.getElementById("tcf_textarea").placeholder = `Tutorial comment for turn ${selected_turn_index} here...`;


}

function select_timeslice(new_timeslice) {
    selected_timeslice = new_timeslice;
    update_game_log_nav(selected_timeslice, selected_round);
    // We store the turn index in the tutorial comment form
    update_tutorial_comment_form(selected_timeslice, selected_round);
}

function select_round(new_round_n, new_timeslice = null) {
    selected_round = new_round_n;
    if (new_timeslice != null) {
        select_timeslice(new_timeslice);
    }
    //document.getElementById("navigation_label").innerText = `Selected timeslice ${selected_timeslice}, selected round ${selected_round}`;
    update_game_log_nav(selected_timeslice, selected_round);
    update_tutorial_comment_form(selected_timeslice, selected_round);
}
