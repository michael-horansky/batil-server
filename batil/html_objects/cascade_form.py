# A special html object for cascade selection
# Creates a form-group; has to be initialised within the context of a html form

import json

from batil.db import get_db, get_table_as_list_of_dicts

from batil.html_objects.html_object import HTMLObject

class CascadeForm(HTMLObject):

    def __init__(self, identifier, groups, elements):
        super().__init__()
        self.identifier = identifier

        # groups is a list of dicts, where each dict is {"ID", "DESCRIPTION", "ORDER"}
        self.groups = groups # we assume the list is ordered by ORDER
        # elements is a list of dicts, where each dict is {"ID", "GROUP", "DESCRIPTION", "ORDER", "RESTRICTION", "REQUIREMENT", "LABEL"}
        self.elements = elements

        self.elements_by_group = {}
        for group in self.groups:
            self.elements_by_group[group["ID"]] = []
            for element in self.elements:
                if element["GROUP"] == group["ID"]:
                    self.elements_by_group[group["ID"]].append(element)
            # Now we order the elements in each group
            self.elements_by_group[group["ID"]].sort(key=lambda x : x["ORDER"])

        self.make_selector()

    def make_selector(self):
        self.structured_html.append(f"<div class=\"cascade_form_wrapper\" id=\"cascade_form_{self.identifier}_wrapper\">")
        # Firstly, we make a form group for every rulegroup
        default_restriction = "" # restriction imposed by the default element
        for group in self.groups:
            self.structured_html.append([
                    f"<div id=\"cascade_form_{self.identifier}_selection_group_{group["ID"]}\" class=\"cascade_form_selection_group\">",
                    f"  <label for=\"cascade_form_{self.identifier}_selection_group_{group["ID"]}_select\" class=\"cascade_form_label\">{group["DESCRIPTION"]}</label>",
                    f"  <select id=\"cascade_form_{self.identifier}_selection_group_{group["ID"]}_select\" name=\"{group["ID"]}\" class=\"cascade_form_select\">"
                ])
            if default_restriction != "":
                # We hide the restricted options in the default selection
                for element in self.elements_by_group[group["ID"]]:
                    if element["REQUIREMENT"] == default_restriction:
                        self.structured_html.append(f"    <option value=\"{element["ID"]}\">{element["LABEL"]}</option>")
                    else:
                        self.structured_html.append(f"    <option value=\"{element["ID"]}\" disabled hidden>{element["LABEL"]}</option>")
            else:
                # We show all options
                for element in self.elements_by_group[group["ID"]]:
                    self.structured_html.append(f"    <option value=\"{element["ID"]}\">{element["LABEL"]}</option>")
            default_restriction = self.elements_by_group[group["ID"]][0]["RESTRICTION"]
            self.structured_html.append([
                    f"  </select>",
                    f"  <button type=\"button\" class=\"cascade_form_explain\" id=\"cascade_form_{self.identifier}_explain_{group["ID"]}\">Explain</button>",
                    f"</div>"
                ])
        self.structured_html.append("</div>") # we close the wrapper
        # Now we make the script where we simply deposit the selection structure

        groups_subject_to_restrictions = []

        self.structured_html.append("<script>")
        self.structured_html.append("const restrictions = {")
        for i in range(1, len(self.groups)):
            # We check if previous row has RESTRICTIONS
            subject_to_restriction = False
            for element in self.elements_by_group[self.groups[i-1]["ID"]]:
                if element["RESTRICTION"] != "":
                    subject_to_restriction = True
                    break
            if subject_to_restriction:
                groups_subject_to_restrictions.append(i)
                # We add the structure and the listener
                self.structured_html.append(f"  \"{self.groups[i]["ID"]}\" : {{")
                for element in self.elements_by_group[self.groups[i-1]["ID"]]:
                    self.structured_html.append(f"    \"{element["ID"]}\" : [")
                    for successor in self.elements_by_group[self.groups[i]["ID"]]:
                        if successor["REQUIREMENT"] == element["RESTRICTION"]:
                            self.structured_html.append(f"      \"{successor["ID"]}\",")
                    # We need to get rid of the final comma
                    self.structured_html[-1] = self.structured_html[-1][:-1]
                    self.structured_html.append(f"    ],")
                self.structured_html[-1] = self.structured_html[-1][:-1]
                self.structured_html.append("  },")
        self.structured_html[-1] = self.structured_html[-1][:-1]
        self.structured_html.append("};\n")

        # Now we add the change listeners to groups which are subject to restrictions
        for i in groups_subject_to_restrictions:
            self.structured_html.append([
                    f"document.getElementById(\"cascade_form_{self.identifier}_selection_group_{self.groups[i-1]["ID"]}_select\").addEventListener(\"change\", function() {{",
                    f"  const value = this.value;",
                    f"  const affected = document.getElementById(\"cascade_form_{self.identifier}_selection_group_{self.groups[i]["ID"]}_select\");",
                    f"  let selection_update_pending = true",
                    f"  Array.from(affected.options).forEach(opt => {{",
                    f"    if (restrictions[\"{self.groups[i]["ID"]}\"][value].includes(opt.value)) {{",
                    f"      opt.hidden = false;",
                    f"      opt.disabled = false;",
                    f"      if (selection_update_pending) {{",
                    f"        affected.value = opt.value;",
                    f"        selection_update_pending = false;",
                    f"      }}"
                    f"    }} else {{",
                    f"      opt.hidden = true;",
                    f"      opt.disabled = true;",
                    f"    }}",
                    f"  }});",
                    f"}});"
                ])

        # Add onclick listeners for explain buttons (and store element descriptions)
        self.structured_html.append("const element_descriptions = {")
        for element in self.elements:
            self.structured_html.append(f"  \"{element["ID"]}\" : {json.dumps(element["DESCRIPTION"])},")
        self.structured_html[-1] = self.structured_html[-1][:-1]
        self.structured_html.append("};\n")
        for group in self.groups:
            self.structured_html.append([
                    f"document.getElementById(\"cascade_form_{self.identifier}_explain_{group["ID"]}\").addEventListener(\"click\", function() {{",
                    f"  alert(element_descriptions[document.getElementById(\"cascade_form_{self.identifier}_selection_group_{group["ID"]}_select\").value]);",
                    "})"
                ])
        self.structured_html.append("</script>")

