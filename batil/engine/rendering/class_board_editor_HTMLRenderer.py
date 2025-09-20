# -----------------------------------------------------------------------------
# ---------------------------- class HTMLRenderer -----------------------------
# -----------------------------------------------------------------------------
# This renderer creates a longstring in a HTML format, with interactive
# features managed by JavaScript.
# A hidden form is dynamically altered by user interaction, and can be resolved
# on submission, serverside.

import numpy as np

import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)


from batil.engine.rendering.class_Renderer import Renderer


class BoardEditorHTMLRenderer(Renderer):

    def __init__(self, render_object, board_id):
        super().__init__(render_object)
        self.board_id = board_id
        self.structured_output = []

        # ------------------------ Rendering constants ------------------------

        # Document structure

        self.board_square_empty_color = "#E5E5FF"
        self.unused_TJ_clip_circle_radius = 0.45

        # Board structure
        self.board_square_base_side_length = 100

        # Stone types
        # Since the editor can add any stone type, they are all required
        self.required_stone_types = {
                "GM": ["box", "mine"],
                "A" : ["tank", "bombardier", "tagger", "sniper", "wildcard"],
                "B" : ["tank", "bombardier", "tagger", "sniper", "wildcard"]
            }
        board_squares_info_data_file = current_app.open_resource("engine/game_logic/board_squares_info.json")
        self.board_squares_info_data = json.load(board_squares_info_data_file)
        board_squares_info_data_file.close()

        element_keywords_data_file = current_app.open_resource("engine/stones/element_keywords.json")
        self.element_keywords = json.load(element_keywords_data_file)
        element_keywords_data_file.close()


    # ------------------- Output file communication methods -------------------

    def open_body(self):
        self.commit_to_output([
                "<body onkeydown=\"parse_keydown_event(event)\" onkeyup=\"parse_keyup_event(event)\">"
            ])

    def close_body(self):
        # We actually leave the <body> tag open for possible scripts to be slapped onto the end
        if self.render_object["client_action"] == "edit":
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='boc_board_editor.js') }\"></script>")
        else:
            self.commit_to_output(f"  <script src=\"{ url_for('static', filename='boc_board_editor_read_only.js') }\"></script>")

    def commit_to_output(self, html_object):
        self.structured_output.append(html_object)

    # ------------------------ Label mangling methods -------------------------

    def encode_board_square_id(self, x, y):
        return(f"board_square_{x}_{y}")

    def encode_board_square_class(self, x, y):
        # returns a tuple (class_name, z_index)
        if self.render_object["board_static"][x][y] == " ":
            return("board_square_empty")
        elif self.render_object["board_static"][x][y] == "X":
            return("board_square_wall")
        else:
            return("board_square_unknown")

    def encode_stone_ID(self, stone):
        return(f"stone_{stone["x"]}_{stone["y"]}")

    def encode_base_ID(self, base):
        return(f"base_{base["x"]}_{base["y"]}")

    # ---------------------------- Data depositing ----------------------------

    def deposit_datum(self, name, value):
        if value is None:
            self.commit_to_output(f"  var {name} = null;")
        elif isinstance(value, bool):
            if value:
                self.commit_to_output(f"  var {name} = true;")
            else:
                self.commit_to_output(f"  var {name} = false;")
        elif isinstance(value, str):
            self.commit_to_output(f"  var {name} = {json.dumps(value)};")
        else:
            self.commit_to_output(f"  var {name} = {value};")

    def deposit_list(self, name, value):
        # If there are no dictionaries in the nest, the output of json.dumps is
        # immediately interpretable by javascript
        self.commit_to_output(f"  var {name} = {json.dumps(value)};")

    def deposit_object(self, name, value):
        #json_string_raw = json.dumps(value)
        #json_string_sanitised = json_string_raw.replace("<", "\\u003c").replace(">", "\\u003e")
        #self.commit_to_output(f"  var {name} = JSON.parse('{json_string_sanitised}');")
        self.commit_to_output(f"  var {name} = {json.dumps(value)};")

    def deposit_contextual_data(self):
        # This method creates a <script> environment which deposits all data
        # which change between games and which are needed by the JavaScript.
        # This means the main script can be global for all the games :)
        self.commit_to_output(f"<script>")
        # ------------------------ General properties -------------------------
        self.deposit_list("board_static", self.render_object["board_static"])
        self.deposit_datum("t_dim", self.render_object["t_dim"])
        self.deposit_datum("x_dim", self.render_object["x_dim"])
        self.deposit_datum("y_dim", self.render_object["y_dim"])

        self.deposit_object("bases", self.render_object["bases"])
        self.deposit_object("stones", self.render_object["stones"])

        # -------------------------- Static app data --------------------------
        static_stone_data_file = current_app.open_resource("engine/stones/stone_properties.json")
        static_stone_data = json.load(static_stone_data_file)
        static_stone_data_file.close()
        self.deposit_object("static_stone_data", static_stone_data)

        self.deposit_list("board_square_types", list(self.board_squares_info_data.keys()))
        self.deposit_object("board_square_info", self.board_squares_info_data)

        self.deposit_list("bases_keywords", self.element_keywords["bases"])
        self.deposit_list("stones_keywords", self.element_keywords["stones"])

        self.deposit_datum("client_action", self.render_object["client_action"])

        self.commit_to_output("</script>")

    # -------------------------------------------------------------------------
    # ---------------------- Document structure methods -----------------------
    # -------------------------------------------------------------------------

    def open_boardside(self):
        # Boardside is the top two thirds of the screen, containing the board control panel, the board window, and the board interaction panel
        self.commit_to_output("<div id=\"boardside\">")

    def close_boardside(self):
        self.commit_to_output("</div>")

    def draw_board_control_panel(self):
        self.commit_to_output("<div id=\"board_control_panel\">\n</div>")

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


    # ------------------------- Board window methods --------------------------

    def board_window_definitions(self):
        # Declarations after opening the board window <svg> environment

        self.commit_to_output("<defs>")

        # drop shadow for highlighting elements
        drop_shadow_filter = []
        drop_shadow_filter.append("<filter id=\"spotlight\">")
        drop_shadow_filter.append("  <feDropShadow dx=\"0\" dy=\"0\" stdDeviation=\"15\" flood-color=\"#ffe100\" flood-opacity=\"1\"/>")
        drop_shadow_filter.append("  <feDropShadow dx=\"0\" dy=\"0\" stdDeviation=\"15\" flood-color=\"#ffe100\" flood-opacity=\"1\"/>")
        drop_shadow_filter.append("</filter>")
        self.commit_to_output(drop_shadow_filter)

        self.commit_to_output("</defs>")

    def open_board_window_camera_scope(self):
        self.commit_to_output(f"<g id=\"camera_subject\" transform-origin=\"{self.render_object["x_dim"] * self.board_square_base_side_length / 2}px {self.render_object["y_dim"] * self.board_square_base_side_length / 2}px\">")

    def close_board_window_camera_scope(self):
        self.commit_to_output("</g>")

    def draw_selection_mode_highlights(self):
        # Highlights
        selection_mode_highlights = []
        selection_mode_highlights.append(f"<g id=\"selection_mode_highlights\" visibility=\"hidden\">")
        for x in range(self.render_object["x_dim"]):
            for y in range(self.render_object["y_dim"]):
                selection_mode_highlights.append(f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"selection_mode_highlight\" id=\"selection_mode_highlight_{x}_{y}\" />")
        selection_mode_highlights.append(f"</g>")
        self.commit_to_output(selection_mode_highlights)

    def draw_selection_mode_dummies(self):
        # Dummy
        # We draw one dummy of each type
        for allegiance in self.required_stone_types.keys():
            for stone_type in self.required_stone_types[allegiance]:
                self.commit_to_output(self.create_stone({"faction" : allegiance, "stone_type" : stone_type}, "dummy"))


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

    def create_board_layer_structure(self, number_of_layers):
        self.board_layer_structure = []
        for n in range(number_of_layers):
            self.board_layer_structure.append([f"<g class=\"board_layer\" id=\"board_layer_{n}\">"])

    def commit_board_layer_structure(self):
        for n in range(len(self.board_layer_structure)):
            self.board_layer_structure[n].append([f"</g>"])
        self.commit_to_output(self.board_layer_structure)

    # Templates (squares, bases, stones)

    def draw_templates(self):
        templates = ["<g id=\"group_templates\" display=\"none\">"]
        # A template id is always {class}_template"
        # board square templates
        templates.append(f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"0\" y=\"0\" class=\"board_square_empty\" id=\"board_square_empty_template\" />")
        templates.append(f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"0\" y=\"0\" class=\"board_square_wall\" id=\"board_square_wall_template\" />")
        # bases templates
        for faction in ["A", "B", "neutral"]:
            base_class = f"base_{faction}"
            templates.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}\" id=\"{base_class}_template\" transform-origin=\"50px 50px\" style=\"pointer-events:none\">")
            templates.append(f"  <circle cx=\"50\" cy=\"50\" r=\"25\" class=\"{base_class}_indicator\" id=\"{base_class}_template_indicator\" />")
            templates.append(f"</g>")
        # stones templates
        for faction in self.required_stone_types.keys():
            for stone_type in self.required_stone_types[faction]:
                templates.append(self.create_stone({"faction" : faction, "stone_type" : stone_type}, "template"))

        templates.append("</g>")
        self.commit_to_output(templates)

    def draw_board_square(self, x, y):
        # Draws a board square object into the active context
        # ID is position
        # Class is static type
        # All squares are at layer 0
        class_name = self.encode_board_square_class(x, y)
        board_square_object = f"  <rect width=\"{self.board_square_base_side_length}\" height=\"{self.board_square_base_side_length}\" x=\"{x * self.board_square_base_side_length}\" y=\"{y * self.board_square_base_side_length}\" class=\"{class_name}\" id=\"{self.encode_board_square_id(x, y)}\" onclick=\"inspector.board_square_click({x},{y})\" />"
        self.board_layer_structure[0].append(board_square_object)


    def draw_board_squares(self):
        #enclosing_group = f"<g id=\"static_board_squares\">"
        #self.commit_to_output(enclosing_group)

        self.board_layer_structure[0].append("<g id=\"group_squares\">")
        for x in range(self.render_object["x_dim"]):
            for y in range(self.render_object["y_dim"]):
                self.draw_board_square(x, y)
        self.board_layer_structure[0].append("</g>")

    # Stone type particulars
    def create_stone(self, stone, special_id = None, special_id_display="none", special_id_onclick=None):
        # Stone_ID can be set to "dummy" for the selection mode dummies
        base_class = f"{stone["faction"]}_{stone["stone_type"]}"
        stone_object = []
        if "x" in stone.keys():
            stone_x = stone["x"] * self.board_square_base_side_length
            stone_y = stone["y"] * self.board_square_base_side_length
        else:
            stone_x = 0
            stone_y = 0
        azimuth = 0
        if "a" in stone.keys():
            if stone["a"] is not None:
                azimuth = stone["a"] * 90
        if special_id is not None:
            if special_id_onclick is None:
                stone_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class} {special_id}\" id=\"{base_class}_{special_id}\" transform-origin=\"50px 50px\" style=\"display:{special_id_display}; pointer-events:none; transform:translate({stone_x}px,{stone_y}px)\">")
            else:
                stone_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class} {special_id}\" id=\"{base_class}_{special_id}\" transform-origin=\"50px 50px\" style=\"display:{special_id_display}; transform:translate({stone_x}px,{stone_y}px)\" onclick=\"{special_id_onclick}\">")
            stone_object.append(f"  <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_animation_effects\" id=\"{base_class}_{special_id}_animation_effects\" transform-origin=\"50px 50px\">")
            stone_object.append(f"    <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_rotation\" id=\"{base_class}_{special_id}_rotation\" transform-origin=\"50px 50px\" style=\"transform:rotate({azimuth}deg)\">")
        else:
            stone_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}\" id=\"{self.encode_stone_ID(stone)}\" transform-origin=\"50px 50px\" style=\"pointer-events:none; transform:translate({stone_x}px,{stone_y}px)\">")
            stone_object.append(f"  <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_animation_effects\" id=\"{self.encode_stone_ID(stone)}_animation_effects\" transform-origin=\"50px 50px\">")
            stone_object.append(f"    <g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}_rotation\" id=\"{self.encode_stone_ID(stone)}_rotation\" transform-origin=\"50px 50px\" style=\"transform:rotate({azimuth}deg)\">")
        stone_object.append(f"      <rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"stone_pedestal\" visibility=\"hidden\" />")

        # Now the main body of the stone
        # Playable stone types
        if stone["stone_type"] == "tank":
            stone_object.append(f"      <polygon points=\"{self.get_regular_polygon_points(6, 30, (50, 50), "s")}\" class=\"{base_class}_body\" />")
            stone_object.append(f"      <rect x=\"45\" y=\"10\" width=\"10\" height=\"45\" class=\"{base_class}_barrel\" />")
            stone_object.append(f"      <circle cx=\"50\" cy=\"50\" r=\"12\" class=\"{base_class}_hatch\" />")
        if stone["stone_type"] == "bombardier":
            stone_object.append(f"      <polyline points=\"{self.get_polygon_points([[25, 65], [50, 30], [75, 65]])}\" class=\"{base_class}_legs\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([[20, 25], [45, 25], [45, 70]])}\" class=\"{base_class}_left_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([[80, 25], [55, 25], [55, 70]])}\" class=\"{base_class}_right_face\" />")
            stone_object.append(f"      <rect x=\"45\" y=\"15\" width=\"10\" height=\"50\" class=\"{base_class}_welding\" />")
        if stone["stone_type"] == "sniper":
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
        if stone["stone_type"] == "tagger":
            pentagon = self.get_regular_polygon_points(5, 30, convert_to_svg = False)
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[4], pentagon[0], pentagon[1], [0, 0]], (50, 50))}\" class=\"{base_class}_top_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[1], pentagon[2], [0, 0]], (50, 50))}\" class=\"{base_class}_right_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[2], pentagon[3], [0, 0]], (50, 50))}\" class=\"{base_class}_bottom_face\" />")
            stone_object.append(f"      <polygon points=\"{self.get_polygon_points([pentagon[3], pentagon[4], [0, 0]], (50, 50))}\" class=\"{base_class}_left_face\" />")
            stone_object.append(f"      <polyline points=\"{self.get_polygon_points(pentagon, [50, 50])}\" class=\"{base_class}_outline\" />")
        if stone["stone_type"] == "wildcard":
            r = 30
            k = 0.8
            stone_object.append(f"      <circle cx=\"50\" cy=\"50\" r=\"{r}\" class=\"{base_class}_body\" />")
            stone_object.append(f"      <line x1=\"{50-k*r}\" y1=\"{50-k*r}\" x2=\"{50+k*r}\" y2=\"{50+k*r}\" class=\"{base_class}_halo\" />")
            stone_object.append(f"      <line x1=\"{50-k*r}\" y1=\"{50+k*r}\" x2=\"{50+k*r}\" y2=\"{50-k*r}\" class=\"{base_class}_halo\" />")
        # Neutral stone types
        if stone["stone_type"] == "box":
            stone_object.append(f"      <rect x=\"15\" y=\"15\" width=\"70\" height=\"70\" class=\"{base_class}_base\" />")
            stone_object.append(f"      <line x1=\"15\" y1=\"15\" x2=\"85\" y2=\"85\" class=\"{base_class}_line\" />")
            stone_object.append(f"      <line x1=\"15\" y1=\"85\" x2=\"85\" y2=\"15\" class=\"{base_class}_line\" />")
            stone_object.append(f"      <rect x=\"15\" y=\"15\" width=\"70\" height=\"70\" class=\"{base_class}_outline\" />")
        if stone["stone_type"] == "mine":
            stone_object.append(f"      <path d=\"M45,15 L45,25 A20,20,90,0,1,25,45 L15,45 A40,40,0,0,0,15,55 L25,55 A20,20,90,0,1,45,75 L45,85 A40,40,0,0,0,55,85 L55,75 A20,20,90,0,1,75,55 L85,55 A40,40,0,0,0,85,45 L75,45 A20,20,90,0,1,55,25 L55,15 A40,40,0,0,0, 45,15 Z\" class=\"{base_class}_body\" /> ")
            stone_object.append(f"      <circle cx=\"50\" cy=\"50\" r=\"8\" class=\"{base_class}_button\" />")


        stone_object.append("    </g>")
        stone_object.append("  </g>")
        stone_object.append("</g>")
        return(stone_object)

    def create_base(self, base, special_id = None, special_id_display="none", special_id_onclick=None):
        base_class = f"base_{base["faction"]}"
        if "x" in base.keys():
            base_x = base["x"] * self.board_square_base_side_length
            base_y = base["y"] * self.board_square_base_side_length
        else:
            base_x = 0
            base_y = 0
        base_object = []

        if special_id is not None:
            iden = f"{base_class}_{special_id}"
            if special_id_onclick is None:
                base_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class} {special_id}\" id=\"{base_class}_{special_id}\" transform-origin=\"50px 50px\" style=\"display:{special_id_display}; pointer-events:none; transform:translate({base_x}px,{base_y}px)\">")
            else:
                base_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class} {special_id}\" id=\"{base_class}_{special_id}\" transform-origin=\"50px 50px\" style=\"display:{special_id_display}; transform:translate({base_x}px,{base_y}px)\" onclick=\"{special_id_onclick}\">")
        else:
            iden = self.encode_base_ID(base)
            base_object.append(f"<g x=\"0\" y=\"0\" width=\"100\" height=\"100\" class=\"{base_class}\" id=\"{iden}\" transform-origin=\"50px 50px\" style=\"pointer-events:none; transform:translate({base_x}px,{base_y}px)\">")

        base_object.append(f"  <circle cx=\"50\" cy=\"50\" r=\"25\" class=\"{base_class}_indicator\" id=\"{iden}_indicator\" />")
        base_object.append(f"</g>")
        return(base_object)


    def draw_stones(self):
        # These are drawn on the x=0,y=0 square with display:none, and will be
        # moved around by JavaScript using the 'transform' attrib1ute.
        self.board_layer_structure[4].append("<g id=\"group_stones\">")
        for stone in self.render_object["stones"]:
            self.board_layer_structure[4].append(self.create_stone(stone))
        self.board_layer_structure[4].append("</g>")

    def draw_bases(self):
        # Same principle as stones
        self.board_layer_structure[2].append("<g id=\"group_bases\">")
        for base in self.render_object["bases"]:
            self.board_layer_structure[2].append(self.create_base(base))
        self.board_layer_structure[2].append("</g>")

    def draw_square_highlighter(self):
        self.board_layer_structure[3].append(f"<polyline id=\"square_highlighter\" points=\"{self.get_polygon_points([[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]])}\" display=\"none\"/>")

    def draw_board(self):
        self.open_board_window()
        self.draw_templates()
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
        # This inspector is used for altering properties of placed bases and stones
        self.commit_to_output("<div id=\"stone_inspector\" class=\"inspector\">")
        self.commit_to_output("  <h1 id=\"stone_inspector_title\" class=\"inspector_title\"></h1>")
        self.commit_to_output("  <div id=\"stone_inspector_header\" class=\"stone_inspector_part\">")
        self.draw_inspector_table("stone", {"allegiance" : "Allegiance", "stone_type" : "Stone type"})
        self.draw_inspector_table("base", {"allegiance" : "Allegiance"})
        self.commit_to_output("  </div>")
        stone_inspector_object = []
        stone_inspector_object.append("  <div id=\"stone_inspector_commands\" class=\"stone_inspector_part\">")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"base_inspector_buttons_svg\" display=\"none\">")
        stone_inspector_object.append("      <g id=\"remove_base_button\">")
        stone_inspector_object.append("        <rect x=\"0\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"remove_base_button_polygon\" onclick=\"inspector.remove_base()\" />")
        stone_inspector_object.append("        <text x=\"50\" y=\"42\" text-anchor=\"middle\" id=\"remove_base_button_label\" class=\"button_label\">Remove</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"stone_inspector_buttons_svg\" display=\"none\">")
        stone_inspector_object.append("      <g id=\"remove_stone_button\">")
        stone_inspector_object.append("        <rect x=\"0\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"remove_stone_button_polygon\" onclick=\"inspector.remove_stone()\" />")
        stone_inspector_object.append("        <text x=\"50\" y=\"42\" text-anchor=\"middle\" id=\"remove_stone_button_label\" class=\"button_label\">Remove</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("      <g id=\"rotate_button\">")
        stone_inspector_object.append("        <rect x=\"110\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"rotate_button_polygon\" onclick=\"inspector.rotate_stone()\" />")
        stone_inspector_object.append("        <text x=\"160\" y=\"42\" text-anchor=\"middle\" class=\"button_label\">Rotate</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"selection_mode_abort_svg\" display=\"none\">")
        stone_inspector_object.append("      <g id=\"selection_mode_abort_button\">")
        stone_inspector_object.append("        <rect x=\"0\" y=\"0\" width=\"100\" height=\"83\" class=\"stone_command_panel_button\" id=\"selection_mode_abort_button_polygon\" onclick=\"inspector.turn_off_selection_mode()\" />")
        stone_inspector_object.append("        <text x=\"50\" y=\"42\" text-anchor=\"middle\" id=\"selection_mode_abort_button_label\" class=\"button_label\">Abort</text>")
        stone_inspector_object.append("      </g>")
        stone_inspector_object.append("    </svg>")
        stone_inspector_object.append("  </div>")
        if self.render_object["client_action"] == "edit":
            self.commit_to_output(stone_inspector_object)
        self.commit_to_output("</div>")

    def draw_board_dimensions_inspector(self):
        # This inspector is used for changing the static board dimensions

        self.commit_to_output("<div id=\"board_dimensions_inspector\" class=\"inspector\">")
        #self.commit_to_output("  <div id=\"board_dimensions_inspector_header\">")
        #self.commit_to_output("    <p id=\"board_dimensions_inspector_label\">No element selected</p>")
        #self.commit_to_output("  </div>")
        #self.commit_to_output(f"  <svg width=\"70%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"faction_inspector_svg\">")

        # Now the form for changing board dimensions (not a submit one, everything is handled clientside until board save)
        board_dimensions_edit_form = [
            f"<form id=\"board_dimensions_inspector_form\">",
            f"  <div id=\"board_dimensions_left_col\">",
            f"    <label for=\"board_dimensions_t_input\">Timeslices in round:</label>",
            f"    <input type=\"number\" id=\"board_dimensions_t_input\" name=\"board_dimensions_t_input\" value=\"{self.render_object["t_dim"]}\" min=\"3\" max=\"30\" onchange=\"toggle_board_dimensions_buttons()\">",
            f"    <label for=\"board_dimensions_x_input\">Squares horizontally:</label>",
            f"    <input type=\"number\" id=\"board_dimensions_x_input\" name=\"board_dimensions_x_input\" value=\"{self.render_object["x_dim"]}\" min=\"3\" max=\"30\" onchange=\"toggle_board_dimensions_buttons()\">",
            f"    <label for=\"board_dimensions_y_input\">Squares vertically:</label>",
            f"    <input type=\"number\" id=\"board_dimensions_y_input\" name=\"board_dimensions_y_input\" value=\"{self.render_object["y_dim"]}\" min=\"3\" max=\"30\" onchange=\"toggle_board_dimensions_buttons()\">",
            f"  </div>",
            f"  <div id=\"board_dimensions_right_col\">",
            f"    <input type=\"button\" id=\"board_dimensions_update_btn\" value=\"Update\" onclick=\"inspector.update_board_dimensions()\" hidden>",
            f"    <input type=\"button\" id=\"board_dimensions_reset_btn\" value=\"Reset\" onclick=\"reset_board_dimensions_form()\" hidden>",
            f"  </div>",
            f"</form>"
            ]
        if self.render_object["client_action"] == "edit":
            self.commit_to_output(board_dimensions_edit_form)

        #self.commit_to_output("  </svg>")
        self.commit_to_output("</div>")


    def draw_square_inspector(self):
        # This inspector is used for altering square types
        square_inspector_object = []
        self.commit_to_output("<div id=\"square_inspector\" class=\"inspector\">")
        self.commit_to_output("  <h1 id=\"square_inspector_title\" class=\"inspector_title\"></h1>")

        square_inspector_object.append("    <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"square_inspector_buttons_svg\">")
        x_offset = 0
        button_width = 150
        for board_square_symbol, board_square_label in self.board_squares_info_data.items():
            square_inspector_object.append(f"      <g id=\"change_square_to_{board_square_label}\" display=\"none\">")
            square_inspector_object.append(f"        <rect x=\"{x_offset}\" y=\"0\" width=\"{button_width}\" height=\"83\" class=\"stone_command_panel_button\" id=\"change_square_to_{board_square_label}_polygon\" onclick=\"inspector.change_square_type(\'{board_square_symbol}\')\" />")
            square_inspector_object.append(f"        <text x=\"{int(x_offset + button_width / 2)}\" y=\"42\" text-anchor=\"middle\" id=\"change_square_to_{board_square_label}_label\" class=\"button_label\">Change to {board_square_label}</text>")
            square_inspector_object.append(f"      </g>")
        square_inspector_object.append("    </svg>")

        if self.render_object["client_action"] == "edit":
            self.commit_to_output(square_inspector_object)

        self.commit_to_output("</div>")

    def draw_inspectors(self):
        self.open_inspectors()
        self.draw_stone_inspector()
        self.draw_board_dimensions_inspector()
        self.draw_square_inspector()
        self.close_inspectors()

    # ---------------------- Game control panel methods -----------------------

    def draw_element_input_panel(self):
        # game control panel allows one to place new elements onto the boards. Each element is represented by an icon.
        self.commit_to_output("<div id=\"element_input_panel\">")
        self.draw_base_input_section()
        self.draw_neutral_stone_input_section()
        self.draw_stone_input_section()
        self.commit_to_output("</div>")

    def draw_base_input_section(self):
        self.commit_to_output([
            "  <div id=\"element_input_panel_base_section\">",
            "    <svg xmlns=\"http://www.w3.org/2000/svg\" id=\"element_input_panel_base_section_svg\">"
            ])
        input_icon_index = 0
        for allegiance in ["neutral", "A", "B"]:
            self.commit_to_output(self.create_base({"faction" : allegiance, "x" : input_icon_index, "y" : 0}, "input_icon", "block", f"inspector.select_input_element(\'base\', \'{allegiance}\', null)"))
            input_icon_index += 1
        self.commit_to_output([
            "    </svg>",
            "  </div>"
            ])

    def draw_neutral_stone_input_section(self):
        self.commit_to_output([
            "  <div id=\"element_input_panel_neutral_stone_section\">",
            "    <svg xmlns=\"http://www.w3.org/2000/svg\" id=\"element_input_panel_neutral_stone_section_svg\">"
            ])
        input_icon_index = 0
        for stone_type in self.required_stone_types["GM"]:
            self.commit_to_output(self.create_stone({"faction" : "GM", "stone_type" : stone_type, "x" : input_icon_index, "y" : 0}, "input_icon", "block", f"inspector.select_input_element(\'stone\', \'GM\', \'{stone_type}\')"))
            input_icon_index += 1
        self.commit_to_output([
            "    </svg>",
            "  </div>"
            ])

    def draw_stone_input_section(self):
        self.commit_to_output([
            "  <div id=\"element_input_panel_stone_section\">",
            "    <svg xmlns=\"http://www.w3.org/2000/svg\" id=\"element_input_panel_stone_section_svg\">"
            ])
        allegiance_index = 0
        for allegiance in ["A", "B"]:
            input_icon_index = 0
            for stone_type in self.required_stone_types[allegiance]:
                self.commit_to_output(self.create_stone({"faction" : allegiance, "stone_type" : stone_type, "x" : input_icon_index, "y" : allegiance_index}, "input_icon", "block", f"inspector.select_input_element(\'stone\', \'{allegiance}\', \'{stone_type}\')"))
                input_icon_index += 1
            allegiance_index += 1
        self.commit_to_output([
            "    </svg>",
            "  </div>"
            ])


    # ------------------------- Command form methods --------------------------

    def draw_board_edit_form(self):
        board_edit_form = []
        board_edit_form.append(f"<div id=\"board_edit_form_div\">")
        if self.render_object["client_action"] == "edit":
            board_edit_form.append(f"  <form id=\"board_edit_form\" class=\"submission_form\" action=\"{url_for("board.board_edit_submission", board_id=self.board_id)}\" method=\"POST\">")
            # ------------------------ Invisible elements -------------------------
            # Fieldset Header: t_dim, x_dim, y_dim, total number of bases/stones
            board_edit_form.append(f"    <fieldset id=\"header_data\" class=\"board_edit_data_field\">")
            board_edit_form.append(f"      <input type=\"hidden\" name=\"h_t_dim\" id=\"h_t_dim\" value=\"{self.render_object["t_dim"]}\">")
            board_edit_form.append(f"      <input type=\"hidden\" name=\"h_x_dim\" id=\"h_x_dim\" value=\"{self.render_object["x_dim"]}\">")
            board_edit_form.append(f"      <input type=\"hidden\" name=\"h_y_dim\" id=\"h_y_dim\" value=\"{self.render_object["y_dim"]}\">")
            board_edit_form.append(f"      <input type=\"hidden\" name=\"h_number_of_bases\" id=\"h_number_of_bases\" value=\"{len(self.render_object["bases"])}\">")
            board_edit_form.append(f"      <input type=\"hidden\" name=\"h_number_of_stones\" id=\"h_number_of_stones\" value=\"{len(self.render_object["stones"])}\">")
            board_edit_form.append(f"    </fieldset>")
            # Fieldset Squares: For each square its type
            board_edit_form.append(f"    <fieldset id=\"squares_data\" class=\"board_edit_data_field\">")
            for y in range(self.render_object["y_dim"]):
                for x in range(self.render_object["x_dim"]):
                    board_edit_form.append(f"      <input type=\"hidden\" name=\"square_{x}_{y}\" id=\"square_{x}_{y}\" value=\"{self.render_object["board_static"][x][y]}\">")
            board_edit_form.append(f"    </fieldset>")
            # Fieldset Bases: For each base its position and allegiance
            board_edit_form.append(f"    <fieldset id=\"bases_data\" class=\"board_edit_data_field\">")
            for base_i in range(len(self.render_object["bases"])):
                for kw in self.element_keywords["bases"]:
                    board_edit_form.append(f"      <input type=\"hidden\" name=\"base_{base_i}_{kw}\" id=\"base_{base_i}_{kw}\" value=\"{self.render_object["bases"][base_i][kw]}\" >")
            board_edit_form.append(f"    </fieldset>")
            # Fieldset Stones: For each stone its allegiance, type, position, and azimuth
            board_edit_form.append(f"    <fieldset id=\"stones_data\" class=\"board_edit_data_field\">")
            for stone_i in range(len(self.render_object["stones"])):
                for kw in self.element_keywords["stones"]:
                    board_edit_form.append(f"      <input type=\"hidden\" name=\"stone_{stone_i}_{kw}\" id=\"stone_{stone_i}_{kw}\" value=\"{self.render_object["stones"][stone_i][kw]}\" >")
            board_edit_form.append(f"    </fieldset>")

            # ------------------------- Visible elements --------------------------
            board_edit_form.append(f"    <input type=\"text\" name=\"board_name\" id=\"board_name\" required value=\"{self.render_object["board_name"]}\" >")


            board_edit_form.append(f"    <button type=\"submit\" name=\"board_submission\" value=\"submit\" id=\"save_board_button\">Save board</button>")
            board_edit_form.append(f"  </form>")
        else:
            # Link to author
            board_edit_form.append(f"  <a href=\"{url_for("user.user", username = self.render_object["author"])}\" target=\"_blank\" class=\"action_table_col_link\">{ self.render_object["author"] }</a>")
        board_edit_form.append(f"</div>")
        self.commit_to_output(board_edit_form)

    # ---------------------------- Cursor overlay -----------------------------

    def create_cursor_overlay(self):
        self.commit_to_output("<div id=\"cursor_overlay\">")
        self.commit_to_output("  <svg width=\"100%\" height=\"100%\" xmlns=\"http://www.w3.org/2000/svg\" id=\"cursor_overlay_svg\">")


        for allegiance in ["neutral", "A", "B"]:
            self.commit_to_output(self.create_base({"faction" : allegiance}, "input_icon_shadow", ""))
        for allegiance in self.required_stone_types.keys():
            for stone_type in self.required_stone_types[allegiance]:
                self.commit_to_output(self.create_stone({"faction" : allegiance, "stone_type" : stone_type}, "input_icon_shadow", ""))

        self.commit_to_output("  </svg>")
        self.commit_to_output("</div>")

    # --------------------------- guest info table ----------------------------

    def draw_gameside_info_table(self):
        self.commit_to_output([
            f"  <table id=\"gameside_info_table\" class=\"action_table\">",
            f"    <thead>",
            f"      <tr>",
            f"        <th class=\"action_table_header\">Board name</th>",
            f"        <th class=\"action_table_header\">Author</th>",
            f"        <th class=\"action_table_header\">Timeslices</th>",
            f"        <th class=\"action_table_header\">Width</th>",
            f"        <th class=\"action_table_header\">Height</th>",
            f"        <th class=\"action_table_header\"># of games played on board</th>",
            f"        <th class=\"action_table_header\"># of users who saved board</th>",
            f"        <th class=\"action_table_header\">Handicap</th>",
            f"        <th class=\"action_table_header\">Draw prob.</th>",
            f"        <th class=\"action_table_header\">Published</th>",
            f"        <th colspan=\"1\" class=\"action_table_actions_header\">Actions</th>",
            f"      </tr>",
            f"    </thead>",
            f"    <tbody>",
            f"      <tr>",
            f"        <td>{self.render_object["board_name"]}</td>",
            f"        <td><a href=\"{url_for("user.user", username = self.render_object["author"])}\" target=\"_blank\" class=\"action_table_col_link\">{ self.render_object["author"] }</a></td>",
            f"        <td>{self.render_object["t_dim"]}</td>",
            f"        <td>{self.render_object["x_dim"]}</td>",
            f"        <td>{self.render_object["y_dim"]}</td>",
            f"        <td>{self.render_object["games_played"]}</td>",
            f"        <td>{self.render_object["saved_by"]}</td>",
            f"        <td>{self.render_object["handicap"]}</td>",
            f"        <td>{self.render_object["p_draw"]}</td>",
            f"        <td>{self.render_object["d_published"]}</td>",
            f"        <td><button type=\"submit\" name=\"action_game_management_table\" value=\"save_board\" class=\"action_game_management_submit_btn action_table_column_button\">Save board</button></td>",
            f"      </tr>",
            f"    </tbody>",
            f"  </table>"
            ])


    # ---------------------------- Global methods -----------------------------

    def render_board(self):
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

        if self.render_object["client_action"] == "edit":
            self.draw_element_input_panel()
            self.draw_board_edit_form() # Don't draw this if board is just for viewing!
        else:
            self.draw_gameside_info_table()

        # Close gameside
        self.close_gameside()

        # cursor overlay
        self.create_cursor_overlay()

        self.close_body()


