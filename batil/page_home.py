from batil.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.action_form import ActionForm

class PageHome(Page):

    def __init__(self):
        super().__init__()

    def render_page(self):
        self.html_open("Home", "style")
        self.html_navbar()

        self.structured_html.append("<section class=\"content\">")
        # Check if logged in
        if g.user:
            self.structured_html.append([
                "<header>",
                f"  <h1>Welcome back, {g.user["username"]}</h1>",
                "</header>"
            ])
        else:
            self.structured_html.append([
                "<header>",
                f"  <h1>Get outta here</h1>",
                "</header>"
            ])

        silly_form = ActionForm("skibidi")
        silly_form.initialise_tabs(["hocus", "pocus"])
        silly_form.open_section(0)
        silly_form.structured_html.append([
            "<h3>Lol</h3>"
            ])
        silly_form.close_section()
        silly_form.open_section(1)
        silly_form.structured_html.append([
            "<p>lorem ipsum dolor</p>",
            "<button type=\"submit\">Post</button>"
            ])
        silly_form.close_section()
        silly_form.close_form()
        self.structured_html.append(silly_form.structured_html)



        self.structured_html.append([
                "</section>"
            ])
        return(self.print_html())
