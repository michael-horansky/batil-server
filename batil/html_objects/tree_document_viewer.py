# Generic class for viewers of documents with tree-like structures.
# All document content is kept in the table BOC_TREE_DOCUMENTS, for
# which this object serves as a html interface.

# Navigation inside the viewer is done through links and GET tokens,
# so that links to particular chapters are persistent.

import re

from batil.db import get_db
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.html_objects.html_object import HTMLObject

class TreeDocumentViewer(HTMLObject):

    # Static methods

    def get_navigation_keywords(iden):
        result_get_args = {}
        if f"{iden}_chapter" in request.form:
            result_get_args[f"{iden}_chapter"] = request.form.get(f"{iden}_chapter")
            print("Open chapter:", request.form.get(f"{iden}_chapter"))
        return(result_get_args)

    # Instance methods

    def __init__(self, iden, bp, home_index, client_privilege, persistent_get_args = {}):
        super().__init__()
        self.iden = iden
        self.bp = bp
        self.home_index = home_index
        self.client_privilege = client_privilege # USER can read, ADMIN can edit!
        self.persistent_get_args = persistent_get_args
        self.determine_current_display()
        self.load_content()
        self.make_viewer()

    def determine_current_display(self):
        if f"{self.iden}_chapter" in request.args:
            try:
                self.current_display = int(request.args.get(f"{self.iden}_chapter"))
            except:
                self.current_display = "_ROOT_"
        else:
            self.current_display = "_ROOT_"

    def load_content(self):
        db = get_db()

        if self.current_display == "_ROOT_":
            self.display_element = db.execute("SELECT CHAPTER_ID, LABEL, CONTENT, NEXT_CHAPTER, FIRST_SUBCHAPTER, PARENT_CHAPTER FROM BOC_TREE_DOCUMENTS WHERE VIEWER = ? AND PARENT_CHAPTER IS NULL", (self.iden,)).fetchone()
            self.display_parent = None
        else:
            self.display_element = db.execute("SELECT CHAPTER_ID, LABEL, CONTENT, NEXT_CHAPTER, FIRST_SUBCHAPTER, PARENT_CHAPTER FROM BOC_TREE_DOCUMENTS WHERE CHAPTER_ID = ?", (self.current_display,)).fetchone()
            self.display_parent = db.execute("SELECT CHAPTER_ID, LABEL, NEXT_CHAPTER, FIRST_SUBCHAPTER FROM BOC_TREE_DOCUMENTS WHERE CHAPTER_ID = ?", (self.display_element["PARENT_CHAPTER"],)).fetchone()

            display_siblings_data = db.execute("SELECT CHAPTER_ID, LABEL, NEXT_CHAPTER, FIRST_SUBCHAPTER FROM BOC_TREE_DOCUMENTS WHERE VIEWER = ? AND PARENT_CHAPTER = ?", (self.iden, self.display_element["PARENT_CHAPTER"])).fetchall()
            self.display_siblings = {}
            for datum in display_siblings_data:
                self.display_siblings[datum["CHAPTER_ID"]] = datum

        display_children_data = db.execute("SELECT CHAPTER_ID, LABEL, NEXT_CHAPTER, FIRST_SUBCHAPTER FROM BOC_TREE_DOCUMENTS WHERE VIEWER = ? AND PARENT_CHAPTER = ?", (self.iden, self.display_element["CHAPTER_ID"])).fetchall()
        self.display_children = {}
        for datum in display_children_data:
            self.display_children[datum["CHAPTER_ID"]] = datum

    def chapter_href(self, chapter_id):
        return(url_for(f"{self.bp}.{self.home_index}", **self.persistent_get_args, **{f"{self.iden}_chapter" : chapter_id}))

    def make_left_sidebar(self):
        self.structured_html.append([
            f"  <nav id=\"{self.iden}_left_sidebar\" class=\"tdv_left_sidebar tdv_sidebar\">",
            f"    <ul>"
            ])

        if self.display_parent is not None:
            self.structured_html.append(f"      <li><a href=\"{self.chapter_href(self.display_parent["CHAPTER_ID"])}\">(up) {self.display_parent["LABEL"]}</a></li>")

            cur_sibling = self.display_parent["FIRST_SUBCHAPTER"]
            while(cur_sibling is not None):
                if cur_sibling == self.current_display:
                    self.structured_html.append(f"      <li><span class=\"tdv_nav_this\">{self.display_siblings[cur_sibling]["LABEL"]}</span></li>")
                else:
                    self.structured_html.append(f"      <li><a href=\"{self.chapter_href(self.display_siblings[cur_sibling]["CHAPTER_ID"])}\">{self.display_siblings[cur_sibling]["LABEL"]}</a></li>")

                cur_sibling = self.display_siblings[cur_sibling]["NEXT_CHAPTER"]
        else:
            # Root has no siblings since tree is always connected
            self.structured_html.append(f"      <li><span class=\"tdv_nav_this\">{self.display_element["LABEL"]}</span></li>")

        self.structured_html.append([
            f"    </ul>",
            f"  </nav>"
            ])

    def parse_content_for_display(self, content_text):
        # This function allows us to add not just html objects, but also dynamical python-calculated objects, such as links with URL_FOR
        parsed_content_text = content_text

        def lft(href, label):
            # link from text
            return(f"<a href=\"{href}\" target=\"_blank\">{label}</a>")

        # Magic word patterns
        magic_word_patterns = {
            "_URLKW2_([A-Za-z.]+)<([A-Za-z_]+)=([A-Za-z0-9]+),([A-Za-z_]+)=([A-Za-z0-9]+)>_([A-Za-z0-9\- ]+)_" : (lambda match : lft(url_for(match.group(1), **{match.group(2) : match.group(3), match.group(4) : match.group(5)}), match.group(6)) ),
            "_URLKW_([A-Za-z.]+)<([A-Za-z_]+)=([A-Za-z0-9]+)>_([A-Za-z0-9\- ]+)_" : (lambda match : lft(url_for(match.group(1), **{match.group(2) : match.group(3)}), match.group(4)) ),
            "_URL_([A-Za-z.]+)_([A-Za-z0-9\- ]+)_" : (lambda match : lft(url_for(match.group(1)), match.group(2)) ),
            "_URLEXT_<([A-Za-z0-9.:/\-_]+)>_([A-Za-z0-9\- ]+)_" : (lambda match : lft(match.group(1), match.group(2)) )
            }

        for pattern, replacer in magic_word_patterns.items():
            parsed_content_text = re.sub(pattern, replacer, parsed_content_text)

        return(parsed_content_text)

    def make_main_content(self):
        if self.client_privilege == "ADMIN":
            self.structured_html.append([
                f"  <div id=\"{self.iden}_content\" class=\"tdv_main\">",
                f"    <form id=\"{self.iden}_form\" class=\"tdv_form\" action=\"{url_for(f"{self.bp}.action_{self.iden}")}\" method=\"post\">",
                f"      <div id=\"{self.iden}_tabs\" class=\"tdv_tabs\">",
                f"        <div id=\"{self.iden}_tab_read\" class=\"tdv_tab active\" onclick=\"tdv_{self.iden}_read()\">Read</div>",
                f"        <div id=\"{self.iden}_tab_edit\" class=\"tdv_tab\" onclick=\"tdv_{self.iden}_edit()\">Edit</div>",
                f"      </div>",
                f"      <div id=\"{self.iden}_section_container\" class=\"tdv_section_container\">",
                f"        <div id=\"{self.iden}_section_read\" class=\"tdv_section_read tdv_section active\">",
                f"          <div id=\"{self.iden}_section_read_content\" class=\"tdv_section_content\">",
                self.parse_content_for_display(self.display_element["CONTENT"]),
                f"          </div>",
                f"        </div>",
                f"        <div id=\"{self.iden}_section_edit\" class=\"tdv_section_edit tdv_section\">",
                f"          <div id=\"{self.iden}_section_edit_content\" class=\"tdv_section_content\">",
                f"            <input type=\"text\" class=\"tdv_edit_label\" name=\"chapter_label\" value=\"{self.display_element["LABEL"]}\">",
                f"            <textarea class=\"tdv_edit_textarea\" name=\"chapter_content\">{self.display_element["CONTENT"]}</textarea>",
                f"          </div>",
                f"        </div>",
                f"      </div>",
                f"      <div id=\"{self.iden}_action_footer\" class=\"tdv_action_footer\">",
                f"        <button type=\"submit\" class=\"tdv_action_button\" name=\"{self.iden}_action\" value=\"edit\">Save changes</button>"
                ])
            if self.display_element["PARENT_CHAPTER"] is None:
                self.structured_html.append(f"        <button type=\"submit\" class=\"tdv_action_button\" name=\"{self.iden}_action\" value=\"insert_new_chapter_next\" disabled>Insert new chapter next</button>")
            else:
                self.structured_html.append(f"        <button type=\"submit\" class=\"tdv_action_button\" name=\"{self.iden}_action\" value=\"insert_new_chapter_next\">Insert new chapter next</button>")
            self.structured_html.append([
                f"        <button type=\"submit\" class=\"tdv_action_button\" name=\"{self.iden}_action\" value=\"insert_new_child\">Add new child</button>",
                f"      </div>",
                f"      <input type=\"hidden\" name=\"{self.iden}_chapter\" value=\"{self.display_element["CHAPTER_ID"]}\">",
                f"    </form>",
                f"  </div>"
                ])
        elif self.client_privilege in ["USER", "GUEST"]:
            self.structured_html.append([
                f"  <div id=\"{self.iden}_content\" class=\"tdv_main\">",
                f"    <div id=\"{self.iden}_section_container\" class=\"tdv_section_container\">",
                f"      <div id=\"{self.iden}_section_read\" class=\"tdv_section_read tdv_section active\">",
                f"        <div id=\"{self.iden}_section_read_content\" class=\"tdv_section_content\">",
                self.parse_content_for_display(self.display_element["CONTENT"]),
                f"        </div>",
                f"      </div>",
                f"    </div>",
                f"  </div>"
                ])

    def make_right_sidebar(self):
        self.structured_html.append([
            f"  <nav id=\"{self.iden}_right_sidebar\" class=\"tdv_right_sidebar tdv_sidebar\">",
            f"    <ul>"
            ])

        cur_child = self.display_element["FIRST_SUBCHAPTER"]
        while(cur_child is not None):
            self.structured_html.append(f"      <li><a href=\"{self.chapter_href(self.display_children[cur_child]["CHAPTER_ID"])}\">{self.display_children[cur_child]["LABEL"]}</a></li>")
            cur_child = self.display_children[cur_child]["NEXT_CHAPTER"]

        self.structured_html.append([
            f"    </ul>",
            f"  </nav>"
            ])

    def make_tab_script(self):
        self.structured_html.append([
            f"<script>",
            f"  function tdv_{self.iden}_read() {{",
            f"    document.getElementById(`{self.iden}_tab_edit`).classList.toggle('active', false);",
            f"    document.getElementById(`{self.iden}_section_edit`).classList.toggle('active', false);",
            f"    document.getElementById(`{self.iden}_tab_read`).classList.toggle('active', true);",
            f"    document.getElementById(`{self.iden}_section_read`).classList.toggle('active', true);",
            f"  }}",
            f"  function tdv_{self.iden}_edit() {{",
            f"    document.getElementById(`{self.iden}_tab_read`).classList.toggle('active', false);",
            f"    document.getElementById(`{self.iden}_section_read`).classList.toggle('active', false);",
            f"    document.getElementById(`{self.iden}_tab_edit`).classList.toggle('active', true);",
            f"    document.getElementById(`{self.iden}_section_edit`).classList.toggle('active', true);",
            f"  }}",
            f"</script>"
            ])


    def make_viewer(self):

        self.structured_html.append(f"<div id=\"{self.iden}_container\" class=\"tdv_container\">")

        self.make_left_sidebar()
        self.make_main_content()
        self.make_right_sidebar()

        self.structured_html.append(f"</div>")

        if self.client_privilege == "ADMIN":
            self.make_tab_script()
