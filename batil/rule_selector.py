# A special html object for selecting rulesets by conditioned rulegroups

from batil.db import get_db, get_table_as_list_of_dicts

from batil.html_object import HTMLObject

class RuleSelector(HTMLObject):

    def __init__(self, identifier):
        super().__init__()
        self.identifier = identifier

        self.make_selector()

    def make_selector(self):
        pass
