# HTML table initialised from sql. This is meant to be included within a form

from batil.html_object import HTMLObject

class ActionTable(HTMLObject):

    def __init__(self, identifier, include_select = True):
        super().__init__()
        self.identifier = identifier
        self.include_select = include_select

        self.structured_html.append(f"<table id=\"action_table_{self.identifier}\" class=\"action_table\">")

    def make_head(self, headers, actions = None):
        # Both headers and actions are dictionaries in the form {id : name}
        self.headers = headers
        self.actions = actions
        self.structured_html.append([
                "  <thead>",
                "    <tr>",
            ])
        for iden, name in headers.items():
            self.structured_html.append(f"      <th>{name}</th>")
        """if self.include_select:
            self.structured_html.append(f"      <th>Select</th>")
        if actions is not None:
            for iden, name in actions.items():
                self.structured_html.append(f"      <th>{name}</th>")"""
        self.structured_html.append([
                "    </tr>",
                "  </thead>",
            ])

    def make_body(self, data):
        # data is a list of dictionaries, where each dictionary is in the form {header_id : row_value}.
        # Also, each row has to have a key called "IDENTIFIER", the value of which is a string which is a
        # valid partial SQL query, namely the WHERE condition for a SELECT query which selects this row.
        self.structured_html.append("  <tbody>")
        for datum in data:
            self.structured_html.append(f"    <tr data-rowid=\"{datum["IDENTIFIER"]}\">")
            for column_id in self.headers.keys():
                if self.include_select:
                    self.structured_html.append(f"      <td class=\"{self.identifier}_select_row_btn\" data-rowid=\"{ datum["IDENTIFIER"] }\">{ datum[column_id] }</td>")
                else:
                    self.structured_html.append(f"      <td>{ datum[column_id] }</td>")
            if self.include_select:
                self.structured_html.append([
                        "      <td>",
                        f"        <button type=\"button\" class=\"{self.identifier}_select_row_btn action_table_button\" data-rowid=\"{ datum["IDENTIFIER"] }\">Select</button>",
                        "      </td>"
                    ])
            if self.actions is not None:
                for iden, name in self.actions.items():
                    self.structured_html.append([
                            "      <td>",
                            f"        <button type=\"submit\" name=\"action\" value=\"{iden}\" class=\"{self.identifier}_submit_btn action_table_button\" data-rowid=\"{ datum["IDENTIFIER"] }\">{name}</button>",
                            "      </td>"
                        ])
            self.structured_html.append("    </tr>")
        self.structured_html.append("  </tbody>")

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
                f"  }});",
                "</script>"
            ])




