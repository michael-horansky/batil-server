# Generic class for pages. Every page inherits this.

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.db import get_db, get_pfp_source
from batil.html_objects.html_object import HTMLObject
from batil.aux_funcs import *

class Page(HTMLObject):

    def __init__(self, title):
        super().__init__()
        self.title = title
        # if "section" is a key in GET request, save as default section. Otherwise save 0
        if "section" in request.args:
            self.default_section = int(request.args.get("section"))
        else:
            self.default_section = 0

        self.client_row = None
        if g.user:
            db = get_db()
            self.client_row = db.execute("SELECT PRIVILEGE, CAST(ROUND(RATING) AS INTEGER) AS RATING_ROUND FROM BOC_USER WHERE USERNAME = ?", (g.user["username"],)).fetchone()

    def resolve_request(self):
        if request.method == 'POST':
            pass

    def html_open(self, stylesheet = None):
        if stylesheet is None:
            self.structured_html.append([
                    "<!doctype html>",
                    f"<title>{self.title} - Batil</title>",
                    f"<link rel=\"shortcut icon\" href=\"{ url_for('static', filename='favicon.ico') }\">"
                ])
        else:
            self.structured_html.append([
                    "<!doctype html>",
                    f"<title>{self.title} - Batil</title>",
                    f"<link rel=\"stylesheet\" href=\"{ url_for('static', filename=str(stylesheet)+'.css') }\">",
                    f"<link rel=\"shortcut icon\" href=\"{ url_for('static', filename='favicon.ico') }\">"
                ])

    def html_navbar(self):
        navlist = []
        navlist.append([
                "<nav class=\"navbar\">",
                "  <div class=\"navbar-left\">",
                f"    <span class=\"app_name\">{self.title} - Batil</span>",
                "  </div>",
                "  <div class=\"navbar-right\">",
                f"    <a href=\"{ url_for('home.index') }\">Home</a>"
            ])
        if g.user:
            # logged in
            navlist.append([
                    f"    <a href=\"{ url_for('auth.logout') }\">Log Out</a>"
                ])
            if self.client_row["PRIVILEGE"] == "ADMIN":
                navlist.append([
                        f"    <a href=\"{ url_for('admin.admin') }\">Admin</a>"
                    ])
        else:
            # logged out
            navlist.append([
                    f"    <a href=\"{ url_for('auth.register') }\">Register</a>",
                    f"    <a href=\"{ url_for('auth.login') }\">Log In</a>"
                ])
        navlist.append([
                "  </div>",
                "</nav>"
            ])
        self.structured_html.append(navlist)

    def get_initial_tab_class(self, tab_index):
        if tab_index == self.default_section:
            return("tab_content active")
        return("tab_content")

    def initialise_sections(self, section_names):
        # section names = {"id" : "human-readable label"}
        self.section_names = []
        self.structured_html.append([
            "<div class=\"container\">",
            "  <nav class=\"sidebar\">",
            "    <div class=\"sidebar_nav\">",
            "      <h2 class=\"sidebar_title\">Menu</h2>",
            "      <ul>"])
        self.number_of_sections = 0
        for iden, label in section_names.items():
            if self.number_of_sections == self.default_section:
                self.structured_html.append(f"        <li><a href=\"#\" class=\"tab_link active\" data-tab=\"{iden}\">{label}</a></li>")
            else:
                self.structured_html.append(f"        <li><a href=\"#\" class=\"tab_link\" data-tab=\"{iden}\">{label}</a></li>")
            self.section_names.append([iden, label])
            self.number_of_sections += 1
        self.structured_html.append([
            "      </ul>",
            "    </div>"
            ])
        # if logged in, we display the pfp here
        if g.user:
            """user_row = db.execute("SELECT USERNAME, D_CREATED, RATING, PROFILE_PICTURE_EXTENSION FROM BOC_USER WHERE USERNAME = ?", (g.user["username"],)).fetchone()
            if user_row["PROFILE_PICTURE_EXTENSION"] is not None:
                pfp_ext_ind = int(user_row["PROFILE_PICTURE_EXTENSION"])
                pfp_url = url_for('static', filename=f"user_content/profile_pictures/{g.user["username"]}_pfp{PFP_EXTENSIONS[pfp_ext_ind]}")"""
            pfp_url = get_pfp_source(g.user["username"])
            self.structured_html.append([
                "  <div class=\"sidebar_pfp\">",
                f"    <div class=\"sidebar_pfp_username\">{ g.user['username'] }</div>",
                f"    <div class=\"sidebar_pfp_username\">{ self.client_row['RATING_ROUND'] }</div>",
                f"    <img src=\"{pfp_url}\" alt=\"{g.user['username']} profile picture\">",
                "  </div>"
                ])

        self.structured_html.append([
            "  </nav>",
            "  <div class=\"main_content\">",
            f"    <div id=\"{self.section_names[0][0]}\" class=\"{self.get_initial_tab_class(0)}\">"
            ])
        self.section_currently_opened = 0

    def open_next_section(self):
        self.section_currently_opened += 1
        self.structured_html.append([
            "    </div>",
            f"    <div id=\"{self.section_names[self.section_currently_opened][0]}\" class=\"{self.get_initial_tab_class(self.section_currently_opened)}\">"
            ])

    def close_sections(self):
        self.structured_html.append([
            "    </div>",
            "  </div>",
            "</div>"
            ])
        # Add section-switching script
        self.structured_html.append([
            "<script>",
            "    document.querySelectorAll(\".tab_link\").forEach(link => {",
            "        link.addEventListener(\"click\", e => {",
            "            e.preventDefault();",
            "            document.querySelectorAll(\".tab_link\").forEach(l => l.classList.remove(\"active\"));",
            "            document.querySelectorAll(\".tab_content\").forEach(c => c.classList.remove(\"active\"));",
            "            link.classList.add(\"active\");",
            "            document.getElementById(link.dataset.tab).classList.add(\"active\");",
            "        });",
            "    });",
            "</script>"
            ])

    def open_container(self, iden, cls = None):
        if cls is None:
            self.structured_html.append(f"<div id=\"{iden}\">")
        else:
            self.structured_html.append(f"<div id=\"{iden}\" class=\"{cls}\">")

    def close_container(self):
        self.structured_html.append("</div>")

    def render_page(self):
        self.resolve_request()
        self.html_open("style")
        self.html_navbar()

        return(self.print_html())

    # Redirects and other browser-side actions

    def redirect_and_open(self, return_url, new_tab_url):
        return(f"""
            <script>
                window.location.href = \"{ return_url }\";
                window.open(\"{ new_tab_url }\", \"_blank\");
            </script>
        """)
