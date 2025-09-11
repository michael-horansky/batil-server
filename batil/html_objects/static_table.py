# Generic class for static tables.

from batil.html_objects.html_object import HTMLObject

class StaticTable(HTMLObject):

    def __init__(self, iden):
        super().__init__()
        self.iden = iden

    def make_table(self, table_data, col_classes = None):
        # col_classes is a list of strings
        # table data is a list of lists of strings
        self.structured_html.append([
            f"  <div id=\"{self.iden}_static_table_container\" class=\"static_table_container\">",
            f"    <table id=\"{self.iden}\" class=\"static_table\">",
            f"      <tbody id=\"{self.iden}_static_table_body\" class=\"static_table_body\">"
            ])

        for data_i in range(len(table_data)):
            self.structured_html.append(f"        <tr>")
            for col_i in range(len(table_data[data_i])):
                if col_classes is not None:
                    self.structured_html.append(f"          <td class=\"{col_classes[col_i]}\">{table_data[data_i][col_i]}</td>")
                else:
                    self.structured_html.append(f"          <td>{table_data[data_i][col_i]}</td>")
            self.structured_html.append(f"        </tr>")
        self.structured_html.append([
            f"      </tbody>",
            f"    </table>",
            f"  </div>"
            ])
