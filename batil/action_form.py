# This is a class to make complicated html forms
import json

from batil.html_object import HTMLObject

class ActionForm(HTMLObject):

    id_generator = 0
    def generate_id():
        ActionForm.id_generator += 1
        return(ActionForm.id_generator - 1)

    def __init__(self, identifier, form_title, method = "post"):
        super().__init__()
        self.identifier = identifier
        self.form_title = form_title
        self.cls = "action_form"

        self.number_of_tabs = 0

        self.structured_html.append(f"<form id=\"action_form_{self.identifier}\" method=\"{method}\">")

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
        self.structured_html.append("</div>")

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






