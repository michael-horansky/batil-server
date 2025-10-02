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
// Tracking properties
cameraman.tracking_stone = null;
cameraman.is_tracking_stone_onscreen = false;
cameraman.used_by_an_animation = false;

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

cameraman.apply_tracking = function(tracking_stone_state = null) {
    // tracking_stone_state is used mid-animations
    if (!(inspector.selection_mode_enabled)) {
        if (tracking_stone_state == null) {
            if (cameraman.tracking_stone != null) {
                if (stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone] != null) {
                    cameraman.cx = (stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][0] + 0.5) / x_dim;
                    cameraman.cy = (stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][1] + 0.5) / y_dim;
                    cameraman.is_tracking_stone_onscreen = true;
                    if (visible_process == "canon") {
                        inspector.display_square_info(stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][0], stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][1]);
                        inspector.display_stone_info(stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][0], stone_trajectories[visible_round][visible_timeslice][visible_process][cameraman.tracking_stone][1]);
                    }
                } else {
                    cameraman.is_tracking_stone_onscreen = false;
                    if (inspector.highlighted_square != null) {
                        inspector.display_highlighted_info();
                    }
                }
            } else {
                cameraman.is_tracking_stone_onscreen = false;
                if (inspector.highlighted_square != null) {
                    inspector.display_highlighted_info();
                }
            }
        } else {
            cameraman.cx = (tracking_stone_state[0] + 0.5) / x_dim;
            cameraman.cy = (tracking_stone_state[1] + 0.5) / y_dim;
            cameraman.is_tracking_stone_onscreen = true;
        }
    }
    cameraman.apply_camera();
}

// -------------------------- Camera stone tracking ---------------------------
// Tracking has the following effects:
//   1. A panel shows up at the bottom of Stone inspector, allowing the player
//      to view the endpoints of the stone's trajectory and turn off tracking
//   2. The camera follows the stone, affixing it to the centre of the window
//   3. Auto-selecting the stone's trajectory points for the Square inspector
// Tracking can be turned on in the following ways:
//   1. Clicking on a stone highlight
//   2. Clicking on the button "Track this stone" in the Stone inspector panel
//   3. Double-clicking an occupied square (NOPE)
// And it can be turned off in the following ways:
//   1. Clicking the "Turn off tracking" button in the tracking inspector
//   2. Resetting the camera, e.g. by pressing the "R" key
//   3. Turning on a different camera mode, e.g. "go to square"
cameraman.track_stone = function(stone_ID) {
    if (!inspector.selection_mode_enabled) {
        // If null, tracking is turned off

        // We refuse to track a stone not placed on the board in this round
        if (stone_ID != null && stone_endpoints[selected_round][stone_ID] == undefined) {
            alert("Stone not placed on board");
        } else {
            cameraman.tracking_stone = stone_ID;
            document.getElementById("stone_tracking_label").innerHTML = (stone_ID == null ? "Stone tracking off" : `Tracking a<br/>${stone_highlight(stone_ID)}.`);
            set_stone_highlight(null); // We turn off the highlight
            if (stone_ID == null) {
                // Hide tracking buttons
                document.getElementById("tracking_inspector_svg").style.visibility = "hidden"
            } else {
                // Show tracking buttons
                document.getElementById("tracking_inspector_svg").style.visibility = "visible"
            }
            cameraman.apply_tracking();
        }
    }
}


cameraman.reset_camera = function() {
    cameraman.fov_coef = cameraman.default_fov_coef;
    cameraman.cx = 0.5;
    cameraman.cy = 0.5;
    cameraman.track_stone(null);
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
    if (!(cameraman.tracking_stone != null && cameraman.is_tracking_stone_onscreen)) {
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
