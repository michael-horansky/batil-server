import os
import json
import random
import string
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

import click
from flask import current_app, g

from batil.aux_funcs import *

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
def get_table_as_list_of_dicts(query, identifier, columns):
    db = get_db()
    cur = db.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    # Convert rows to dicts
    dict_rows = []
    for row in rows:
        raw_row_dict = dict(row)
        row_dict = {}
        #row_identifier_list = []
        #for identifier in identifiers:
        #    row_identifier_list.append(f"{identifier} = {raw_row_dict[identifier]}")
        #row_dict["IDENTIFIER"] = " AND ".join(row_identifier_list)
        row_dict["IDENTIFIER"] = raw_row_dict[identifier]
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

def new_blind_challenge(target_board, challenge_author, ruleset_selection):
    # target_board can be null for blind challenges
    # challange_author is username of person who made the request
    # ruleset_selection is a dict {rulegroup : rule}
    db = get_db()
    cur = db.cursor()
    # We first make a temporary table which encodes the current ruleset selection
    cur.execute("DROP TABLE IF EXISTS EXPECTED_RULES;")
    cur.execute("CREATE TEMP TABLE EXPECTED_RULES (RULEGROUP_ID INTEGER, RULE_VALUE TEXT);")
    for rg_name, rule_val in ruleset_selection.items():
        cur.execute("INSERT INTO EXPECTED_RULES (RULEGROUP_ID, RULE_VALUE) VALUES (?, ?)", (rg_name, rule_val))

    # Then we check if there exists a challenge proposition which we can match (specifically match on its ruleset, board, and opponent)
    if target_board is None:
        # For a blind board, the opponent must be blind
        retrieve_challenge = cur.execute("""
            SELECT BOC_CHALLENGES.CHALLENGE_ID AS CHALLENGE_ID, BOC_CHALLENGES.RESERVED_GAME_ID AS RESERVED_GAME_ID, BOC_CHALLENGES.CHALLENGER AS CHALLENGER, BOC_CHALLENGES.CHALLENGEE AS CHALLENGEE, BOC_CHALLENGES.BOARD_ID AS BOARD_ID, BOC_CHALLENGES.STATUS AS CHALLENGE_STATUS
                FROM BOC_CHALLENGES JOIN BOC_RULESETS ON BOC_CHALLENGES.RESERVED_GAME_ID = BOC_RULESETS.GAME_ID
                JOIN EXPECTED_RULES ON BOC_RULESETS.RULE_GROUP = EXPECTED_RULES.RULEGROUP_ID AND BOC_RULESETS.RULE = EXPECTED_RULES.RULE_VALUE
                WHERE CHALLENGE_STATUS = 'active' AND CHALLENGEE IS NULL AND CHALLENGER != ?
                GROUP BY BOC_CHALLENGES.CHALLENGE_ID
                HAVING COUNT(*) = (SELECT COUNT(*) FROM EXPECTED_RULES)
                ORDER BY BOC_CHALLENGES.DATE_CREATED ASC
            """, (challenge_author,)).fetchone()
    else:
        # selected board, blind opponent
        retrieve_challenge = cur.execute("""
            SELECT BOC_CHALLENGES.CHALLENGE_ID AS CHALLENGE_ID, BOC_CHALLENGES.RESERVED_GAME_ID AS RESERVED_GAME_ID, BOC_CHALLENGES.CHALLENGER AS CHALLENGER, BOC_CHALLENGES.CHALLENGEE AS CHALLENGEE, BOC_CHALLENGES.BOARD_ID AS BOARD_ID, BOC_CHALLENGES.STATUS AS CHALLENGE_STATUS
                FROM BOC_CHALLENGES JOIN BOC_RULESETS ON BOC_CHALLENGES.RESERVED_GAME_ID = BOC_RULESETS.GAME_ID
                JOIN EXPECTED_RULES ON BOC_RULESETS.RULE_GROUP = EXPECTED_RULES.RULEGROUP_ID AND BOC_RULESETS.RULE = EXPECTED_RULES.RULE_VALUE
                WHERE CHALLENGE_STATUS = 'active' AND (BOARD_ID = ? OR BOARD_ID IS NULL) AND CHALLENGEE IS NULL AND CHALLENGER != ?
                GROUP BY BOC_CHALLENGES.CHALLENGE_ID
                HAVING COUNT(*) = (SELECT COUNT(*) FROM EXPECTED_RULES)
                ORDER BY BOC_CHALLENGES.DATE_CREATED ASC
            """, (target_board, challenge_author)).fetchone()
    if retrieve_challenge is not None:
        # Answer the proposition
        # If proposition also doesn't specify the board_id, we select a random board! exciting!
        if target_board is None:
            target_board_id = retrieve_challenge["BOARD_ID"]
            if target_board_id is None:
                random_board_row = cur.execute("SELECT BOARD_ID FROM BOC_BOARDS WHERE BOARD_ID >= ABS(RANDOM()) % (SELECT MAX(BOARD_ID) + 1 FROM BOC_BOARDS) ORDER BY BOARD_ID").fetchone()
                target_board_id = random_board_row["BOARD_ID"]
        else:
            target_board_id = target_board

        # We now randomly determine if the challenger or the challengee is player A
        if random.randint(0, 1) == 0:
            # challenger is A
            player_a = retrieve_challenge["CHALLENGER"]
            player_b = g.user["username"]
        else:
            player_a = g.user["username"]
            player_b = retrieve_challenge["CHALLENGER"]

        # We finally activate the placeholder game
        cur.execute("UPDATE BOC_GAMES SET PLAYER_A = ?, PLAYER_B = ?, BOARD_ID = ?, D_STARTED = CURRENT_TIMESTAMP, STATUS = \"in_progress\" WHERE GAME_ID = ?", (player_a, player_b, target_board_id, retrieve_challenge["RESERVED_GAME_ID"]))

        # We also add the initial setup
        target_board_info = cur.execute("INSERT INTO BOC_MOVES (GAME_ID, TURN_INDEX, PLAYER, REPRESENTATION, D_MOVE) SELECT ?, 0, 'GM', SETUP_REPRESENTATION, CURRENT_TIMESTAMP FROM BOC_BOARDS WHERE BOARD_ID = ?", (retrieve_challenge["RESERVED_GAME_ID"], target_board_id))

        # We can't delete the challenge so that the game id hash doesn't repeat. That's fine! We just set its status to 'resolved'
        cur.execute("UPDATE BOC_CHALLENGES SET STATUS = 'resolved' WHERE CHALLENGE_ID = ?", (retrieve_challenge["CHALLENGE_ID"],))
    else:
        # If not, we create a new challenge proposition
        cur.execute("INSERT INTO BOC_CHALLENGES (CHALLENGER) VALUES (?)", (g.user["username"],))
        challenge_id = cur.lastrowid
        reserved_game_id = hash_number(challenge_id, length = 16)
        cur.execute("UPDATE BOC_CHALLENGES SET RESERVED_GAME_ID = ? WHERE CHALLENGE_ID = ?", (reserved_game_id, challenge_id))
        # Now we insert the placeholder game and the ruleset
        cur.execute("INSERT INTO BOC_GAMES (GAME_ID, STATUS) VALUES (?, 'waiting_for_match')", (reserved_game_id,))
        for rg_name, rule_val in ruleset_selection.items():
            cur.execute("INSERT INTO BOC_RULESETS (GAME_ID, RULE_GROUP, RULE) VALUES (?, ?, ?)", (reserved_game_id, rg_name, rule_val))
    db.commit()

def new_targeted_challenge(target_board, target_opponent, challenge_author, ruleset_selection):
    # a targeted challenge cannot be accepted blindly, but only through a designated form
    # hence creating a new targeted challenge always creates a new challenge row
    db = get_db()
    cur = db.cursor()

    # If not, we create a new challenge proposition
    cur.execute("INSERT INTO BOC_CHALLENGES (CHALLENGER, CHALLENGEE, BOARD_ID) VALUES (?, ?, ?)", (g.user["username"], target_opponent, target_board))
    challenge_id = cur.lastrowid
    reserved_game_id = hash_number(challenge_id, length = 16)
    cur.execute("UPDATE BOC_CHALLENGES SET RESERVED_GAME_ID = ? WHERE CHALLENGE_ID = ?", (reserved_game_id, challenge_id))
    # Now we insert the placeholder game and the ruleset
    cur.execute("INSERT INTO BOC_GAMES (GAME_ID, STATUS) VALUES (?, 'waiting_for_match')", (reserved_game_id,))
    for rg_name, rule_val in ruleset_selection.items():
        cur.execute("INSERT INTO BOC_RULESETS (GAME_ID, RULE_GROUP, RULE) VALUES (?, ?, ?)", (reserved_game_id, rg_name, rule_val))
    db.commit()

def accept_challenge(challenge_id):
    db = get_db()

    challenge_row = db.execute("SELECT RESERVED_GAME_ID, CHALLENGER, BOARD_ID FROM BOC_CHALLENGES WHERE CHALLENGE_ID = ?", (challenge_id,)).fetchone()

    # We now randomly determine if the challenger or the challengee is player A
    if random.randint(0, 1) == 0:
        # challenger is A
        player_a = challenge_row["CHALLENGER"]
        player_b = g.user["username"]
    else:
        player_a = g.user["username"]
        player_b = challenge_row["CHALLENGER"]

    # We activate the placeholder game
    db.execute("UPDATE BOC_GAMES SET PLAYER_A = ?, PLAYER_B = ?, BOARD_ID = ?, D_STARTED = CURRENT_TIMESTAMP, STATUS = \"in_progress\" WHERE GAME_ID = ?", (player_a, player_b, challenge_row["BOARD_ID"], challenge_row["RESERVED_GAME_ID"]))

    # We also add the initial setup
    target_board_info = db.execute("INSERT INTO BOC_MOVES (GAME_ID, TURN_INDEX, PLAYER, REPRESENTATION, D_MOVE) SELECT ?, 0, 'GM', SETUP_REPRESENTATION, CURRENT_TIMESTAMP FROM BOC_BOARDS WHERE BOARD_ID = ?", (challenge_row["RESERVED_GAME_ID"], challenge_row["BOARD_ID"]))

    # We can't delete the challenge so that the game id hash doesn't repeat. That's fine! We just set its status to 'resolved'
    db.execute("UPDATE BOC_CHALLENGES SET STATUS = 'resolved' WHERE CHALLENGE_ID = ?", (challenge_id,))
    db.commit()

def decline_challenge(challenge_id):
    db = get_db()
    challenge_row = db.execute("SELECT RESERVED_GAME_ID FROM BOC_CHALLENGES WHERE CHALLENGE_ID = ?", (challenge_id,)).fetchone()
    db.execute("UPDATE BOC_GAMES SET STATUS = \"declined\" WHERE GAME_ID = ?", (challenge_row["RESERVED_GAME_ID"],))
    db.execute("UPDATE BOC_CHALLENGES SET STATUS = 'resolved' WHERE CHALLENGE_ID = ?", (challenge_id,))
    db.commit()



