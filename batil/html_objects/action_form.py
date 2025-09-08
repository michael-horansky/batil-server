# This is a class to make complicated html forms
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.html_objects.html_object import HTMLObject
from batil.html_objects.action_table import ActionTable

from batil.db import get_db, get_table_as_list_of_dicts

class ActionForm(HTMLObject):

    id_generator = 0
    def generate_id():
        ActionForm.id_generator += 1
        return(ActionForm.id_generator - 1)

    def __init__(self, identifier, form_title, blueprint, method = "post"):
        super().__init__()
        self.identifier = identifier
        self.form_title = form_title
        self.blueprint = blueprint # To create the url for action
        self.action_url = url_for(f"{self.blueprint}.action_{self.identifier}")
        self.cls = "action_form"

        self.number_of_tabs = 0

        self.structured_html.append([
            f"<div id=\"action_form_{self.identifier}_container\" class=\"action_form_container\">",
            f"<form id=\"action_form_{self.identifier}\" method=\"{method}\" action=\"{self.action_url}\">",
            f"  <button type=\"submit\" name=\"action_{self.identifier}\" value=\"refresh\" hidden></button>" # automatic refresh on Enter press
            ])

        self.last_section_opened = None

    def initialise_tabs(self, list_of_tabs):
        # list_of_tabs is the list of HR names
        self.number_of_tabs = len(list_of_tabs)
        self.structured_html.append("<div class=\"action_form_tabs\">")
        for i in range(len(list_of_tabs)):
            if i == 0:
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

    def open_section(self, ordinator):
        self.structured_html.append(f"<div id=\"action_form_{self.identifier}_section_{ordinator}\" class=\"action_form_section\">")
        self.structured_html.append("  <div class=\"action_form_section_content\">")
        self.last_section_opened = ordinator

    def open_section_footer(self):
        # Close content, open footer. This is an optional element!
        self.structured_html.append([
                "  </div>",
                "  <div class=\"action_form_section_footer\">"
            ])

    def close_section(self, selection_condition = None):
        self.structured_html.append([
                "  </div>",
                "</div>"
            ])
        if selection_condition is not None:
            # The tab that just closed is only accessible when the element with selection_condition ID has non-empty value
            tab_id = f"action_form_{self.identifier}_tab_{self.last_section_opened}"
            self.structured_html.append([
                    "<script>",
                    f"if (document.getElementById({json.dumps(selection_condition)}).value == \"\") {{",
                    f"  document.getElementById({json.dumps(tab_id)}).style.display = \"none\";",
                    f"}}",
                    f"document.getElementById({json.dumps(selection_condition)}).addEventListener(\"change\", function(){{",
                    f"  if (this.value == \"\") {{",
                    f"    document.getElementById({json.dumps(tab_id)}).style.display = \"none\";",
                    f"  }} else {{",
                    f"    document.getElementById({json.dumps(tab_id)}).style.display = \"block\";",
                    f"  }}",
                    f"}});",
                    "</script>"
                ])


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
                f"      document.getElementById(`action_form_{self.identifier}_section_${{i}}`).classList.toggle('active', i === idx);",
                f"    }}",
                f"  }}",
                f"  action_form_{self.identifier}_select(0);",
                "</script>"
            ])

    # ----------------- Little HTML elements --------------------

    def add_button(self, btn_type, btn_value, btn_description, btn_id = None, btn_class = "action_form_button", selection_condition = None):
        if selection_condition is not None and btn_id is None:
            # We need to generate an ID!
            btn_id = f"action_form_{self.identifier}_btn_{ActionForm.generate_id()}"
        if btn_id is not None:
            self.structured_html.append(f"<button type=\"{btn_type}\" name=\"action_{self.identifier}\" value=\"{btn_value}\" id=\"{btn_id}\" class=\"{btn_class}\">{btn_description}</button>")
        else:
            self.structured_html.append(f"<button type=\"{btn_type}\" name=\"action_{self.identifier}\" value=\"{btn_value}\" class=\"{btn_class}\">{btn_description}</button>")
        if selection_condition is not None:
            # The button is only displayed if the HTML element with id selection_condition has "value" attribute equal to a non-empty string
            self.structured_html.append([
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

    def add_ordered_table(self, table_id, table_query, data_identifier, data_cols, include_select, headers, order_options, actions = None, filters = None, action_instructions = {}, rows_per_view = 10):
        # Call this after open_section. This also opens section footer, so there can only be this table in the content of this section
        # The ordering and navigation are done through the GET form!

        # order_options = [["QUERY FRAGMENT", "label"], ...]

        main_table = ActionTable(table_id, include_select)
        main_table.make_head(headers, actions, action_instructions)

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
        if isinstance(filters, bool):
            if filters:
                if "GROUP BY" in table_query:
                    filter_clause = " HAVING ("
                else:
                    if "WHERE" in table_query:
                        filter_clause = " AND ("
                    else:
                        filter_clause = " WHERE ("
                for col_id in headers.keys():
                    filter_value = request.args.get(f"filter_{table_id}_{col_id}")
                    if filter_value != "":
                        filter_subclauses.append(f"{col_id} LIKE %{filter_value}%")
                filter_clause += " AND ".join(filter_subclauses)
                filter_clause += ")"
        elif filters is not None:
            if "GROUP BY" in table_query:
                filter_clause = " HAVING ("
            else:
                if "WHERE" in table_query:
                    filter_clause = " AND ("
                else:
                    filter_clause = " WHERE ("
            for col_id in filters:
                filter_value = request.args.get(f"filter_{table_id}_{col_id}")
                if filter_value != "":
                    filter_subclauses.append(f"{col_id} LIKE \'%{filter_value}%\'")
            filter_clause += " AND ".join(filter_subclauses)
            filter_clause += ")"

        if len(filter_subclauses) == 0:
            filter_clause = ""

        main_table_data = get_table_as_list_of_dicts(f"{table_query}{filter_clause} ORDER BY {main_table_order} {main_table_dir} LIMIT {rows_per_view} OFFSET {main_table_page * rows_per_view}", data_identifier, data_cols)
        main_table_next_page_data = get_table_as_list_of_dicts(f"{table_query}{filter_clause} ORDER BY {main_table_order} {main_table_dir} LIMIT 1 OFFSET {(main_table_page + 1) * rows_per_view}", data_identifier, data_cols)
        main_table_next_page = (len(main_table_next_page_data) > 0)

        current_filter_values = {}
        for col_id in filters:
            if f"filter_{table_id}_{col_id}" in request.args:
                current_filter_values[col_id] = request.args.get(f"filter_{table_id}_{col_id}")

        main_table.make_body(main_table_data, filters, current_filter_values)

        self.structured_html.append(main_table.structured_html)

        self.open_section_footer()

        order_form = []
        order_form.append(f"  <input type=\"hidden\" name=\"{table_id}_order\" value=\"{main_table_order_value}\">")
        order_form.append(f"  <input type=\"hidden\" name=\"{table_id}_dir\" value=\"{main_table_dir_value}\">")
        order_form.append(f"  <input type=\"hidden\" name=\"{table_id}_page\" value=\"{main_table_page_value}\">")

        # Now for the buttons. Non-relevant buttons are still rendered, but disabled

        # order options
        for order_i in range(len(order_options)):
            if str(order_i) == main_table_order_value:
                order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_order\" value=\"{order_i}\" id=\"{table_id}_order_{order_options[order_i][0]}\" class=\"action_form_button\" disabled>{order_options[order_i][1]}</button>")
            else:
                order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_order\" value=\"{order_i}\" id=\"{table_id}_order_{order_options[order_i][0]}\" class=\"action_form_button\">{order_options[order_i][1]}</button>")

        # ordering direction options
        if main_table_dir_value == "A":
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"D\" id=\"{table_id}_dir_D\" class=\"action_form_button\">Desc.</button>")
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"A\" id=\"{table_id}_dir_A\" class=\"action_form_button\" disabled>Asc.</button>")
        else:
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"D\" id=\"{table_id}_dir_D\" class=\"action_form_button\" disabled>Desc.</button>")
            order_form.append(f"<button type=\"submit\" name=\"action_{table_id}_dir\" value=\"A\" id=\"{table_id}_dir_A\" class=\"action_form_button\">Asc.</button>")

        # page navigation options (top, prev., next)
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

        self.structured_html.append(order_form)





