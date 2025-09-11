# HTML table initialised from sql. This is meant to be included within a form

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.html_objects.html_object import HTMLObject

class ActionTable(HTMLObject):

    # static methods

    def get_navigation_keywords(table_id, list_of_filters = None):
        nav_keywords = {}
        if f"{table_id}_order" in request.form:
            table_order_val = request.form.get(f"{table_id}_order")
            table_dir_val = request.form.get(f"{table_id}_dir")
            try:
                table_page_val = int(request.form.get(f"{table_id}_page"))
            except:
                table_page_val = 0
            if f"action_{table_id}_page" in request.form:
                page_action = request.form.get(f"action_{table_id}_page")
                if page_action == "top":
                    table_page_val = 0
                if page_action == "prev":
                    table_page_val -= 1
                if page_action == "next":
                    table_page_val += 1
            # If the filters or ordering changed, the page resets to 0
            if f"action_{table_id}_order" in request.form:
                table_order_val = request.form.get(f"action_{table_id}_order")
                table_page_val = 0
            if f"action_{table_id}_dir" in request.form:
                table_dir_val = request.form.get(f"action_{table_id}_dir")
                table_page_val = 0

            nav_keywords[f"{table_id}_order"] = table_order_val
            nav_keywords[f"{table_id}_dir"] = table_dir_val
            nav_keywords[f"{table_id}_page"] = table_page_val

            # filters
            if list_of_filters is not None:
                for filter_kw in list_of_filters:
                    cur_filter_val = request.form.get(f"filter_{table_id}_{filter_kw}")
                    if cur_filter_val is None:
                        cur_filter_val = ""
                    nav_keywords[f"filter_{table_id}_{filter_kw}"] = cur_filter_val
        return(nav_keywords)

    # instance methods

    def __init__(self, identifier, include_select = True):
        super().__init__()
        self.identifier = identifier
        self.include_select = include_select

        self.structured_html.append(f"<table id=\"action_table_{self.identifier}\" class=\"action_table\">")

    def make_head(self, headers, actions = None, action_instructions = {}):
        # Both headers and actions are dictionaries in the form {id : name}
        self.headers = headers
        self.actions = actions
        self.action_instructions = action_instructions
        self.structured_html.append([
                "  <thead>",
                "    <tr>",
            ])
        for iden, name in headers.items():
            self.structured_html.append(f"      <th class=\"action_table_header\">{name}</th>")
        """if self.include_select:
            self.structured_html.append(f"      <th>Select</th>")
        if actions is not None:
            for iden, name in actions.items():
                self.structured_html.append(f"      <th>{name}</th>")"""
        if actions is None:
            actions_span = 0
        else:
            actions_span = len(actions)
        if self.include_select:
            actions_span += 1
        if actions_span > 0:
            self.structured_html.append(f"      <th colspan=\"{actions_span}\" class=\"action_table_actions_header\">Actions</th>")
        self.structured_html.append([
                "    </tr>",
                "  </thead>",
            ])

    def make_body(self, data, include_filters = False, filter_values = None, row_class_by_col = None):
        # data is a list of dictionaries, where each dictionary is in the form {header_id : row_value}.
        # Also, each row has to have a key called "IDENTIFIER", the value of which is a string which is a
        # valid partial SQL query, namely the WHERE condition for a SELECT query which selects this row.

        # include_filters = True (all columns), False (no filters), or list of column ids
        # filter_values = None or {col id : filter value}
        if filter_values is None:
            filter_values = {}
        self.structured_html.append("  <tbody>")
        for datum in data:
            if row_class_by_col is None:
                self.structured_html.append(f"    <tr data-rowid=\"{datum["IDENTIFIER"]}\">")
            else:
                self.structured_html.append(f"    <tr data-rowid=\"{datum["IDENTIFIER"]}\" class=\"{self.identifier}_row_{datum[row_class_by_col]}\">")
            for column_id in self.headers.keys():
                if self.include_select:
                    self.structured_html.append(f"      <td class=\"{self.identifier}_select_row_btn\" data-rowid=\"{ datum["IDENTIFIER"] }\">{ datum[column_id] }</td>")
                else:
                    self.structured_html.append(f"      <td>{ datum[column_id] }</td>")
            if self.include_select:
                self.structured_html.append([
                        "      <td>",
                        f"        <button type=\"button\" class=\"{self.identifier}_select_row_btn action_table_column_button\" data-rowid=\"{ datum["IDENTIFIER"] }\">Select</button>",
                        "      </td>"
                    ])
            if self.actions is not None:
                for iden, name in self.actions.items():
                    if iden in self.action_instructions.keys():
                        # Special type of button
                        if self.action_instructions[iden]["type"] == "link":
                            target_url = self.action_instructions[iden]["url_func"](datum)
                            self.structured_html.append([
                                    "      <td>",
                                    f"        <a href=\"{target_url}\" target=\"_blank\">",
                                    f"          <button type=\"button\" class=\"action_table_column_button\">{name}</button>",
                                    f"        </a>",
                                    "      </td>"
                                ])
                    else:
                        self.structured_html.append([
                                "      <td>",
                                f"        <button type=\"submit\" name=\"action_{self.identifier}\" value=\"{iden}\" class=\"{self.identifier}_submit_btn action_table_column_button\" data-rowid=\"{ datum["IDENTIFIER"] }\">{name}</button>",
                                "      </td>"
                            ])
            self.structured_html.append("    </tr>")
        self.structured_html.append("  </tbody>")

        if isinstance(include_filters, bool):
            if include_filters:
                # We include filters for every column
                self.structured_html.append("  <tfoot>")
                self.structured_html.append("    <tr>")
                for column_id, column_label in self.headers.items():
                    if column_id in filter_values.keys():
                        self.structured_html.append(f"      <td><input type=\"text\" name=\"filter_{self.identifier}_{column_id}\" id=\"filter_{self.identifier}_{column_id}\" placeholder=\"Filter for: {column_label}\" value=\"{filter_values[column_id]}\"></td>")
                    else:
                        self.structured_html.append(f"      <td><input type=\"text\" name=\"filter_{self.identifier}_{column_id}\" id=\"filter_{self.identifier}_{column_id}\" placeholder=\"Filter for: {column_label}\"></td>")
                self.structured_html.append("    </tr>")
                self.structured_html.append("  </tfoot>")
        elif include_filters is not None:
            # include_filters is a list of column ids which permit a filter
            self.structured_html.append("  <tfoot>")
            self.structured_html.append("    <tr>")
            for column_id, column_label in self.headers.items():
                if column_id in include_filters:
                    if column_id in filter_values.keys():
                        self.structured_html.append(f"      <td><input type=\"text\" name=\"filter_{self.identifier}_{column_id}\" id=\"filter_{self.identifier}_{column_id}\" placeholder=\"Filter for: {column_label}\" value=\"{filter_values[column_id]}\"></td>")
                    else:
                        self.structured_html.append(f"      <td><input type=\"text\" name=\"filter_{self.identifier}_{column_id}\" id=\"filter_{self.identifier}_{column_id}\" placeholder=\"Filter for: {column_label}\"></td>")
                else:
                    self.structured_html.append(f"      <td></td>")
            self.structured_html.append("    </tr>")
            self.structured_html.append("  </tfoot>")

        self.close_table() # automatic finalisation

    def close_table(self):
        # hidden input: row selection
        self.structured_html.append([
                "</table>",
                f"<input type=\"hidden\" name=\"action_table_{self.identifier}_selected_row\" id=\"action_table_{self.identifier}_selected_row_input\" value=\"\" autocomplete=\"off\">"
            ])

        # script for buttons
        self.structured_html.append([
                "<script>",
                f"  document.querySelectorAll('.{self.identifier}_select_row_btn').forEach(function(btn) {{",
                f"    btn.addEventListener('click', function() {{",
                f"      document.querySelectorAll('#action_table_{self.identifier} tbody tr').forEach(function(tr) {{",
                f"        tr.classList.remove('selected');",
                f"        tr.removeAttribute('data-selected');",
                f"      }});",
                f"      var rowId = btn.getAttribute('data-rowid');",
                f"      var selectedRow = document.querySelector('tr[data-rowid=\"' + rowId + '\"]');",
                f"      selectedRow.classList.add('selected');",
                f"      selectedRow.setAttribute('data-selected', 'true');",
                f"      document.getElementById('action_table_{self.identifier}_selected_row_input').value = rowId;",
                f"      document.getElementById('action_table_{self.identifier}_selected_row_input').dispatchEvent(new Event(\"change\"));",
                f"    }});",
                f"  }});",
                f"  document.querySelectorAll('.{self.identifier}_submit_btn').forEach(function(btn) {{",
                f"    btn.addEventListener('click', function(e) {{",
                f"      var rowId = btn.getAttribute('data-rowid');",
                f"      document.getElementById('action_table_{self.identifier}_selected_row_input').value = rowId;",
                f"      document.getElementById('action_table_{self.identifier}_selected_row_input').dispatchEvent(new Event(\"change\"));",
                f"      document.querySelectorAll('#action_table_{self.identifier} tbody tr').forEach(function(tr) {{",
                f"        tr.classList.remove('selected');",
                f"        tr.removeAttribute('data-selected');",
                f"      }});",
                f"      var selectedRow = document.querySelector('tr[data-rowid=\"' + rowId + '\"]');",
                f"      selectedRow.classList.add('selected');",
                f"      selectedRow.setAttribute('data-selected', 'true');",
                f"    }});",
                f"  }});"])
        # if the selection is specified in GET, we select now
        if f"action_table_{self.identifier}_cur_sel" in request.args:
            cur_sel = request.args.get(f"action_table_{self.identifier}_cur_sel")
            if cur_sel != "":
                self.structured_html.append([
                    f"      document.querySelectorAll('#action_table_{self.identifier} tbody tr').forEach(function(tr) {{",
                    f"        tr.classList.remove('selected');",
                    f"        tr.removeAttribute('data-selected');",
                    f"      }});",
                    f"      var rowId = {cur_sel};",
                    f"      var selectedRow = document.querySelector('tr[data-rowid=\"' + rowId + '\"]');",
                    f"      selectedRow.classList.add('selected');",
                    f"      selectedRow.setAttribute('data-selected', 'true');",
                    f"      document.getElementById('action_table_{self.identifier}_selected_row_input').value = rowId;",
                    f"      document.getElementById('action_table_{self.identifier}_selected_row_input').dispatchEvent(new Event(\"change\"));"
                    ])
        self.structured_html.append("</script>")




