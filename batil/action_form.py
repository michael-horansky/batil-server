# This is a class to make complicated html forms

from batil.html_object import HTMLObject

class ActionForm(HTMLObject):

    def __init__(self, identifier):
        super().__init__()
        self.identifier = identifier
        self.cls = "action_form"

        self.number_of_tabs = 0

        self.structured_html.append(f"<form id=\"action_form_{self.identifier}\">")

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
        self.structured_html.append("</div>")

    def open_section(self, ordinator):
        self.structured_html.append(f"<div id=\"action_form_{self.identifier}_section_{ordinator}\" class=\"action_form_section\">")

    def close_section(self):
        self.structured_html.append("</div>")

    def close_form(self):
        self.structured_html.append("</form>")
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





