# Generic class for pages. Every page inherits this.

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.html_object import HTMLObject

class Page(HTMLObject):

    def __init__(self):
        super().__init__()

    def html_open(self, title, stylesheet):
        self.structured_html.append([
                "<!doctype html>",
                f"<title>{title} - Batil</title>",
                f"<link rel=\"stylesheet\" href=\"{ url_for('static', filename=str(stylesheet)+'.css') }\">",
                f"<link rel=\"shortcut icon\" href=\"{ url_for('static', filename='favicon.ico') }\">"
            ])

    def html_navbar(self):
        navlist = []
        navlist.append([
                "<nav>",
                "  <h1>Batil</h1>",
                "  <ul>"
            ])
        if g.user:
            # logged in
            navlist.append([
                    f"    <li><span>{ g.user['username'] }</span>",
                    f"    <li><a href=\"{ url_for('auth.logout') }\">Log Out</a>"
                ])
        else:
            # logged out
            navlist.append([
                    f"    <li><a href=\"{ url_for('auth.register') }\">Register</a>"
                    f"    <li><a href=\"{ url_for('auth.login') }\">Log In</a>"
                ])
        navlist.append([
                "  </ul>",
                "</nav>"
            ])
        self.structured_html.append(navlist)

    def render_page(self):
        self.html_open("default", "style")
        self.html_navbar()
        return(self.print_html())
