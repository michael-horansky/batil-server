# -----------------------------------------------------------------------------
# ------------------------ class TutorialHTMLRenderer -------------------------
# -----------------------------------------------------------------------------
# This renderer creates a longstring in a HTML format, with interactive
# features managed by JavaScript.

import numpy as np

import json
import re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)


from batil.engine.rendering.class_Renderer import Renderer
from batil.engine.rendering.class_Abstract_Output import Abstract_Output


class TutorialHTMLRenderer(Renderer):

    def __init__(self, render_object, tutorial_id, tutorial_comments, client_role, editor_role = None):
        super().__init__(render_object)
        self.tutorial_id = tutorial_id
        self.tutorial_comments = tutorial_comments
        self.client_role = client_role
        self.editor_role = editor_role # If client_role is "editor", then this is either None, "A", or "B"
        self.structured_output = []

        # ------------------------ Rendering constants ------------------------

        # Document structure

        self.board_square_empty_color = "#E5E5FF"
        self.unused_TJ_clip_circle_radius = 0.45

        # Board structure
        self.board_square_base_side_length = 100

        # Stone types
        self.required_stone_types = []
        for neutral_stone_ID in self.render_object.faction_armies["GM"]:
            if (self.render_object.stone_properties[neutral_stone_ID]["stone_type"] not in self.required_stone_types):
                self.required_stone_types.append(self.render_object.stone_properties[neutral_stone_ID]["stone_type"])
        for faction in self.render_object.factions:
            for faction_stone_ID in self.render_object.faction_armies[faction]:
                if (self.render_object.stone_properties[faction_stone_ID]["stone_type"] not in self.required_stone_types):
                    self.required_stone_types.append(self.render_object.stone_properties[faction_stone_ID]["stone_type"])

    # ------------------- Output file communication methods -------------------

    def open_body(self):
        self.commit_to_output([
                "<body onkeydown=\"parse_keydown_event(event)\" onkeyup=\"parse_keyup_event(event)\">"
            ])

    def close_body(self):
        # We actually leave the <body> tag open for possible scripts to be slapped onto the end
        if self.client_role == "editor":
            #self.commit_to_output(f"  <script src=\"{ url_for('static', filename='boc_tutorial.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/01_preamble.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/02_nav_tutorial.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/03_animation_manager.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/04_cameraman.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/05_events.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/06_commander.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/07_inspector.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/08_animation_setup.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/09_display_setup_tutorial.js') }\"></script>")
        else:
            #self.commit_to_output(f"  <script src=\"{ url_for('static', filename='boc_tutorial_read_only.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/01_preamble.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/02_nav_tutorial_read_only.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/03_animation_manager.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/04_cameraman.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/05_events.js') }\"></script>")
            # we omit the commander script
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/07_inspector.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/08_animation_setup.js') }\"></script>")
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='gamescript/09_display_setup_tutorial_read_only.js') }\"></script>")

    def commit_to_output(self, html_object):
        self.structured_output.append(html_object)

    # ------------------------ Label mangling methods -------------------------

    def encode_board_square_id(self, x, y):
        return(f"board_square_{x}_{y}")

    def encode_board_square_class(self, x, y):
        # returns a tuple (class_name, z_index)
        if self.render_object.board_static[x][y] == " ":
            return("board_square_empty", 0)
        elif self.render_object.board_static[x][y] == "X":
            return("board_square_wall", 3)
        else:
            return("board_square_unknown", 0)

    def encode_used_time_jump_marker_id(self, x, y):
        return(f"used_time_jump_marker_{x}_{y}")

    def encode_unused_time_jump_marker_id(self, x, y):
        return(f"unused_time_jump_marker_{x}_{y}")

    def encode_stone_ID(self, stone_ID):
        return(f"stone_{stone_ID}")

    def encode_base_ID(self, base_ID):
        return(f"base_{base_ID}")

    # ---------------------------- Data depositing ----------------------------

    def deposit_datum(self, name, value, volatile = False):
        if volatile:
            declaration_str = "let"
        else:
            declaration_str = "const"

        if value is None:
            self.commit_to_output(f"  {declaration_str} {name} = null;")
        elif isinstance(value, bool):
            if value:
                self.commit_to_output(f"  {declaration_str} {name} = true;")
            else:
                self.commit_to_output(f"  {declaration_str} {name} = false;")
        elif isinstance(value, str):
            self.commit_to_output(f"  {declaration_str} {name} = {json.dumps(value)};")
        else:
            self.commit_to_output(f"  {declaration_str} {name} = {value};")

    def deposit_list(self, name, value, volatile = False):
        # If there are no dictionaries in the nest, the output of json.dumps is
        # immediately interpretable by javascript
        if volatile:
            declaration_str = "let"
        else:
            declaration_str = "const"
        self.commit_to_output(f"  {declaration_str} {name} = {json.dumps(value)};")

    def deposit_object(self, name, value, volatile = False):
        if volatile:
            declaration_str = "let"
        else:
            declaration_str = "const"
        self.commit_to_output(f"  {declaration_str} {name} = {json.dumps(value)};")

    def deposit_contextual_data(self):
        # This method creates a <script> environment which deposits all data
        # which change between games and which are needed by the JavaScript.
        # This means the main script can be global for all the games :)
        self.commit_to_output(f"<script>")
        # ------------------------ General properties -------------------------
        self.deposit_list("board_static", self.render_object.board_static)
        self.deposit_datum("t_dim", self.render_object.t_dim)
        self.deposit_datum("x_dim", self.render_object.x_dim)
        self.deposit_datum("y_dim", self.render_object.y_dim)
        self.deposit_list("factions", self.render_object.factions)
        self.deposit_list("faction_armies", self.render_object.faction_armies)
        self.deposit_object("stone_properties", self.render_object.stone_properties)
        self.deposit_list("bases", self.render_object.bases)

        # Command properties
        self.deposit_datum("did_player_finish_turn", self.render_object.did_player_finish_turn)
        self.deposit_list("stones_to_be_commanded", self.render_object.stones_to_be_commanded)
        self.deposit_object("available_commands", self.render_object.available_commands)

        # ----------------------- Roundwise properties ------------------------
        self.deposit_object("stone_trajectories", self.render_object.stone_trajectories)
        self.deposit_object("stone_endpoints", self.render_object.stone_endpoints)
        self.deposit_object("base_trajectories", self.render_object.base_trajectories)
        self.deposit_list("stone_actions", self.render_object.stone_actions)
        self.deposit_list("board_actions", self.render_object.board_actions)

        #self.deposit_object("reverse_causality_flags", self.render_object.reverse_causality_flags)
        self.deposit_object("reverse_causality_flag_properties", self.render_object.reverse_causality_flag_properties)
        self.deposit_list("effects", self.render_object.effects)
        self.deposit_list("causes", self.render_object.causes)
        self.deposit_list("activated_buffered_causes", self.render_object.activated_buffered_causes)
        self.deposit_object("scenarios", self.render_object.scenarios)
        self.deposit_object("time_jumps", self.render_object.time_jumps)

        self.deposit_datum("current_turn", self.render_object.current_turn)
        # See if the displayed turn was specified. If not, we default to the first turn of the game.
        if self.client_role == "editor":
            default_displayed_turn = self.render_object.current_turn
        else:
            default_displayed_turn = 1
        if "last_displayed_turn" in request.args:
            try:
                if int(request.args.get("last_displayed_turn")) >= 1:
                    self.deposit_datum("last_displayed_turn", int(request.args.get("last_displayed_turn")))
                else:
                    self.deposit_datum("last_displayed_turn", default_displayed_turn)
            except:
                self.deposit_datum("last_displayed_turn", default_displayed_turn)
        else:
            self.deposit_datum("last_displayed_turn", default_displayed_turn)

        # ---------------------- Game status properties -----------------------
        self.deposit_datum("game_status", self.render_object.game_status)
        self.deposit_datum("game_outcome", self.render_object.game_outcome)
        self.deposit_datum("editor_role", self.editor_role)
        # ------------------------- Tutorial comments -------------------------
        self.deposit_list("tutorial_populated_turns", list(self.tutorial_comments.keys()), volatile = True)
        if self.client_role == "editor":
            self.deposit_object("tutorial_comments", self.tutorial_comments, volatile = True)
        else:
            # We parse every tutorial comment
            parsed_tutorial_comments = {}
            for tc_turn_index, tc_text in self.tutorial_comments.items():
                parsed_tutorial_comments[tc_turn_index] = self.parse_content_for_display(tc_text)
            self.deposit_object("tutorial_comments", parsed_tutorial_comments)

        self.commit_to_output("</script>")

    # -------------------------------------------------------------------------
    # ---------------------- Document structure methods -----------------------
    # -------------------------------------------------------------------------

    def open_boardside(self):
        # Boardside is the top two thirds of the screen, containing the board control panel, the board window, and the board interaction panel
        self.commit_to_output("<div id=\"boardside\">")

    def close_boardside(self):
        self.commit_to_output("</div>")

    def open_board_window(self):
        enclosing_div = "<div id=\"board_window\">"
        svg_window = f"<svg xmlns=\"http://www.w3.org/2000/svg\" id=\"board_window_svg\">"
        background_rectangle = f"<rect x=\"0\" y =\"0\" id=\"board_window_background\" />"
        self.commit_to_output([enclosing_div, svg_window, background_rectangle])
        self.board_window_definitions()

    def close_board_window(self):
        svg_window = "</svg>"
        enclosing_div = "</div>"
        self.commit_to_output([svg_window, enclosing_div])

    def open_inspectors(self):
        self.commit_to_output("<div id=\"inspectors\">")

    def close_inspectors(self):
        self.commit_to_output("</div>")

    def open_gameside(self):
        # Gameside is bottom third of the screen, containing the game control panel and the game log
        self.commit_to_output("<div id=\"gameside\">")

    def close_gameside(self):
        self.commit_to_output("</div>")


    # -------------------------- General svg methods --------------------------

    def get_polygon_points(self, point_matrix, offset = (0, 0), scale = 1):
        # point_matrix = [[x1, y1], [x2, y2]...]
        # offset = [offset x, offset y]
        off_x, off_y = offset
        off_arr = [off_x, off_y]
        result_string = " ".join(",".join(str(pos[i] * scale + off_arr[i]) for i in range(len(pos))) for pos in point_matrix)
        return(result_string)

    def get_regular_polygon_points(self, N, R, offset = (0, 0), mode = "v", convert_to_svg = True):
        # mode == "v": vertex right above centre
        # mode == "s" : side right above centre
        off_x, off_y = offset
        if mode == "v":
            angle_offset = 0
        elif mode == "s":
            angle_offset = np.pi / N
        points = []
        for n in range(N+2):
            points.append([off_x + R * np.sin(angle_offset + 2.0 * np.pi * n / N), off_y - R * np.cos(angle_offset + 2.0 * np.pi * n / N)])
        if convert_to_svg:
            return(self.get_polygon_points(points))
        else:
            return(points)


    # ---------------------- Board control panel methods ----------------------

    def draw_board_control_panel(self):
        # board control panel allows one to traverse timeslices, and toggle camera controls.
        enclosing_div = "<div id=\"board_control_panel\">"
        enclosing_svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" id=\"board_control_panel_svg\">"
        self.commit_to_output([enclosing_div, enclosing_svg])

        # Next timeslice button
        next_timeslice_button_points = [[0, 20], [80, 20], [80, 0], [130, 50], [80, 100], [80, 80], [0, 80]]
        next_timeslice_button_polygon = f"<polygon points=\"{self.get_polygon_points(next_timeslice_button_points, (10, 0))}\" class=\"board_control_panel_button\" id=\"next_timeslice_button\" onclick=\"show_next_timeslice()\" />"
        next_timeslice_button_text = "<text x=\"16\" y=\"55\" class=\"button_label\" id=\"next_timeslice_button_label\">Next timeslice</text>"

        # Active timeslice button
        active_timeslice_button_object = f"<rect x=\"20\" y=\"120\" width=\"110\" height=\"60\" rx=\"5\" ry=\"5\" class=\"board_control_panel_button\" id=\"active_timeslice_button\" onclick=\"show_active_timeslice()\" />"
        active_timeslice_button_text = "<text x=\"40\" y=\"127\" class=\"button_label\" id=\"active_timeslice_button_label\"><tspan x=\"50\" dy=\"1.2em\">Active</tspan><tspan x=\"40\" dy=\"1.2em\">timeslice</tspan></text>"

        # Previous timeslice button
        prev_timeslice_button_points = [[130, 20], [50, 20], [50, 0], [0, 50], [50, 100], [50, 80], [130, 80]]
        prev_timeslice_button_polygon = f"<polygon points=\"{self.get_polygon_points(prev_timeslice_button_points, (10, 200))}\" class=\"board_control_panel_button\" id=\"prev_timeslice_button\" onclick=\"show_prev_timeslice()\" />"
        prev_timeslice_button_text = "<text x=27 y=255 class=\"button_label\" id=\"prev_timeslice_button_label\">Prev timeslice</text>"

        self.commit_to_output([next_timeslice_button_polygon, next_timeslice_button_text, active_timeslice_button_object, active_timeslice_button_text, prev_timeslice_button_polygon, prev_timeslice_button_text])

        self.commit_to_output("</svg>\n</div>")


    # ------------------------- Board window methods --------------------------

    def board_window_definitions(self):
        # Declarations after opening the board window <svg> environment

        self.commit_to_output("<defs>")

        # TJ marker gradients
        used_TJI = []
        used_TJI.append("  <radialGradient id=\"grad_used_TJI\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJI.append("    <stop offset=\"40%\" stop-color=\"cyan\" />")
        used_TJI.append("    <stop offset=\"100%\" stop-color=\"blue\" />")
        used_TJI.append("  </radialGradient>")
        used_TJO = []
        used_TJO.append("  <radialGradient id=\"grad_used_TJO\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJO.append("    <stop offset=\"40%\" stop-color=\"orange\" />")
        used_TJO.append("    <stop offset=\"100%\" stop-color=\"coral\" />")
        used_TJO.append("  </radialGradient>")
        used_TJ_conflict = []
        used_TJ_conflict.append("  <radialGradient id=\"grad_used_conflict\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        used_TJ_conflict.append("    <stop offset=\"40%\" stop-color=\"red\" />")
        used_TJ_conflict.append("    <stop offset=\"100%\" stop-color=\"crimson\" />") #try crimson-brown
        used_TJ_conflict.append("  </radialGradient>")
        unused_TJI = []
        unused_TJI.append("  <radialGradient id=\"grad_unused_TJI\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        unused_TJI.append("    <stop offset=\"71%\" stop-color=\"cyan\" />")
        unused_TJI.append("    <stop offset=\"100%\" stop-color=\"blue\" />")
        unused_TJI.append("  </radialGradient>")
        unused_TJO = []
        unused_TJO.append("  <radialGradient id=\"grad_unused_TJO\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        unused_TJO.append("    <stop offset=\"71%\" stop-color=\"orange\" />")
        unused_TJO.append("    <stop offset=\"100%\" stop-color=\"coral\" />")
        unused_TJO.append("  </radialGradient>")
        unused_TJ_conflict = []
        unused_TJ_conflict.append("  <radialGradient id=\"grad_unused_conflict\" cx=\"50%\" cy=\"50%\" r=\"70%\" fx=\"50%\" fy=\"50%\">")
        unused_TJ_conflict.append("    <stop offset=\"71%\" stop-color=\"red\" />")
        unused_TJ_conflict.append("    <stop offset=\"100%\" stop-color=\"crimson\" />") #try crimson-brown
        unused_TJ_conflict.append("  </radialGradient>")
        self.commit_to_output([used_TJI, used_TJO, used_TJ_conflict, unused_TJI, unused_TJO, unused_TJ_conflict])

        # unused TJ clip-path
        unused_TJ_clip_path = []
        unused_TJ_clip_path.append("  <clipPath id=\"unused_TJ_clip_path\" clipPathUnits=\"objectBoundingBox\" >")
        unused_TJ_clip_path.append(f"    <path d=\"M0,0 L1,0 L1,1 L0,1 L0,0 M{0.5-self.unused_TJ_clip_circle_radius},0.5 A{self.unused_TJ_clip_circle_radius},{self.unused_TJ_clip_circle_radius}, 180, 1, 0, {0.5+self.unused_TJ_clip_circle_radius}, 0.5 A{self.unused_TJ_clip_circle_radius},{self.unused_TJ_clip_circle_radius}, 180, 1, 0, {0.5-self.unused_TJ_clip_circle_radius}, 0.5 Z\"/>")
        unused_TJ_clip_path.append("  </clipPath>")
        self.commit_to_output(unused_TJ_clip_path)

        # drop shadow for highlighting elements
        drop_shadow_filter = []
        drop_shadow_filter.append("<filter id=\"spotlight\">")
        drop_shadow_filter.append("  <feDropShadow dx=\"0\" dy=\"0\" stdDeviation=\"15\" flood-color=\"#ffe100\" flood-opacity=\"1\"/>")
        drop_shadow_filter.append("  <feDropShadow dx=\"0\" dy=\"0\" stdDeviation=\"15\" flood-color=\"#ffe100\" flood-opacity=\"1\"/>")
        drop_shadow_filter.append("</filter>")
        self.commit_to_output(drop_shadow_filter)

        self.commit_to_output("</defs>")

    def open_board_window_camera_scope(self):
        self.commit_to_output(f"<g id=\"camera_subject\" transform-origin=\"{self.render_object.x_dim * self.board_square_base_side_length / 2}px {self.render_object.y_dim * self.board_square_base_side_length / 2}px\">")

    def close_board_window_camera_scope(self):
        self.commit_to_output("</g>")

    def draw_selection_mode_highlights(self):
        # Highlights
        selection_mode_highlights = []
        selection_mode_highlights.append(f"<g id=\"selection_mode_highlights\" visibility=\"hidden\">")
        for x in range(self.render_object.x_dim):
            for y in range(self.render_object.y_dim):
                selection_mode_highlights.append(f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"selection_mode_highlight\" id=\"selection_mode_highlight_{x}_{y}\" />")
        selection_mode_highlights.append(f"</g>")
        self.commit_to_output(selection_mode_highlights)

    def draw_selection_mode_dummies(self):
        # Dummy
        # We draw one dummy of each type
        for allegiance in self.render_object.factions:
            for stone_type in self.required_stone_types:
                self.commit_to_output(self.create_stone(stone_type, allegiance, "dummy"))


    def draw_selection_mode_azimuth_indicators(self):
        # Azimuth indicators
        triangle_width = 100
        triangle_height = 30
        triangle_offset = 0.1
        azimuth_indicator_points = [
                [[0, -triangle_height], [triangle_width / 2, 0], [-triangle_width / 2, 0]],
                [[triangle_height, 0], [0, triangle_width / 2], [0, -triangle_width / 2]],
                [[0, triangle_height], [triangle_width / 2, 0], [-triangle_width / 2, 0]],
                [[-triangle_height, 0], [0, triangle_width / 2], [0, -triangle_width / 2]]
            ]
        azimuth_indicators = []
        for azimuth in range(4):
            azimuth_indicators.append(f"  <polygon id=\"azimuth_indicator_{azimuth}\" points=\"{self.get_polygon_points(azimuth_indicator_points[azimuth])}\" class=\"azimuth_indicator\" id=\"azimuth_indicator_{azimuth}\" onclick=\"inspector.select_azimuth({azimuth})\" display=\"none\"/>")
        self.commit_to_output(azimuth_indicators)


    def draw_board_animation_overlay(self):
        animation_overlay = []
        animation_overlay.append(f"<g id=\"board_animation_overlay\" visibility=\"hidden\">")
        animation_overlay.append(f"  <rect id=\"board_animation_overlay_bg\" x=\"0\" y=\"0\" />")
        animation_overlay.append(f"  <text id=\"board_animation_overlay_text\"  x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" >changeme</text>")
        animation_overlay.append("</g>")
        self.commit_to_output(animation_overlay)

    def create_board_layer_structure(self, number_of_layers):
        self.board_layer_structure = []
        for n in range(number_of_layers):
            self.board_layer_structure.append([f"<g class=\"board_layer\" id=\"board_layer_{n}\">"])

    def commit_board_layer_structure(self):
        for n in range(len(self.board_layer_structure)):
            self.board_layer_structure[n].append([f"</g>"])
        self.commit_to_output(self.board_layer_structure)

    def draw_board_square(self, x, y):
        # Draws a board square object into the active context
        # ID is position
        # Class is static type
        class_name, z_index = self.encode_board_square_class(x, y)
        board_square_object = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"{class_name}\" id=\"{self.encode_board_square_id(x, y)}\" onclick=\"inspector.board_square_click({x},{y})\" />"
        self.board_layer_structure[z_index].append(board_square_object)

        # Draws time jump marker into z-index = 1, with
        # For each square, there is one marker for used and one marker for unused time jumps, and its color depends on whether a TJO, a TJI, or both are present
        # For efficiency, we omit squares whose main markers are placed above the time jump z index
        if z_index <= 1:
            used_time_jump_marker = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"used_time_jump_marker\" id=\"{self.encode_used_time_jump_marker_id(x, y)}\" visibility=\"hidden\" />"
            unused_time_jump_marker = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"unused_time_jump_marker\" id=\"{self.encode_unused_time_jump_marker_id(x, y)}\" visibility=\"hidden\" clip-path=\"url(#unused_TJ_clip_path)\" />"
            self.board_layer_structure[1] += [used_time_jump_marker, unused_time_jump_marker]

    def draw_board_squares(self):
        #enclosing_group = f"<g id=\"static_board_squares\">"
        #self.commit_to_output(enclosing_group)
        for x in range(self.render_object.x_dim):
            for y in range(self.render_object.y_dim):
                self.draw_board_square(x, y)
        #self.commit_to_output("</g>")

    # Stone type particulars
    def create_stone(self, stone_type, allegiance, stone_ID):
        # Stone_ID can be set to "dummy" for the selection mode dummies
        base_class = f"{allegiance}_{stone_type}"
        stone_object = []
        if stone_ID == "dummy":
            stone_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"selection_mode_dummy\" id=\"{allegiance}_{stone_type}_dummy\" transform-origin=\"50px 50px\" style=\"display:none; pointer-events:none\">")
            stone_object.append(f"  <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_animation_effects\" id=\"{allegiance}_{stone_type}_dummy_animation_effects\" transform-origin=\"50px 50px\">")
            stone_object.append(f"    <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_rotation\" id=\"{allegiance}_{stone_type}_dummy_rotation\" transform-origin=\"50px 50px\">")
        else:
            stone_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}\" id=\"{self.encode_stone_ID(stone_ID)}\" transform-origin=\"50px 50px\" style=\"pointer-events:none\">")
            stone_object.append(f"  <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_animation_effects\" id=\"{self.encode_stone_ID(stone_ID)}_animation_effects\" transform-origin=\"50px 50px\">")
            stone_object.append(f"    <polyline id=\"command_marker_{stone_ID}\" class=\"command_marker\" points=\"{self.get_regular_polygon_points(4, 40, (50, 50))}\" display=\"none\"/>")
            stone_object.append(f"    <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_rotation\" id=\"{self.encode_stone_ID(stone_ID)}_rotation\" transform-origin=\"50px 50px\">")
        stone_object.append(f"      <rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"stone_pedestal\" visibility=\"hidden\" />")

        # Now the main body of the stone
        # Playable stone types
        if stone_type == "tank":
            stone_object.append(f"      <polygon points=\"{self.get_regular_polygon_points(6, 30, (50, 50), "s")}\" class=\"{base_class}_body\" />")
            stone_object.append(f"      <rect x=\"45\" y=\"10\" width=\"10\" height=\"45\" class=\"{base_class}_barrel\" />")
            stone_object.append(f"      <circle cx=\"50\" cy=\"50\" r=\"12\" class=\"{base_class}_hatch\" />")
        if stone_type == "bombardier":
            stone_object.append(f"      <polyline points=\"{self.get_polygon_points([[25, 65], [50, 30], [75, 65]])}\" class=\"{base_class}_legs\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([[20, 25], [45, 25], [45, 70]])}\" class=\"{base_class}_left_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([[80, 25], [55, 25], [55, 70]])}\" class=\"{base_class}_right_face\" />")
            stone_object.append(f"      <rect x=\"45\" y=\"15\" width=\"10\" height=\"50\" class=\"{base_class}_welding\" />")
        if stone_type == "sniper":
            r = 32
            l = 7
            stone_object.append(f"      <line x1=\"{r+l}\" y1=\"{r-l}\" x2=\"{r-l}\" y2=\"{r+l}\" class=\"{base_class}_foot\" />")
            stone_object.append(f"      <line x1=\"{100-(r+l)}\" y1=\"{r-l}\" x2=\"{100-(r-l)}\" y2=\"{r+l}\" class=\"{base_class}_foot\" />")
            stone_object.append(f"      <line x1=\"{r+l}\" y1=\"{100-(r-l)}\" x2=\"{r-l}\" y2=\"{100-(r+l)}\" class=\"{base_class}_foot\" />")
            stone_object.append(f"      <line x1=\"{100-(r+l)}\" y1=\"{100-(r-l)}\" x2=\"{100-(r-l)}\" y2=\"{100-(r+l)}\" class=\"{base_class}_foot\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([[25, 25], [30, 25], [75, 70], [75, 75], [70, 75], [25, 30]])}\" class=\"{base_class}_left_leg\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([[75, 25], [70, 25], [25, 70], [25, 75], [30, 75], [75, 30]])}\" class=\"{base_class}_right_leg\" />")
            stone_object.append(f"      <line x1=\"50\" y1=\"50\" x2=\"50\" y2=\"20\" class=\"{base_class}_gun\" />")
            stone_object.append(f"      <rect x=\"40\" y=\"40\" width=\"20\" height=\"20\" class=\"{base_class}_nest\" />")
        if stone_type == "tagger":
            pentagon = self.get_regular_polygon_points(5, 30, convert_to_svg = False)
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[4], pentagon[0], pentagon[1], [0, 0]], (50, 50))}\" class=\"{base_class}_top_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[1], pentagon[2], [0, 0]], (50, 50))}\" class=\"{base_class}_right_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[2], pentagon[3], [0, 0]], (50, 50))}\" class=\"{base_class}_bottom_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[3], pentagon[4], [0, 0]], (50, 50))}\" class=\"{base_class}_left_face\" />")
            stone_object.append(f"      <polyline points=\"{self.get_polygon_points(pentagon, [50, 50])}\" class=\"{base_class}_outline\" />")
        if stone_type == "wildcard":
            r = 30
            k = 0.8
            stone_object.append(f"      <circle cx=\"50\" cy=\"50\" r=\"{r}\" class=\"{base_class}_body\" />")
            stone_object.append(f"      <line x1=\"{50-k*r}\" y1=\"{50-k*r}\" x2=\"{50+k*r}\" y2=\"{50+k*r}\" class=\"{base_class}_halo\" />")
            stone_object.append(f"      <line x1=\"{50-k*r}\" y1=\"{50+k*r}\" x2=\"{50+k*r}\" y2=\"{50-k*r}\" class=\"{base_class}_halo\" />")
        # Neutral stone types
        if stone_type == "box":
            stone_object.append(f"      <rect x=\"15\" y=\"15\" width=\"70\" height=\"70\" class=\"{base_class}_base\" />")
            stone_object.append(f"      <line x1=\"15\" y1=\"15\" x2=\"85\" y2=\"85\" class=\"{base_class}_line\" />")
            stone_object.append(f"      <line x1=\"15\" y1=\"85\" x2=\"85\" y2=\"15\" class=\"{base_class}_line\" />")
            stone_object.append(f"      <rect x=\"15\" y=\"15\" width=\"70\" height=\"70\" class=\"{base_class}_outline\" />")
        if stone_type == "mine":
            stone_object.append(f"      <path d=\"M45,15 L45,25 A20,20,90,0,1,25,45 L15,45 A40,40,0,0,0,15,55 L25,55 A20,20,90,0,1,45,75 L45,85 A40,40,0,0,0,55,85 L55,75 A20,20,90,0,1,75,55 L85,55 A40,40,0,0,0,85,45 L75,45 A20,20,90,0,1,55,25 L55,15 A40,40,0,0,0, 45,15 Z\" class=\"{base_class}_body\" /> ")
            stone_object.append(f"      <circle cx=\"50\" cy=\"50\" r=\"8\" class=\"{base_class}_button\" />")


        stone_object.append("    </g>")
        stone_object.append("  </g>")
        stone_object.append("</g>")
        return(stone_object)

    def create_base(self, base_ID):
        iden = self.encode_base_ID(base_ID)
        base_object = [
            f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"base\" id=\"{iden}\" transform-origin=\"50px 50px\" style=\"pointer-events:none\">",
            f"  <circle cx=\"50\" cy=\"50\" r=\"25\" class=\"base_indicator\" id=\"{iden}_indicator\" />",
            f"</g>"
        ]
        return(base_object)


    def draw_stones(self):
        # These are drawn on the x=0,y=0 square with display:none, and will be
        # moved around by JavaScript using the 'transform' attrib1ute.
        # First, we prepare the neutral stones
        for neutral_stone_ID in self.render_object.faction_armies["GM"]:
            self.board_layer_structure[4].append(self.create_stone(self.render_object.stone_properties[neutral_stone_ID]["stone_type"], "GM", neutral_stone_ID))
        for faction in self.render_object.factions:
            for faction_stone_ID in self.render_object.faction_armies[faction]:
                self.board_layer_structure[4].append(self.create_stone(self.render_object.stone_properties[faction_stone_ID]["stone_type"], faction, faction_stone_ID))

    def draw_bases(self):
        # Same principle as stones
        for base_ID in self.render_object.bases:
            self.board_layer_structure[2].append(self.create_base(base_ID))

    def draw_square_highlighter(self):
        self.board_layer_structure[3].append(f"<polyline id=\"square_highlighter\" points=\"{self.get_polygon_points([[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]])}\" display=\"none\"/>")

    def draw_board(self):
        self.open_board_window()
        self.open_board_window_camera_scope()
        self.create_board_layer_structure(5) # every element is first added to this, where index = z-index
        self.draw_board_squares()
        self.draw_stones()
        self.draw_bases()
        self.draw_square_highlighter()
        self.commit_board_layer_structure()
        self.draw_selection_mode_highlights()
        self.draw_selection_mode_dummies()
        self.close_board_window_camera_scope()
        self.draw_selection_mode_azimuth_indicators()
        self.draw_board_animation_overlay()
        self.close_board_window()

    # --------------------------- Inspector methods ---------------------------

    def draw_inspector_table(self, which_inspector, table_dict):
        # table_dict["js_value_key"] = "human-readable label"
        self.commit_to_output(f"<table id=\"{which_inspector}_info_table\" class=\"inspector_table\">")
        for table_key, table_label in table_dict.items():
            table_element = []
            table_element.append(f"<tr id=\"{which_inspector}_info_{table_key}_container\" class=\"inspector_table_container\">")
            table_element.append(f"  <td id=\"{which_inspector}_info_{table_key}_label\" class=\"{which_inspector}_inspector_table_label\">{table_label}</td>")
            table_element.append(f"  <td id=\"{which_inspector}_info_{table_key}\" class=\"inspector_table_value\"></td>")
            table_element.append(f"</tr>")
            self.commit_to_output(table_element)
        self.commit_to_output(f"</table>")

    def draw_stone_inspector(self):
        # This inspector is used for:
        #   1. Inspecting stone commands
        #   2. Administering stone commands
        self.commit_to_output("<div id=\"stone_inspector\" class=\"inspector\">")
        self.commit_to_output("  <h1 id=\"stone_inspector_title\" class=\"inspector_title\"></h1>")
        self.commit_to_output("  <div id=\"stone_inspector_header\" class=\"stone_inspector_part\">")
        self.draw_inspector_table("stone", {"allegiance" : "Allegiance", "stone_type" : "Stone type", "startpoint" : "Start-point", "endpoint" : "End-point"})
        stone_inspector_object = []
        stone_inspector_object.append("  </div>")
        stone_inspector_object.append("  <div id=\"stone_inspector_commands\" class=\"stone_inspector_part\">")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"stone_inspector_commands_svg\">")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"undo_command_button_svg\" style=\"display:none;\">")
        stone_inspector_object.append("      <g id=\"undo_command_button\">")
        stone_inspector_object.append("        <rect x=\"0\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"undo_command_button_polygon\" onclick=\"inspector.undo_command()\" />")
        stone_inspector_object.append("        <text x=\"50\" y=\"42\" text-anchor=\"middle\" id=\"undo_command_button_label\" class=\"button_label\">Undo</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"stone_inspector_selection_mode_buttons_svg\">")
        stone_inspector_object.append("      <g id=\"abort_selection_button\" display=\"none\">")
        stone_inspector_object.append("        <rect x=\"0\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"abort_selection_button_polygon\" onclick=\"inspector.turn_off_selection_mode()\" />")
        stone_inspector_object.append("        <text x=\"50\" y=\"42\" text-anchor=\"middle\" id=\"abort_selection_button_label\" class=\"button_label\">Abort</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("      <g id=\"submit_selection_button\" display=\"none\">")
        stone_inspector_object.append("        <rect x=\"110\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"submit_selection_button_polygon\" onclick=\"inspector.submit_selection()\" />")
        stone_inspector_object.append("        <text x=\"160\" y=\"42\" text-anchor=\"middle\" class=\"button_label\">Submit</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("  </div>")
        stone_inspector_object.append("</div>")
        self.commit_to_output(stone_inspector_object)

    def draw_tracking_inspector(self):
        self.commit_to_output("<div id=\"tracking_inspector\" class=\"inspector\">")
        #self.commit_to_output("  <p id=\"stone_tracking_label\"></p>")
        self.commit_to_output("  <div id=\"tracking_inspector_header\">")
        self.commit_to_output("    <p id=\"stone_tracking_label\"></p>")
        self.commit_to_output("  </div>")
        self.commit_to_output(f"  <svg width=\"70%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"tracking_inspector_svg\">")


        # Start-point button
        startpoint_button_points = [[130, 20], [50, 20], [50, 0], [0, 50], [50, 100], [50, 80], [130, 80]]
        startpoint_button_polygon = f"<polygon points=\"{self.get_polygon_points(startpoint_button_points, (10, 10), 0.8)}\" class=\"game_control_panel_button\" id=\"tracking_startpoint_button\" onclick=\"tracking_startpoint()\" />"
        startpoint_button_text = "<text x=25 y=55 class=\"button_label\" id=\"tracking_startpoint_button_label\">Start-point</text>"

        # End-point button
        endpoint_button_points = [[0, 20], [80, 20], [80, 0], [130, 50], [80, 100], [80, 80], [0, 80]]
        endpoint_button_polygon = f"<polygon points=\"{self.get_polygon_points(endpoint_button_points, (120, 10), 0.8)}\" class=\"game_control_panel_button\" id=\"tracking_endpoint_button\" onclick=\"tracking_endpoint()\" />"
        endpoint_button_text = "<text x=\"128\" y=\"55\" class=\"button_label\" id=\"tracking_endpoint_button_label\">End-point</text>"

        # Turn off tracking button
        turn_off_tracking_button_object = f"<rect x=\"235\" y=\"26\" width=\"88\" height=\"48\" rx=\"5\" ry=\"5\" class=\"game_control_panel_button\" id=\"turn_off_tracking_button\" onclick=\"cameraman.track_stone(null)\" />"
        turn_off_tracking_button_text = "<text x=\"238\" y=\"27\" class=\"button_label\" id=\"turn_off_tracking_button_label\"><tspan x=\"248\" dy=\"1.2em\">Turn off</tspan><tspan x=\"248\" dy=\"1.2em\">tracking</tspan></text>"

        self.commit_to_output([startpoint_button_polygon, startpoint_button_text, endpoint_button_polygon, endpoint_button_text, turn_off_tracking_button_object, turn_off_tracking_button_text])

        self.commit_to_output("  </svg>")
        self.commit_to_output("</div>")


    def draw_square_inspector(self):
        square_inspector_object = []
        self.commit_to_output("<div id=\"square_inspector\" class=\"inspector\">")
        self.commit_to_output("  <h1 id=\"square_inspector_title\" class=\"inspector_title\"></h1>")
        self.draw_inspector_table("square", {"active_effects" : "Active ante-effects", "activated_causes" : "Activated retro-causes", "inactive_effects" : "Inactive ante-effects", "not_activated_causes" : "Not activated retro-causes"})
        self.commit_to_output("</div>")

    def draw_choice_selector(self):
        # Replaces tracking_inspector in selection mode
        choice_selector = []
        choice_selector.append("<div id=\"choice_selector\" class=\"selector\" style=\"display:none;\">")
        choice_selector.append("  <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"choice_selector_buttons_svg\">")
        choice_selector.append("  </svg>")
        choice_selector.append("</div>")
        self.commit_to_output(choice_selector)

    def draw_swap_effect_selector(self):
        # Replaces tracking_inspector in selection mode
        choice_selector = []
        choice_selector.append("<div id=\"swap_effect_selector\" class=\"selector\" style=\"display:none;\">")
        choice_selector.append("  <table id=\"swap_effect_selector_table\" class=\"selector_table\">")
        choice_selector.append("  </table>")
        choice_selector.append("</div>")
        self.commit_to_output(choice_selector)

    def draw_inspectors(self):
        self.open_inspectors()
        self.draw_stone_inspector()
        self.draw_tracking_inspector()
        self.draw_square_inspector()
        self.draw_choice_selector()
        self.draw_swap_effect_selector()
        self.close_inspectors()

    # ---------------------- Game control panel methods -----------------------

    def draw_game_control_panel(self):
        # game control panel allows one to traverse rounds, as well as change the game status (resign, offer draw, submit commands, request paradox viewing...).
        enclosing_div = "<div id=\"game_control_panel\">"
        enclosing_svg = "<svg xmlns=\"http://www.w3.org/2000/svg\" id=\"game_control_panel_svg\">"
        self.commit_to_output([enclosing_div, enclosing_svg])

        # Previous round button
        prev_round_button_points = [[130, 20], [50, 20], [50, 0], [0, 50], [50, 100], [50, 80], [130, 80]]
        prev_round_button_polygon = f"<polygon points=\"{self.get_polygon_points(prev_round_button_points, (10, 0))}\" class=\"game_control_panel_button\" id=\"prev_round_button\" onclick=\"show_prev_round()\" />"
        prev_round_button_text = "<text x=40 y=55 class=\"button_label\" id=\"prev_round_button_label\">Prev round</text>"

        # Active round button
        active_round_button_object = f"<rect x=\"150\" y=\"20\" width=\"110\" height=\"60\" rx=\"5\" ry=\"5\" class=\"game_control_panel_button\" id=\"active_round_button\" onclick=\"show_active_round()\" />"
        active_round_button_text = "<text x=\"170\" y=\"27\" class=\"button_label\" id=\"active_round_button_label\"><tspan x=\"182\" dy=\"1.2em\">Active</tspan><tspan x=\"182\" dy=\"1.2em\">round</tspan></text>"

        # Next round button
        next_round_button_points = [[0, 20], [80, 20], [80, 0], [130, 50], [80, 100], [80, 80], [0, 80]]
        next_round_button_polygon = f"<polygon points=\"{self.get_polygon_points(next_round_button_points, (270, 0))}\" class=\"game_control_panel_button\" id=\"next_round_button\" onclick=\"show_next_round()\" />"
        next_round_button_text = "<text x=\"287\" y=\"55\" class=\"button_label\" id=\"next_round_button_label\">Next round</text>"

        # We make the links for client_role setting
        if self.client_role == "editor":
            client_role_setting = [f"  <div id=\"game_control_panel_client_role_setting\">"]
            for possible_role in ["A", "B"]:
                if possible_role == self.editor_role:
                    client_role_setting.append(f"    <button class=\"editor_role_disabled_link\">{possible_role}</button>")
                else:
                    client_role_setting.append(f"    <a href=\"{url_for("tutorial.tutorial", tutorial_id = self.tutorial_id, editor_role = possible_role)}\" class=\"editor_role_link\">{possible_role}</a>")
            client_role_setting.append(f"  </div>")
        else:
            client_role_setting = ""

        self.commit_to_output([prev_round_button_polygon, prev_round_button_text, active_round_button_object, active_round_button_text, next_round_button_polygon, next_round_button_text, client_role_setting])
        self.commit_to_output("</svg>")

        if self.render_object.game_status == "in_progress" and self.editor_role in ["A", "B"]:
            self.draw_command_form()
        self.commit_to_output("</div>")

    # --------------------------- Game log methods ----------------------------

    def draw_game_log(self):
        self.commit_to_output([
            f"<div id=\"game_log\">",
            f"  <div id=\"game_log_nav\">",
            f"    <div id=\"game_log_nav_timeslice_label\" class=\"game_log_nav_label\">Timeslice</div>",
            f"    <div id=\"game_log_nav_timeslice_value\" class=\"game_log_nav_label\"></div>",
            f"    <div id=\"game_log_nav_round_label\" class=\"game_log_nav_label\">Round</div>",
            f"    <div id=\"game_log_nav_round_value\" class=\"game_log_nav_label\"></div>"
            ])

        self.commit_to_output("  </div>")

        if self.render_object.game_status == "concluded":
            self.draw_outcome_message()

        self.commit_to_output("</div>")


    # ------------------------- Command form methods --------------------------

    def draw_command_form(self):
        command_form = []
        command_form.append(f"<div id=\"command_form_div\">")
        command_form.append(f"  <form id=\"command_form\" class=\"submission_form\" action=\"{url_for("tutorial.command_submission", tutorial_id=self.tutorial_id, editor_role=self.editor_role)}\" method=\"POST\">")
        if not self.render_object.did_player_finish_turn:
            for stone_ID in self.render_object.stones_to_be_commanded:
                command_form.append(f"    <fieldset id=\"command_data_{stone_ID}\" class=\"command_data_field\">")
                for default_keyword in Abstract_Output.command_keywords:
                    command_form.append(f"      <input type=\"hidden\" name=\"cmd_{default_keyword}_{stone_ID}\" id=\"cmd_{default_keyword}_{stone_ID}\" >")
                command_form.append(f"    </fieldset>")
            command_form.append(f"    <fieldset id=\"command_data_meta\" class=\"command_data_field\">")
            command_form.append(f"      <input type=\"hidden\" name=\"touch_order\" id=\"touch_order_input\">")
            command_form.append(f"    </fieldset>")

        command_form.append(f"    <button type=\"submit\" name=\"command_submission\" value=\"submit\" id=\"submit_commands_button\">Submit commands</button>")
        command_form.append(f"  </form>")
        command_form.append(f"</div>")
        self.commit_to_output(command_form)

    # ------------------------ Outcome message methods ------------------------

    def draw_outcome_message(self):
        self.commit_to_output(f"<div id=\"game_log_outcome\">")
        if self.render_object.game_outcome in self.render_object.factions:
            self.commit_to_output(f"Pl. <span id=\"game_log_win_{self.render_object.game_outcome}\">{self.render_object.game_outcome}</span> won!")
        else:
            if self.render_object.game_outcome == "draw":
                self.commit_to_output(f"<span id=\"game_log_draw\">Draw</span>")
        self.commit_to_output("</div>")

    def parse_content_for_display(self, content_text):
        # This function allows us to add not just html objects, but also dynamical python-calculated objects, such as links with URL_FOR
        parsed_content_text = content_text

        def lft(href, label):
            # link from text
            return(f"<a href=\"{href}\" target=\"_blank\">{label}</a>")

        def stone_highlight(stone_ID, stone_label):
            return(f"<span class=\"stone_highlight\" onmouseenter=\"set_stone_highlight({stone_ID})\" onmouseleave=\"set_stone_highlight(null)\" onclick=\"cameraman.track_stone({stone_ID})\">{stone_label}</span>")

        def square_highlight(t, x, y, square_label):
            return(f"<span class=\"square_highlight\" onclick=\"go_to_square({t},{x},{y})\">{square_label}</span>")

        # Magic word patterns
        magic_word_patterns = {
            "--" : (lambda match : "&#8212;"),
            "_URLKW2_([A-Za-z.]+)<([A-Za-z_]+)=([A-Za-z0-9]+),([A-Za-z_]+)=([A-Za-z0-9]+)>_([A-Za-z0-9 ]+)_" : (lambda match : lft(url_for(match.group(1), **{match.group(2) : match.group(3), match.group(4) : match.group(5)}), match.group(6)) ),
            "_URLKW_([A-Za-z.]+)<([A-Za-z_]+)=([A-Za-z0-9]+)>_([A-Za-z0-9 ]+)_" : (lambda match : lft(url_for(match.group(1), **{match.group(2) : match.group(3)}), match.group(4)) ),
            "_URL_([A-Za-z.]+)_([A-Za-z0-9 ]+)_" : (lambda match : lft(url_for(match.group(1)), match.group(2)) ),
            "_URLEXT_<([A-Za-z.:/]+)>_([A-Za-z0-9 ]+)_" : (lambda match : lft(match.group(1), match.group(2)) ),
            "_STONE_([0-9]+)_([A-Za-z0-9\- ]+)_" : (lambda match: stone_highlight(match.group(1), match.group(2))),
            "_SQUARE_([0-9]+),([0-9]+),([0-9]+)_([A-Za-z0-9\- ]+)_" : (lambda match: square_highlight(match.group(1), match.group(2), match.group(3), match.group(4)))
            }

        for pattern, replacer in magic_word_patterns.items():
            parsed_content_text = re.sub(pattern, replacer, parsed_content_text)

        return(parsed_content_text)

    def draw_game_management(self):
        self.commit_to_output("<div id=\"game_management\">")
        # Tutorial comment text

        if self.client_role == "editor":
            # Tutorial editor: can edit the tutorial comment
            self.commit_to_output([
                f"<form id=\"tutorial_comment_form\" action=\"{url_for(f"tutorial.tutorial_edit_tutorial_comments", tutorial_id = self.tutorial_id, editor_role = self.editor_role)}\" method=\"post\">",
                f"  <textarea id=\"tcf_textarea\" name=\"tutorial_comment\"></textarea>",
                f"  <input type=\"hidden\" id=\"tcf_turn_index\" name=\"turn_index\" value=\"\"></input>",
                f"  <button type=\"submit\" id=\"tcf_edit_tutorial_comment_btn\" name=\"tcf_action\" value=\"edit_tutorial_comment\">Save</button>",
                f"</form>"
                ])
        else:
            # Can view the tutorial comment parsed through magic keyword converter
            self.commit_to_output("<div id=\"tutorial_comment_display\"></div>")


        self.commit_to_output("</div>")

    # ---------------------------- Global methods -----------------------------

    def render_game(self):
        self.open_body()
        self.deposit_contextual_data()

        # Initialize boardside
        self.open_boardside()

        # Draw the board control panel
        self.draw_board_control_panel()

        # Draw the static board as a set of timeslices
        self.draw_board()

        # Draw inspectors
        self.draw_inspectors()

        # Close boardside
        self.close_boardside()

        # Open gameside
        self.open_gameside()

        self.draw_game_control_panel()
        self.draw_game_log()
        self.draw_game_management()

        # Close gameside
        self.close_gameside()

        self.close_body()


