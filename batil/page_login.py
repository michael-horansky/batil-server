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
        self.html_open("auth_style")
        self.html_navbar()

        self.open_container("main_content")
        self.open_container("main_column")


        self.open_container("profile_content", "main_column_section")

        self.structured_html.append([
                "<section class=\"content\">",
                "<header>",
                "  <h1>Log in</h1>",
                "</header>"
            ])
        self.html_login_form()

        self.close_container()

        self.close_container()
        self.close_container()
        return(self.print_html())






