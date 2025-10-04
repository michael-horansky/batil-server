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

