import json

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.db import get_db, get_table_as_list_of_dicts


class PageBoardEditor(Page):

    def __init__(self, board_id):
        super().__init__("Board")
        self.board_id = board_id
