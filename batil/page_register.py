from batil.page import Page

class PageRegister(Page):

    def __init__(self):
        super().__init__()

    def html_register_form(self):
        self.structured_html.append([
                "<form method=\"post\">",
                "  <label for=\"username\">Username</label>",
                "  <input name=\"username\" id=\"username\" required>",
                "  <label for=\"email\">E-mail</label>",
                "  <input name=\"email\" id=\"email\" required>",
                "  <label for=\"password\">Password</label>",
                "  <input type=\"password\" name=\"password\" id=\"password\" required>",
                "  <input type=\"submit\" value=\"Register\">",
                "</form>"
            ])

    def render_page(self):
        self.html_open("Registration", "style")
        self.html_navbar()
        self.structured_html.append([
                "<section class=\"content\">",
                "<header>",
                "  <h1>Register</h1>",
                "</header>"
            ])
        self.html_register_form()
        self.structured_html.append(["</section>"])
        return(self.print_html())





