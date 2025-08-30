from batil.html_objects.page import Page

class PageLogin(Page):

    def __init__(self):
        super().__init__("Login")

    def html_login_form(self):
        self.structured_html.append([
                "<form method=\"post\">",
                "  <label for=\"username\">Username</label>",
                "  <input name=\"username\" id=\"username\" required>",
                "  <label for=\"password\">Password</label>",
                "  <input type=\"password\" name=\"password\" id=\"password\" required>",
                "  <input type=\"submit\" value=\"Login\">",
                "</form>"
            ])

    def render_page(self):
        self.html_open("style")
        self.html_navbar()
        self.structured_html.append([
                "<section class=\"content\">",
                "<header>",
                "  <h1>Log In</h1>",
                "</header>"
            ])
        self.html_login_form()
        self.structured_html.append(["</section>"])
        return(self.print_html())






