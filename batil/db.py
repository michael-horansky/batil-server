import os
import json
import random
import string
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

import click
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db_path = "instance/batil.sqlite"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted old database: {db_path}")
    db = get_db()
    cur = db.cursor()
    # Create table structure
    with current_app.open_resource('database/boc_db_init_sqlite.sql') as f:
        cur.executescript(f.read().decode('utf8'))
    # Populate with static data
    with current_app.open_resource('database/boc_db_static_data.sql') as f:
        cur.executescript(f.read().decode('utf8'))
    # Default admin user
    cur.execute(f"INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, D_CREATED, D_CHANGED, PRIVILEGE, STATUS) VALUES( 'batil', 'dvojka@110zbor.sk', '{generate_password_hash('loopinsohard')}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ADMIN', 'ACTIVE' )")
    cur.execute(f"INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, D_CREATED, D_CHANGED, PRIVILEGE, STATUS) VALUES( 'dvojka110', 'dvojka@110zbor.sk', '{generate_password_hash('Allegro4Ever')}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ADMIN', 'ACTIVE' )")
    cur.execute("INSERT INTO BOC_USER_RELATIONSHIPS VALUES('batil', 'dvojka110', 'friends')")

    # Add default boards
    default_boards_file = current_app.open_resource("database/default_boards.json")
    default_boards_data = json.load(default_boards_file)
    default_boards_file.close()
    for default_board in default_boards_data:
        sql, params = add_default_board_script(default_board)
        #cur.execute(sql, params)
        cur.execute(sql, params)
        board_id = cur.lastrowid
        users = cur.execute("SELECT USERNAME FROM BOC_USER").fetchall()
        for (username,) in users:
            cur.execute(
                "INSERT INTO BOC_USER_SAVED_BOARDS (BOARD_ID, USERNAME, D_SAVED) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (board_id, username)
            )


    #db.execute(
    #    "INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, AUTH_CODE, N_FAILS, D_CREATED, D_CHANGED, PRIVILEGE) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, \'USER\')",
    #    (username, email, generate_password_hash(password), random_string),
    #)
    db.commit()


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

# Helpful functions
def get_table_as_list_of_dicts(query, identifiers, columns):
    db = get_db()
    cur = db.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    # Convert rows to dicts
    dict_rows = []
    for row in rows:
        raw_row_dict = dict(row)
        row_dict = {}
        row_identifier_list = []
        for identifier in identifiers:
            row_identifier_list.append(f"{identifier} = {raw_row_dict[identifier]}")
        row_dict["IDENTIFIER"] = " AND ".join(row_identifier_list)
        for col in columns:
            row_dict[col] = raw_row_dict[col]
        dict_rows.append(row_dict)
    return(dict_rows)

def add_default_board_script(default_board):
    #return(f"WITH new_board AS (INSERT INTO BOC_BOARDS (T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, AUTHOR, IS_PUBLIC, D_CREATED, D_CHANGED, D_PUBLISHED, BOARD_NAME ) VALUES ({default_board["T_DIM"]}, {default_board["X_DIM"]}, {default_board["Y_DIM"]}, {json.dumps(default_board["STATIC_REPRESENTATION"])}, {json.dumps(default_board["SETUP_REPRESENTATION"])}, {json.dumps(default_board["AUTHOR"])}, {default_board["IS_PUBLIC"]}, {json.dumps(default_board["D_CREATED"])}, {json.dumps(default_board["D_CHANGED"])}, {json.dumps(default_board["D_PUBLISHED"])}, {json.dumps(default_board["BOARD_NAME"])})  RETURNING BOARD_ID) INSERT INTO BOC_USER_SAVED_BOARDS (BOARD_ID, USERNAME, D_SAVED) SELECT new_board.BOARD_ID, u.USERNAME, CURRENT_TIMESTAMP FROM BOC_USER u, new_board;")
    sql = """
        INSERT INTO BOC_BOARDS (
            T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, AUTHOR, IS_PUBLIC, D_CREATED, D_CHANGED, D_PUBLISHED, BOARD_NAME
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        default_board["T_DIM"], default_board["X_DIM"], default_board["Y_DIM"],
        default_board["STATIC_REPRESENTATION"], default_board["SETUP_REPRESENTATION"],
        default_board["AUTHOR"], default_board["IS_PUBLIC"], default_board["D_CREATED"],
        default_board["D_CHANGED"], default_board["D_PUBLISHED"], default_board["BOARD_NAME"]
    )
    return(sql, params)

def add_user(username, email, password):
    db = get_db()
    # Generate authentification code
    length = 32
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    db.execute(
        "INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, AUTH_CODE, N_FAILS, D_CREATED, D_CHANGED, PRIVILEGE) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, \'USER\')",
        (username, email, generate_password_hash(password), random_string),
    )

    # We check default boards
    default_boards = db.execute("SELECT BOARD_ID FROM BOC_BOARDS WHERE AUTHOR = \"batil\"").fetchall()
    for (board_id,) in default_boards:
        db.execute(
            "INSERT INTO BOC_USER_SAVED_BOARDS (BOARD_ID, USERNAME, D_SAVED) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (board_id, username)
        )

    db.commit()
