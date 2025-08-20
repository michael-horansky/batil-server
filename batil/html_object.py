

class HTMLObject():

    def __init__(self):
        self.structured_html = []

    def print_html(self):
        # This returns a string formed by flattening self.structured_html
        def commit_element(element):
            if isinstance(element, str):
                return(element + "\n")
            else:
                res = ""
                for sub_element in element:
                    res += commit_element(sub_element)
                return(res)

        return(commit_element(self.structured_html))
