# This is a class to make complicated html forms
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.html_objects.html_object import HTMLObject
from batil.html_objects.action_table import ActionTable

from batil.db import get_db, get_table_as_list_of_dicts

class ActionForm(HTMLObject):

    # static methods

    id_generator = 0
    def generate_id():
        ActionForm.id_generator += 1
        return(ActionForm.id_generator - 1)

    def get_args(action_form_id, persistive_selections = []):
        result_get_args = {}
        if f"action_form_{action_form_id}_open_sec" in request.form:
            action_form_section_val = int(request.form.get(f"action_form_{action_form_id}_open_sec"))
            result_get_args[f"action_form_{action_form_id}_open_sec"] = action_form_section_val
        # If "action_{id}" is not in the form, then the selection was not submitted, and should be preserved
        if f"action_{action_form_id}" not in request.form:
            for action_table_id in persistive_selections:
                result_get_args[f"action_table_{action_table_id}_cur_sel"] = request.form.get(f"action_table_{action_table_id}_selected_row")
        else:
            # We reset the open sec!
            result_get_args[f"action_form_{action_form_id}_open_sec"] = 0
        return(result_get_args)

    # instance methods

    def __init__(self, identifier, form_title, blueprint, method = "post", allow_file_encoding = False, **kwargs):
        super().__init__()
        self.identifier = identifier
        self.form_title = form_title
        self.blueprint = blueprint # To create the url for action
        self.action_url = url_for(f"{self.blueprint}.action_{self.identifier}", **kwargs)
        self.cls = "action_form"

        self.number_of_tabs = 0

        if allow_file_encoding:
            encoding_str = "enctype=\"multipart/form-data\""
        else:
            encoding_str = ""

        self.structured_html.append([
            f"<div id=\"action_form_{self.identifier}_container\" class=\"action_form_container\">",
            f"<form id=\"action_form_{self.identifier}\" method=\"{method}\" action=\"{self.action_url}\" {encoding_str}>",
            f"  <button type=\"submit\" name=\"action_{self.identifier}_nav\" value=\"refresh\" hidden></button>" # automatic refresh on Enter press
            ])

        self.last_section_opened = None

    def initialise_tabs(self, list_of_tabs):
        # list_of_tabs is the list of HR names
        self.number_of_tabs = len(list_of_tabs)

        # if list_of_tabs is longer than 1, we include a hidden input for remembering the open tab
        self.action_form_section_val = 0
        if len(list_of_tabs) > 1:
            # if value exists in GET, we read off the value here
            if f"action_form_{self.identifier}_open_sec" in request.args:
                self.action_form_section_val = int(request.args.get(f"action_form_{self.identifier}_open_sec"))
            self.structured_html.append(f"  <input type=\"hidden\" name=\"action_form_{self.identifier}_open_sec\" id=\"action_form_{self.identifier}_open_sec\" value=\"{self.action_form_section_val}\">")

        self.structured_html.append("<div class=\"action_form_tabs\">")
        for i in range(len(list_of_tabs)):
            if i == self.action_form_section_val:
                cur_class = "action_form_tab active"
            else:
                cur_class = "action_form_tab"
            self.structured_html.append(f"  <div id=\"action_form_{self.identifier}_tab_{i}\" class=\"{cur_class}\" onclick=\"action_form_{self.identifier}_select({i})\">{list_of_tabs[i]}</div>")


        # Form title
        self.structured_html.append([
                f"  <div id=\"action_form_{self.identifier}_form_title_div\" class=\"action_form_title\">",
                f"    <span id=\"action_form_{self.identifier}_form_title_span\">{self.form_title}</span>",
                f"  </div>"
            ])
        self.structured_html.append([
            "</div>",
            f"<div class=\"action_form_section_container\">"
            ])

        self.tab_structure_html = []
        self.tab_properties = []
        for i in range(len(list_of_tabs)):
            self.tab_structure_html.append({"content" : []})
            self.tab_properties.append({})

    def add_to_tab(self, tab_index, key, content):
        # tab_index is 0 ... len(list_of_tabs) - 1
        # key is "header", "content", or "footer"
        # content is structured html
        if tab_index < 0 or tab_index >= self.number_of_tabs:
            return(-1)
        if key not in self.tab_structure_html[tab_index]:
            self.tab_structure_html[tab_index][key] = [content]
        else:
            self.tab_structure_html[tab_index][key].append(content)

    def set_tab_property(self, tab_index, key, value):
        # selection_condition: tab only shows up if a given element's value is non-empty
        # ignore_padding: if true, ignores padding of section_content
        if tab_index < 0 or tab_index >= self.number_of_tabs:
            return(-1)
        self.tab_properties[tab_index][key] = value

    def realise_form(self):
        # adds the tab contents to the structured html, adds tab-switching scripts and closes form
        for section_i in range(self.number_of_tabs):
            self.structured_html.append(f"  <div id=\"action_form_{self.identifier}_section_{section_i}\" class=\"action_form_section\">")
            for kw in ["header", "content", "footer"]:
                if kw in self.tab_structure_html[section_i]:
                    if kw == "content" and "ignore_padding" in self.tab_properties[section_i]:
                        self.structured_html.append(f"    <div class=\"action_form_section_content_no_padding\">")
                    else:
                        self.structured_html.append(f"    <div class=\"action_form_section_{kw}\">")
                    self.structured_html.append(self.tab_structure_html[section_i][kw])
                    self.structured_html.append(f"    </div>")
            self.structured_html.append("  </div>")

            if "selection_condition" in self.tab_properties[section_i]:
                tab_id = f"action_form_{self.identifier}_tab_{section_i}"
                self.structured_html.append([
                        "  <script>",
                        f"  if (document.getElementById({json.dumps(self.tab_properties[section_i]["selection_condition"])}).value == \"\") {{",
                        f"    document.getElementById({json.dumps(tab_id)}).style.display = \"none\";",
                        f"  }}",
                        f"  document.getElementById({json.dumps(self.tab_properties[section_i]["selection_condition"])}).addEventListener(\"change\", function(){{",
                        f"    if (this.value == \"\") {{",
                        f"      document.getElementById({json.dumps(tab_id)}).style.display = \"none\";",
                        f"    }} else {{",
                        f"      document.getElementById({json.dumps(tab_id)}).style.display = \"block\";",
                        f"    }}",
                        f"  }});",
                        "  </script>"
                    ])
        self.close_form()

    def close_form(self):
        self.structured_html.append([
            "</div>",
            "</form>",
            "</div>"
            ])
        # Now for the script specific to this form
        self.structured_html.append([
                "<script>",
                f"  function action_form_{self.identifier}_select(idx) {{",
                f"    const number_of_tabs = {self.number_of_tabs};",
                f"    for (let i = 0; i < number_of_tabs; i++) {{",
                f"      document.getElementById(`action_form_{self.identifier}_tab_${{i}}`).classList.toggle('active', i === idx);",
                f"      document.getElementById(`action_form_{self.identifier}_section_${{i}}`).classList.toggle('active', i === idx);"])
        if self.number_of_tabs > 1:
            self.structured_html.append(f"      document.getElementById(`action_form_{self.identifier}_open_sec`).value = idx;")
        self.structured_html.append([
                f"    }}",
                f"  }}",
                f"  action_form_{self.identifier}_select({self.action_form_section_val});",
                "</script>"
            ])

    # ----------------- Little HTML elements --------------------

    def add_button(self, section_i, btn_type, btn_value, btn_description, btn_id = None, btn_class = "action_form_button", selection_condition = None):
        button_html = []
        if selection_condition is not None and btn_id is None:
            # We need to generate an ID!
            btn_id = f"action_form_{self.identifier}_btn_{ActionForm.generate_id()}"
        if btn_id is not None:
            button_html.append(f"<button type=\"{btn_type}\" name=\"action_{self.identifier}\" value=\"{btn_value}\" id=\"{btn_id}\" class=\"{btn_class}\">{btn_description}</button>")
        else:
            button_html.append(f"<button type=\"{btn_type}\" name=\"action_{self.identifier}\" value=\"{btn_value}\" class=\"{btn_class}\">{btn_description}</button>")
        if selection_condition is not None:
            # The button is only displayed if the HTML element with id selection_condition has "value" attribute equal to a non-empty string
            button_html.append([
                    "<script>",
                    f"if (document.getElementById({json.dumps(selection_condition)}).value == \"\") {{",
                    f"  document.getElementById({json.dumps(btn_id)}).disabled = true;",
                    f"}}",
                    f"document.getElementById({json.dumps(selection_condition)}).addEventListener(\"change\", function(){{",
                    f"  if (this.value == \"\") {{",
                    f"    document.getElementById({json.dumps(btn_id)}).disabled = true;",
                    f"  }} else {{",
                    f"    document.getElementById({json.dumps(btn_id)}).disabled = false;",
                    f"  }}",
                    f"}});",
                    "</script>"
                ])
        self.add_to_tab(section_i, "footer", button_html)

    def add_ordered_table(self, section_i, table_id, table_query, data_identifier, data_cols, include_select, headers, order_options, actions = None, filters = None, action_instructions = {}, col_links = {}, rows_per_view = 10, enforce_filter_kw = None, row_class_by_col = None):
        # Call this after open_section. This also opens section footer, so there can only be this table in the content of this section
        # The ordering and navigation are done through the GET form!

        # order_options = [["QUERY FRAGMENT", "label"], ...]

        main_table = ActionTable(table_id, include_select)
        main_table.make_head(headers, actions, action_instructions, col_links)

        if f"{table_id}_order" in request.args:
            try:
                main_table_order_value = request.args.get(f"{table_id}_order")
                main_table_order = order_options[int(request.args.get(f"{table_id}_order"))][0]
            except:
                main_table_order_value = "0"
                main_table_order = order_options[0][0]
        else:
            main_table_order_value = "0"
            main_table_order = order_options[0][0]

        if f"{table_id}_dir" in request.args:
            if request.args.get(f"{table_id}_dir") == "A":
                main_table_dir_value = "A"
                main_table_dir = "ASC"
            else:
                main_table_dir_value = "D"
                main_table_dir = "DESC"
        else:
            main_table_dir_value = "D"
            main_table_dir = "DESC"

        if f"{table_id}_page" in request.args:
            try:
                main_table_page_value = request.args.get(f"{table_id}_page")
                main_table_page = int(request.args.get(f"{table_id}_page"))
            except:
                main_table_page_value = "0"
                main_table_page = 0
        else:
            main_table_page_value = "0"
            main_table_page = 0

        filter_clause = ""
        filter_subclauses = []
        if enforce_filter_kw is not None:
            filter_clause = f" {enforce_filter_kw} ("
        else:
            if "GROUP BY" in table_query:
                filter_clause = " HAVING ("
            else:
                if "WHERE" in table_query:
                    filter_clause = " AND ("
                else:
                    filter_clause = " WHERE ("
        if isinstance(filters, bool):
            if filters:
                for col_id in headers.keys():
                    filter_value = request.args.get(f"filter_{table_id}_{col_id}")
                    if filter_value is not None:
                        filter_subclauses.append(f"{col_id} LIKE %{filter_value}%")
                filter_clause += " AND ".join(filter_subclauses)
                filter_clause += ")"
        elif filters is not None:
            for col_id in filters:
                filter_value = request.args.get(f"filter_{table_id}_{col_id}")
                if filter_value is not None:
                    filter_subclauses.append(f"{col_id} LIKE \'%{filter_value}%\'")
            filter_clause += " AND ".join(filter_subclauses)
            filter_clause += ")"

        if len(filter_subclauses) == 0:
            filter_clause = ""

        main_table_data = get_table_as_list_of_dicts(f"{table_query}{filter_clause} ORDER BY {main_table_order} {main_table_dir} LIMIT {rows_per_view} OFFSET {main_table_page * rows_per_view}", data_identifier, data_cols)
        main_table_next_page_data = get_table_as_list_of_dicts(f"{table_query}{filter_clause} ORDER BY {main_table_order} {main_table_dir} LIMIT 1 OFFSET {(main_table_page + 1) * rows_per_view}", data_identifier, data_cols)
        main_table_next_page = (len(main_table_next_page_data) > 0)

        current_filter_values = {}
        if isinstance(filters, bool):
            if filters:
                for col_id in headers.keys():
                    if f"filter_{table_id}_{col_id}" in request.args:
                        current_filter_values[col_id] = request.args.get(f"filter_{table_id}_{col_id}")
        elif filters is not None:
            for col_id in filters:
                if f"filter_{table_id}_{col_id}" in request.args:
                    current_filter_values[col_id] = request.args.get(f"filter_{table_id}_{col_id}")

        main_table.make_body(main_table_data, filters, current_filter_values, row_class_by_col)

        self.add_to_tab(section_i, "content", main_table.structured_html)

        order_form = []
        order_form.append(f"  <input type=\"hidden\" name=\"{table_id}_order\" value=\"{main_table_order_value}\">")
        order_form.append(f"  <input type=\"hidden\" name=\"{table_id}_dir\" value=\"{main_table_dir_value}\">")
        order_form.append(f"  <input type=\"hidden\" name=\"{table_id}_page\" value=\"{main_table_page_value}\">")

        # Now for the buttons. Non-relevant buttons are still rendered, but disabled

        # order options
        if len(order_options) > 0:
            order_form.append(f"<span class=\"action_form_button_label\">Order by</span>")
        for order_i in range(len(order_options)):
            if str(order_i) == main_table_order_value:
                order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_order\" value=\"{order_i}\" id=\"{table_id}_order_{order_options[order_i][0]}\" class=\"action_form_button\" disabled>{order_options[order_i][1]}</button>")
            else:
                order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_order\" value=\"{order_i}\" id=\"{table_id}_order_{order_options[order_i][0]}\" class=\"action_form_button\">{order_options[order_i][1]}</button>")

        # ordering direction options
        if len(order_options) > 0:
            order_form.append(f"<span class=\"action_form_button_label\">Order dir.</span>")
        if main_table_dir_value == "A":
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"D\" id=\"{table_id}_dir_D\" class=\"action_form_button\">Desc.</button>")
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"A\" id=\"{table_id}_dir_A\" class=\"action_form_button\" disabled>Asc.</button>")
        else:
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"D\" id=\"{table_id}_dir_D\" class=\"action_form_button\" disabled>Desc.</button>")
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"A\" id=\"{table_id}_dir_A\" class=\"action_form_button\">Asc.</button>")

        # page navigation options (top, prev., next)
        order_form.append(f"<span class=\"action_form_button_label\">Nav.</span>")
        if main_table_page_value == "0":
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_page\" value=\"top\" id=\"{table_id}_page_top\" class=\"action_form_button\" disabled>Top</button>")
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_page\" value=\"prev\" id=\"{table_id}_page_prev\" class=\"action_form_button\" disabled>Prev</button>")
        else:
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_page\" value=\"top\" id=\"{table_id}_page_top\" class=\"action_form_button\">Top</button>")
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_page\" value=\"prev\" id=\"{table_id}_page_prev\" class=\"action_form_button\">Prev</button>")

        if main_table_next_page:
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_page\" value=\"next\" id=\"{table_id}_page_next\" class=\"action_form_button\">Next</button>")
        else:
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_page\" value=\"next\" id=\"{table_id}_page_next\" class=\"action_form_button\" disabled>Next</button>")

        order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_refresh\" value=\"refresh\" id=\"{table_id}_refresh\" class=\"action_form_button\">Refresh</button>")

        self.add_to_tab(section_i, "header", order_form)
        self.set_tab_property(section_i, "ignore_padding", True)

    def add_game_archive(self, section_i, table_id, username, opponent_username = None, rows_per_view = 8):
        # A special ordered_table which does the OPPONENT thing and also highlights rows with green/red based on whether USERNAME won the match
        # If opponent_username is specified, only the matches between the two users are included

        if opponent_username is None:
            table_query = f"""
                SELECT BOC_GAMES.GAME_ID AS GAME_ID, BOC_GAMES.D_STARTED AS D_STARTED, BOC_GAMES.D_FINISHED AS D_FINISHED, BOC_GAMES.BOARD_ID AS BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME,
                    CASE
                        WHEN BOC_GAMES.PLAYER_A = {json.dumps(username)} THEN BOC_GAMES.PLAYER_B
                        ELSE BOC_GAMES.PLAYER_A
                    END AS OPPONENT,
                    CASE
                        WHEN BOC_GAMES.PLAYER_A = {json.dumps(username)} THEN \"A\"
                        ELSE \"B\"
                    END AS PLAYER_ROLE,
                    CASE
                        WHEN BOC_GAMES.OUTCOME = \"draw\" THEN \"draw\"
                        WHEN ((BOC_GAMES.PLAYER_A = {json.dumps(username)} AND BOC_GAMES.OUTCOME = \"A\") OR (BOC_GAMES.PLAYER_B = {json.dumps(username)} AND BOC_GAMES.OUTCOME = \"B\")) THEN \"win\"
                        ELSE \"loss\"
                    END AS POV_OUTCOME
                FROM BOC_GAMES INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID
                WHERE (BOC_GAMES.PLAYER_A = {json.dumps(username)} OR BOC_GAMES.PLAYER_B = {json.dumps(username)})
                    AND BOC_GAMES.STATUS = \"concluded\"
            """
            data_identifier = "GAME_ID"
            data_cols = ["OPPONENT", "POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED", "BOARD_ID"]
            headers = {"OPPONENT" : "Opponent", "POV_OUTCOME" : "Outcome", "BOARD_NAME" : "Board", "PLAYER_ROLE": "Role", "D_STARTED" : "Started", "D_FINISHED" : "Finished"}
            order_options = [["D_FINISHED", "Finished"]]
            actions = {"view_game" : "Game", "view_board" : "Board", "view_opponent" : "Opponent"}
            filters = ["OPPONENT", "POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED"]
            action_instructions = {
                "view_game" : {"type" : "link", "url_func" : (lambda datum : url_for("game_bp.game", game_id = datum["IDENTIFIER"]))},
                "view_board" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"]))},
                "view_opponent" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["OPPONENT"]))}
                }
            col_links = {
                "OPPONENT" : (lambda datum : url_for("user.user", username = datum["OPPONENT"])),
                "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"])),
                }

        else:
            table_query = f"""
                SELECT BOC_GAMES.GAME_ID AS GAME_ID, BOC_GAMES.D_STARTED AS D_STARTED, BOC_GAMES.D_FINISHED AS D_FINISHED, BOC_GAMES.BOARD_ID AS BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME,
                    CASE
                        WHEN BOC_GAMES.PLAYER_A = {json.dumps(username)} THEN \"A\"
                        ELSE \"B\"
                    END AS PLAYER_ROLE,
                    CASE
                        WHEN BOC_GAMES.OUTCOME = \"draw\" THEN \"draw\"
                        WHEN ((BOC_GAMES.PLAYER_A = {json.dumps(username)} AND BOC_GAMES.OUTCOME = \"A\") OR (BOC_GAMES.PLAYER_B = {json.dumps(username)} AND BOC_GAMES.OUTCOME = \"B\")) THEN \"win\"
                        ELSE \"loss\"
                    END AS POV_OUTCOME
                FROM BOC_GAMES INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID
                WHERE ((BOC_GAMES.PLAYER_A = {json.dumps(username)} AND BOC_GAMES.PLAYER_B = {json.dumps(opponent_username)}) OR (BOC_GAMES.PLAYER_B = {json.dumps(username)} AND BOC_GAMES.PLAYER_A = {json.dumps(opponent_username)}))
                    AND BOC_GAMES.STATUS = \"concluded\"
            """
            data_identifier = "GAME_ID"
            data_cols = ["POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED", "BOARD_ID"]
            headers = {"POV_OUTCOME" : "Outcome", "BOARD_NAME" : "Board", "PLAYER_ROLE": "Role", "D_STARTED" : "Started", "D_FINISHED" : "Finished"}
            order_options = [["D_FINISHED", "Finished"]]
            actions = {"view_game" : "Game", "view_board" : "Board"}
            filters = ["POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED"]
            action_instructions = {
                "view_game" : {"type" : "link", "url_func" : (lambda datum : url_for("game_bp.game", game_id = datum["IDENTIFIER"]))},
                "view_board" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"]))}
                }
            col_links = {
                "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"]))
                }

        self.add_ordered_table(section_i, table_id, table_query, data_identifier, data_cols, False, headers, order_options, actions, filters, action_instructions, col_links, rows_per_view, row_class_by_col = "POV_OUTCOME")


