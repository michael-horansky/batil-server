import os
import json
import random
import time
import string
import numpy as np
from scipy.optimize import minimize
from cubature import cubature
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

import click
from flask import current_app, g, url_for
#from flask_mail import Message
#from batil.batil_flask_extensions import mail

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
    cur.execute(f"""
        INSERT INTO BOC_USER
            (USERNAME, EMAIL, PASSWORD, D_CREATED, D_CHANGED, PRIVILEGE, STATUS, PROFILE_PICTURE_EXTENSION,
             RATING)
        VALUES( 'batil', 'dvojka@110zbor.sk', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ADMIN', 'ACTIVE', 1,
               (SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_RATING\")
               )""", (generate_password_hash('loopinsohard'), ))
    cur.execute(f"""
        INSERT INTO BOC_USER
            (USERNAME, EMAIL, PASSWORD, D_CREATED, D_CHANGED, PRIVILEGE, STATUS, PROFILE_PICTURE_EXTENSION,
             RATING)
        VALUES( 'dvojka110', 'dvojka@110zbor.sk', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ADMIN', 'ACTIVE', 2,
               (SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_RATING\")
               )""", (generate_password_hash('Allegro4Ever'), ))

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
                "INSERT INTO BOC_USER_BOARD_RELATIONSHIPS (BOARD_ID, USERNAME, STATUS, D_STATUS) VALUES (?, ?, \"saved\", CURRENT_TIMESTAMP)",
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

@click.command('tdv-backup')
def tdv_backup_command():
    # Backs up all TDV rows into a json
    backup_file_path = os.path.join(current_app.root_path, "static", "backup", "tree_documents_content.json")

    db = get_db()
    tree_documents_rows = db.execute("SELECT CHAPTER_ID, LABEL, CONTENT, NEXT_CHAPTER, FIRST_SUBCHAPTER, PARENT_CHAPTER, VIEWER FROM BOC_TREE_DOCUMENTS").fetchall()
    tree_documents = []
    for row in tree_documents_rows:
        tree_documents.append({
            "CHAPTER_ID"       : row["CHAPTER_ID"],
            "LABEL"            : row["LABEL"],
            "CONTENT"          : row["CONTENT"],
            "NEXT_CHAPTER"     : row["NEXT_CHAPTER"],
            "FIRST_SUBCHAPTER" : row["FIRST_SUBCHAPTER"],
            "PARENT_CHAPTER"   : row["PARENT_CHAPTER"],
            "VIEWER"           : row["VIEWER"]
            })

    with open(backup_file_path, "w", encoding="utf-8") as f:
        json.dump(tree_documents, f, indent=2, ensure_ascii=False)

    click.echo(f"Tree document content backed up to {backup_file_path}")

@click.command('tdv-restore')
def tdv_restore_command():
    # Restores all TDV rows from a json
    backup_file_path = os.path.join(current_app.root_path, "static", "backup", "tree_documents_content.json")

    db = get_db()
    with open(backup_file_path, "r", encoding="utf-8") as f:
        tree_documents = json.load(f)
    tree_document_values = []
    for td_row in tree_documents:
        tree_document_values.append((td_row["CHAPTER_ID"], td_row["LABEL"], td_row["CONTENT"], td_row["NEXT_CHAPTER"], td_row["FIRST_SUBCHAPTER"], td_row["PARENT_CHAPTER"], td_row["VIEWER"]))
    db.executemany("INSERT OR REPLACE INTO BOC_TREE_DOCUMENTS (CHAPTER_ID, LABEL, CONTENT, NEXT_CHAPTER, FIRST_SUBCHAPTER, PARENT_CHAPTER, VIEWER) VALUES (?, ?, ?, ?, ?, ?, ?)", tree_document_values)
    db.commit()
    click.echo(f"Tree document content restored from {backup_file_path}")


@click.command('tutorials-backup')
def tutorials_backup_command():
    # Backs up all the tutorials and also their boards
    pass


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(tdv_backup_command)
    app.cli.add_command(tdv_restore_command)

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
        row_dict["IDENTIFIER"] = raw_row_dict[identifier]
        for col in columns:
            row_dict[col] = raw_row_dict[col]
        dict_rows.append(row_dict)
    return(dict_rows)

def add_default_board_script(default_board):
    sql = """
        INSERT INTO BOC_BOARDS (
            T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, AUTHOR, IS_PUBLIC, D_CREATED, D_CHANGED, D_PUBLISHED, BOARD_NAME,
            HANDICAP, HANDICAP_STD, KAPPA, STEP_SIZE
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            0.0, (SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_ESTIMATE_HANDICAP_STD\"),
            (SELECT 2 * PARAMETER_VALUE / (1 - PARAMETER_VALUE) FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_ESTIMATE_DRAW_PROBABILITY\"), 0.0
        )"""
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

    db.execute("""
        INSERT INTO BOC_USER
            (USERNAME, EMAIL, PASSWORD, AUTH_CODE, N_FAILS, D_CREATED, D_CHANGED, PRIVILEGE, STATUS,
            RATING)
        VALUES
            (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, \'USER\', \'ACTIVE\',
            (SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_RATING\"))
        """, (username, email, generate_password_hash(password), random_string),
    )

    # We check default boards
    default_boards = db.execute("SELECT BOARD_ID FROM BOC_BOARDS WHERE AUTHOR = \"batil\"").fetchall()
    for (board_id,) in default_boards:
        db.execute(
            "INSERT INTO BOC_USER_BOARD_RELATIONSHIPS (BOARD_ID, USERNAME, STATUS, D_STATUS) VALUES (?, ?, \"saved\", CURRENT_TIMESTAMP)",
            (board_id, username)
        )

    db.commit()

    # We send the verification email
    """varify_url =
    msg = Message(
        subject="batil - email verification",
        recipients=[email],
        body="This is a test email."
    )
    mail.send(msg)"""

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
                WHERE
                    CHALLENGE_STATUS = 'active'
                    AND CHALLENGEE IS NULL
                    AND CHALLENGER != :a
                    AND NOT EXISTS (
                        SELECT 1
                        FROM BOC_USER_RELATIONSHIPS
                        WHERE BOC_USER_RELATIONSHIPS.STATUS = \"blocked\"
                        AND (
                                (BOC_USER_RELATIONSHIPS.USER_1 = :a AND BOC_USER_RELATIONSHIPS.USER_2 = BOC_CHALLENGES.CHALLENGER)
                            OR (BOC_USER_RELATIONSHIPS.USER_2 = :a AND BOC_USER_RELATIONSHIPS.USER_1 = BOC_CHALLENGES.CHALLENGER)
                        )
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM BOC_USER_BOARD_RELATIONSHIPS BOC_USER_BOARD_RELATIONSHIPS
                        WHERE BOC_USER_BOARD_RELATIONSHIPS.STATUS = 'blocked'
                        AND BOC_USER_BOARD_RELATIONSHIPS.USERNAME = :a
                        AND BOC_USER_BOARD_RELATIONSHIPS.BOARD_ID = BOC_CHALLENGES.BOARD_ID
                    )
                GROUP BY BOC_CHALLENGES.CHALLENGE_ID
                HAVING COUNT(*) = (SELECT COUNT(*) FROM EXPECTED_RULES)
                ORDER BY BOC_CHALLENGES.DATE_CREATED ASC
            """, {"a" : challenge_author}).fetchone()
    else:
        # selected board, blind opponent
        retrieve_challenge = cur.execute("""
            SELECT BOC_CHALLENGES.CHALLENGE_ID AS CHALLENGE_ID, BOC_CHALLENGES.RESERVED_GAME_ID AS RESERVED_GAME_ID, BOC_CHALLENGES.CHALLENGER AS CHALLENGER, BOC_CHALLENGES.CHALLENGEE AS CHALLENGEE, BOC_CHALLENGES.BOARD_ID AS BOARD_ID, BOC_CHALLENGES.STATUS AS CHALLENGE_STATUS
                FROM BOC_CHALLENGES JOIN BOC_RULESETS ON BOC_CHALLENGES.RESERVED_GAME_ID = BOC_RULESETS.GAME_ID
                JOIN EXPECTED_RULES ON BOC_RULESETS.RULE_GROUP = EXPECTED_RULES.RULEGROUP_ID AND BOC_RULESETS.RULE = EXPECTED_RULES.RULE_VALUE
                WHERE
                    CHALLENGE_STATUS = 'active'
                    AND (BOARD_ID = :b OR BOARD_ID IS NULL)
                    AND CHALLENGEE IS NULL
                    AND CHALLENGER != :a
                    AND NOT EXISTS (
                        SELECT 1
                        FROM BOC_USER_RELATIONSHIPS
                        WHERE BOC_USER_RELATIONSHIPS.STATUS = \"blocked\"
                        AND (
                                (BOC_USER_RELATIONSHIPS.USER_1 = :a AND BOC_USER_RELATIONSHIPS.USER_2 = BOC_CHALLENGES.CHALLENGER)
                            OR (BOC_USER_RELATIONSHIPS.USER_2 = :a AND BOC_USER_RELATIONSHIPS.USER_1 = BOC_CHALLENGES.CHALLENGER)
                        )
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM BOC_USER_BOARD_RELATIONSHIPS BOC_USER_BOARD_RELATIONSHIPS
                        WHERE BOC_USER_BOARD_RELATIONSHIPS.STATUS = 'blocked'
                        AND BOC_USER_BOARD_RELATIONSHIPS.USERNAME = BOC_CHALLENGES.CHALLENGER
                        AND BOC_USER_BOARD_RELATIONSHIPS.BOARD_ID = :b
                    )
                GROUP BY BOC_CHALLENGES.CHALLENGE_ID
                HAVING COUNT(*) = (SELECT COUNT(*) FROM EXPECTED_RULES)
                ORDER BY BOC_CHALLENGES.DATE_CREATED ASC
            """, {"a" : challenge_author, "b" : target_board}).fetchone()
    if retrieve_challenge is not None:
        # Answer the proposition
        # If proposition also doesn't specify the board_id, we select a random board! exciting!
        if target_board is None:
            target_board_id = retrieve_challenge["BOARD_ID"]
            if target_board_id is None:
                random_board_row = cur.execute("""
                    SELECT BOC_BOARDS.BOARD_ID AS BOARD_ID FROM BOC_BOARDS WHERE
                        BOC_BOARDS.BOARD_ID >= ABS(RANDOM()) % (SELECT MAX(BOC_BOARDS.BOARD_ID) + 1 FROM BOC_BOARDS)
                        AND NOT EXISTS (
                            SELECT 1
                            FROM BOC_USER_BOARD_RELATIONSHIPS BOC_USER_BOARD_RELATIONSHIPS
                            WHERE BOC_USER_BOARD_RELATIONSHIPS.STATUS = 'blocked'
                            AND BOC_USER_BOARD_RELATIONSHIPS.USERNAME = :a
                            AND BOC_USER_BOARD_RELATIONSHIPS.BOARD_ID = BOC_BOARDS.BOARD_ID
                        )
                    ORDER BY BOC_BOARDS.BOARD_ID
                    """, {"a" : challenge_author}).fetchone()
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
        if ruleset_selection["deadline"] == "one_hour_cumulative":
            player_A_cumulative_seconds = 3600
            player_B_cumulative_seconds = 3600
        elif ruleset_selection["deadline"] == "one_day_cumulative":
            player_A_cumulative_seconds = 3600 * 24
            player_B_cumulative_seconds = 3600 * 24
        else:
            player_A_cumulative_seconds = None
            player_B_cumulative_seconds = None

        # Read the initial ratings of the two players
        player_a_rating = cur.execute("SELECT RATING FROM BOC_USER WHERE USERNAME = ?", (player_a,)).fetchone()["RATING"]
        player_b_rating = cur.execute("SELECT RATING FROM BOC_USER WHERE USERNAME = ?", (player_b,)).fetchone()["RATING"]

        cur.execute("""
            UPDATE BOC_GAMES SET
                PLAYER_A = ?, PLAYER_B = ?, BOARD_ID = ?, D_STARTED = CURRENT_TIMESTAMP, STATUS = \"in_progress\", PLAYER_A_CUMULATIVE_SECONDS = ?, PLAYER_B_CUMULATIVE_SECONDS = ?,
                R_A_INIT = ?,
                R_B_INIT = ?,
                R_A_ADJUSTMENT = NULL
            WHERE GAME_ID = ?""", (player_a, player_b, target_board_id, player_A_cumulative_seconds, player_B_cumulative_seconds, player_a_rating, player_b_rating, retrieve_challenge["RESERVED_GAME_ID"]))

        # We also add the initial setup
        target_board_info = cur.execute("INSERT INTO BOC_MOVES (GAME_ID, TURN_INDEX, PLAYER, REPRESENTATION, D_MOVE) SELECT ?, 0, 'GM', SETUP_REPRESENTATION, CURRENT_TIMESTAMP FROM BOC_BOARDS WHERE BOARD_ID = ?", (retrieve_challenge["RESERVED_GAME_ID"], target_board_id))

        # We can't delete the challenge so that the game id hash doesn't repeat. That's fine! We just set its status to 'resolved'
        cur.execute("UPDATE BOC_CHALLENGES SET STATUS = 'resolved' WHERE CHALLENGE_ID = ?", (retrieve_challenge["CHALLENGE_ID"],))
    else:
        # If not, we create a new challenge proposition
        if target_board is None:
            cur.execute("INSERT INTO BOC_CHALLENGES (CHALLENGER) VALUES (?)", (g.user["username"],))
        else:
            cur.execute("INSERT INTO BOC_CHALLENGES (CHALLENGER, BOARD_ID) VALUES (?, ?)", (g.user["username"], target_board))
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
    rule_for_deadline = db.execute("SELECT RULE FROM BOC_RULESETS WHERE GAME_ID = ? AND RULE_GROUP = \"deadline\"", (challenge_row["RESERVED_GAME_ID"],)).fetchone()["RULE"]
    if rule_for_deadline == "one_hour_cumulative":
        player_A_cumulative_seconds = 3600
        player_B_cumulative_seconds = 3600
    elif rule_for_deadline == "one_day_cumulative":
        player_A_cumulative_seconds = 3600 * 24
        player_B_cumulative_seconds = 3600 * 24
    else:
        player_A_cumulative_seconds = None
        player_B_cumulative_seconds = None

    # Read the initial ratings of the two players
    player_a_rating = db.execute("SELECT RATING FROM BOC_USER WHERE USERNAME = ?", (player_a,)).fetchone()["RATING"]
    player_b_rating = db.execute("SELECT RATING FROM BOC_USER WHERE USERNAME = ?", (player_b,)).fetchone()["RATING"]

    db.execute("UPDATE BOC_GAMES SET PLAYER_A = ?, PLAYER_B = ?, BOARD_ID = ?, D_STARTED = CURRENT_TIMESTAMP, STATUS = \"in_progress\", PLAYER_A_CUMULATIVE_SECONDS = ?, PLAYER_B_CUMULATIVE_SECONDS = ?, R_A_INIT = ?, R_B_INIT = ?, R_A_ADJUSTMENT = NULL WHERE GAME_ID = ?", (player_a, player_b, challenge_row["BOARD_ID"], player_A_cumulative_seconds, player_B_cumulative_seconds, player_a_rating, player_b_rating, challenge_row["RESERVED_GAME_ID"]))

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

# Just the same but for tutorials

def create_new_tutorial(author, board_id, ruleset_selection):
    db = get_db()
    cur = db.cursor()
    print("New tutorial by", author, board_id, ruleset_selection)
    cur.execute("INSERT INTO BOC_TUTORIALS (BOARD_ID, AUTHOR, STATUS) VALUES (?, ?, 'in_progress')", (board_id, author))
    new_tutorial_id = cur.lastrowid

    # ruleset
    for rg_name, rule_val in ruleset_selection.items():
        cur.execute("INSERT INTO BOC_TUTORIAL_RULESETS (TUTORIAL_ID, RULE_GROUP, RULE) VALUES (?, ?, ?)", (new_tutorial_id, rg_name, rule_val))

    # initial setup
    target_board_info = db.execute("INSERT INTO BOC_TUTORIAL_MOVES (TUTORIAL_ID, TURN_INDEX, PLAYER, REPRESENTATION) SELECT ?, 0, 'GM', SETUP_REPRESENTATION FROM BOC_BOARDS WHERE BOARD_ID = ?", (new_tutorial_id, board_id))

    db.commit()




# User relationship management

def send_friend_request(sender, receiver):
    # Basically if relationship doesn't exist already, a friends_pending one is created. If there is a pending one from the other one, it gets accepted. Otherwise nothing happens (existing friends, blocked etc)
    db = get_db()
    existing_relation_row = db.execute("SELECT USER_1, USER_2, STATUS, D_STATUS FROM BOC_USER_RELATIONSHIPS WHERE ((USER_1 = ? AND USER_2 = ?) OR (USER_1 = ? AND USER_2 = ?))", (sender, receiver, receiver, sender)).fetchone()
    if existing_relation_row is None:
        db.execute("INSERT INTO BOC_USER_RELATIONSHIPS (USER_1, USER_2, STATUS, D_STATUS) VALUES (?, ?, \"friends_pending\", CURRENT_TIMESTAMP)", (sender, receiver))
        db.commit()
    elif existing_relation_row["USER_1"] == receiver and existing_relation_row["STATUS"] == "friends_pending":
        db.execute("UPDATE BOC_USER_RELATIONSHIPS SET STATUS = \"friends\", D_STATUS = CURRENT_TIMESTAMP WHERE USER_1 = ? AND USER_2 = ?", (receiver, sender))
        db.commit()

def accept_friend_request(sender, receiver):
    db = get_db()
    db.execute("UPDATE BOC_USER_RELATIONSHIPS SET STATUS = \"friends\", D_STATUS = CURRENT_TIMESTAMP WHERE USER_1 = ? AND USER_2 = ? AND STATUS = \"friends_pending\"", (receiver, sender))
    db.commit()

def decline_friend_request(sender, receiver):
    db = get_db()
    db.execute("DELETE FROM BOC_USER_RELATIONSHIPS WHERE USER_1 = ? AND USER_2 = ? AND STATUS = \"friends_pending\"", (receiver, sender))
    db.commit()

def withdraw_friend_request(sender, receiver):
    db = get_db()
    db.execute("DELETE FROM BOC_USER_RELATIONSHIPS WHERE USER_1 = ? AND USER_2 = ? AND STATUS = \"friends_pending\"", (sender, receiver))
    db.commit()

def unfriend_user(sender, receiver):
    db = get_db()
    db.execute("DELETE FROM BOC_USER_RELATIONSHIPS WHERE ((USER_1 = ? AND USER_2 = ?) OR (USER_1 = ? AND USER_2 = ?)) AND STATUS = \"friends\"", (sender, receiver, receiver, sender))
    db.commit()

def block_user(sender, receiver):
    db = get_db()
    # Removes existing freindship
    db.execute("DELETE FROM BOC_USER_RELATIONSHIPS WHERE ((USER_1 = ? AND USER_2 = ?) OR (USER_1 = ? AND USER_2 = ?)) AND (STATUS = \"friends\" OR STATUS = \"friends_pending\")", (sender, receiver, receiver, sender))
    existing_relation_row = db.execute("SELECT USER_1, USER_2, STATUS, D_STATUS FROM BOC_USER_RELATIONSHIPS WHERE USER_1 = ? AND USER_2 = ?", (sender, receiver)).fetchone()
    if existing_relation_row is None:
        db.execute("INSERT INTO BOC_USER_RELATIONSHIPS (USER_1, USER_2, STATUS, D_STATUS) VALUES (?, ?, \"blocked\", CURRENT_TIMESTAMP)", (sender, receiver))
    else:
        db.execute("UPDATE BOC_USER_RELATIONSHIPS SET STATUS = \"blocked\", D_STATUS = CURRENT_TIMESTAMP WHERE USER_1 = ? AND USER_2 = ?", (receiver, sender))
    db.commit()

def unblock_user(sender, receiver):
    db = get_db()
    db.execute("DELETE FROM BOC_USER_RELATIONSHIPS WHERE USER_1 = ? AND USER_2 = ? AND STATUS = \"blocked\"", (sender, receiver))
    db.commit()


# User data access aux functions

def get_pfp_source(username):
    db = get_db()
    pfp_ext_index_raw = db.execute("SELECT PROFILE_PICTURE_EXTENSION FROM BOC_USER WHERE USERNAME = ?", (username,)).fetchone()["PROFILE_PICTURE_EXTENSION"]
    try:
        pfp_ext_index = int(pfp_ext_index_raw)
        if pfp_ext_index == 0:
            # Default pfp
            return(url_for('static', filename=f"user_content/profile_pictures/_DEFAULT_USER_pfp.jpeg"))
        else:
            return(url_for('static', filename=f"user_content/profile_pictures/{username}_pfp{PFP_EXTENSIONS[pfp_ext_index]}"))
    except:
        return(url_for('static', filename=f"user_content/profile_pictures/_DEFAULT_USER_pfp.jpeg"))

# User boards actions

def hide_board(username, board_id):
    # If only this user saved the board, and it was not used for any game or challenge so far, then it is properly deleted
    # otherwise he just unsaves it, but doesn't block it
    db = get_db()
    no_one_saved_the_board_data = db.execute("SELECT 1 FROM BOC_USER_BOARD_RELATIONSHIPS WHERE BOARD_ID = ? AND USERNAME != ? LIMIT 1", (board_id, username)).fetchone()
    no_one_saved_the_board = no_one_saved_the_board_data is None
    no_chal_used_the_board_data = db.execute("SELECT 1 FROM BOC_CHALLENGES WHERE BOARD_ID = ? LIMIT 1", (board_id,)).fetchone()
    no_chal_used_the_board = no_chal_used_the_board_data is None
    no_game_used_the_board_data = db.execute("SELECT 1 FROM BOC_GAMES WHERE BOARD_ID = ? LIMIT 1", (board_id,)).fetchone()
    no_game_used_the_board = no_game_used_the_board_data is None

    if no_one_saved_the_board and no_chal_used_the_board and no_game_used_the_board:
        db.execute("DELETE FROM BOC_USER_BOARD_RELATIONSHIPS WHERE BOARD_ID = ? AND USERNAME = ?", (board_id, username))
        db.execute("DELETE FROM BOC_BOARDS WHERE BOARD_ID = ?", (board_id,))
        db.commit()
    else:
        db.execute("DELETE FROM BOC_USER_BOARD_RELATIONSHIPS WHERE BOARD_ID = ? AND USERNAME = ?", (board_id, username))
        db.commit()

# Tree document viewer actions

def tdv_edit_chapter(chapter_id, new_label, new_content):
    db = get_db()
    db.execute("UPDATE BOC_TREE_DOCUMENTS SET LABEL = ?, CONTENT = ? WHERE CHAPTER_ID = ?", (new_label, new_content, chapter_id))
    db.commit()

def tdv_add_chapter(prev_chapter_id):
    db = get_db()
    cur = db.cursor()
    # First we find the parent and next_chapter of the prev chapter
    prev_chapter_row = cur.execute("SELECT NEXT_CHAPTER, PARENT_CHAPTER, VIEWER FROM BOC_TREE_DOCUMENTS WHERE CHAPTER_ID = ?", (prev_chapter_id,)).fetchone()

    cur.execute("INSERT INTO BOC_TREE_DOCUMENTS (LABEL, CONTENT, NEXT_CHAPTER, PARENT_CHAPTER, VIEWER) VALUES (\'New chapter\', \'Change me\', ?, ?, ?)", (prev_chapter_row["NEXT_CHAPTER"], prev_chapter_row["PARENT_CHAPTER"], prev_chapter_row["VIEWER"]))
    new_chapter_id = cur.lastrowid

    cur.execute("UPDATE BOC_TREE_DOCUMENTS SET NEXT_CHAPTER = ? WHERE CHAPTER_ID = ?", (new_chapter_id, prev_chapter_id))
    db.commit()

def tdv_add_child(parent_chapter_id):
    db = get_db()
    cur = db.cursor()
    # First we find the first child and the viewer of the prev chapter
    parent_chapter_row = cur.execute("SELECT FIRST_SUBCHAPTER, VIEWER FROM BOC_TREE_DOCUMENTS WHERE CHAPTER_ID = ?", (parent_chapter_id,)).fetchone()

    cur.execute("INSERT INTO BOC_TREE_DOCUMENTS (LABEL, CONTENT, NEXT_CHAPTER, PARENT_CHAPTER, VIEWER) VALUES (\'New chapter\', \'Change me\', ?, ?, ?)", (parent_chapter_row["FIRST_SUBCHAPTER"], parent_chapter_id, parent_chapter_row["VIEWER"]))
    new_chapter_id = cur.lastrowid

    cur.execute("UPDATE BOC_TREE_DOCUMENTS SET FIRST_SUBCHAPTER = ? WHERE CHAPTER_ID = ?", (new_chapter_id, parent_chapter_id))
    db.commit()

# -----------------------------------------------------------------------------
# ------------------------ Game conclusion and rating -------------------------
# -----------------------------------------------------------------------------

def conclude_and_rate_game(game_id, outcome, draw_offer_status = None, draw_offer_condition = None):
    # outcome is A, B, or draw
    db = get_db()

    # Load game properties
    game_properties = db.execute("SELECT PLAYER_A, PLAYER_B, (R_A_INIT - R_B_INIT) AS DELTA_R, BOARD_ID FROM BOC_GAMES WHERE GAME_ID = ?", (game_id,)).fetchone()

    # rate the game
    r_a_adj, new_h, new_h_std, new_kappa, new_K = rate_game(game_id, game_properties["BOARD_ID"], game_properties["PLAYER_A"], game_properties["PLAYER_B"], game_properties["DELTA_R"], outcome)

    # Update the database
    player_A_rating_now = db.execute("SELECT RATING FROM BOC_USER WHERE USERNAME = ?", (game_properties["PLAYER_A"],)).fetchone()["RATING"]
    player_B_rating_now = db.execute("SELECT RATING FROM BOC_USER WHERE USERNAME = ?", (game_properties["PLAYER_B"],)).fetchone()["RATING"]
    db.execute("UPDATE BOC_USER SET RATING = ? WHERE USERNAME = ?", (player_A_rating_now + r_a_adj, game_properties["PLAYER_A"]))
    db.execute("UPDATE BOC_USER SET RATING = ? WHERE USERNAME = ?", (player_B_rating_now - r_a_adj, game_properties["PLAYER_B"]))

    db.execute("UPDATE BOC_BOARDS SET HANDICAP = ?, HANDICAP_STD = ?, KAPPA = ?, STEP_SIZE = ? WHERE BOARD_ID = ?", (new_h, new_h_std, new_kappa, new_K, game_properties["BOARD_ID"]))

    # mark game as concluded
    if draw_offer_status is None:
        db.execute("UPDATE BOC_GAMES SET D_FINISHED = CURRENT_TIMESTAMP, STATUS = \"concluded\", OUTCOME = ?, R_A_ADJUSTMENT = ? WHERE GAME_ID = ?", (outcome, r_a_adj, game_id))
    else:
        db.execute("UPDATE BOC_GAMES SET DRAW_OFFER_STATUS = ?, D_FINISHED = CURRENT_TIMESTAMP, STATUS = \"concluded\", OUTCOME = ?, R_A_ADJUSTMENT = ? WHERE GAME_ID = ? AND DRAW_OFFER_STATUS = ?", (draw_offer_status, outcome, r_a_adj, game_id, draw_offer_condition))

    db.commit()

def safe_power_sum(x, kappa):
    # calculates log (np.power(10, x) + np.power(10, -x) + kappa) safely
    if kappa < 0:
        return(safe_power_sum(x, 0))
    if x > 4:
        return(x * np.log(10))
    elif x < -4:
        return(-x * np.log(10))
    else:
        return(np.log(np.power(10, x) + np.power(10, -x) + kappa + 0.1))

def r_sigma(x, kappa):
    #return( np.power(10, x) / ( np.power(10, x) + np.power(10, -x) + kappa ))
    if kappa < 0:
        return(r_sigma(x, 0.0))

    return( np.exp(x * np.log(10) - safe_power_sum(x, kappa)) )

def rate_game(game_id, board_id, player_A, player_B, delta_R, outcome):
    # This function does NOT update the database, instead it returns a tuple:
    # (player A's rating adjustment, new h, new h_std, new kappa, new step size)

    db = get_db()


    # 1. Load rating model parameters
    rm_params_raw = db.execute("SELECT PARAMETER_NAME, PARAMETER_VALUE FROM BOC_RATING_PARAMETERS").fetchall()
    rm_params = {}
    for rm_param_raw in rm_params_raw:
        rm_params[rm_param_raw["PARAMETER_NAME"]] = rm_param_raw["PARAMETER_VALUE"]

    # 2. Load board hot parameters and prior game ratings
    board_hot_raw = db.execute("SELECT HANDICAP, HANDICAP_STD, KAPPA FROM BOC_BOARDS WHERE BOARD_ID = ?", (board_id,)).fetchone()
    board_hot = {
            "h" : board_hot_raw["HANDICAP"],
            "h_std" : board_hot_raw["HANDICAP_STD"],
            "kappa" : board_hot_raw["KAPPA"],
            "p_draw" : board_hot_raw["KAPPA"] / (board_hot_raw["KAPPA"] + 2.0),
        }
    board_prior_games = db.execute("SELECT (R_A_INIT - R_B_INIT) AS DELTA_R, OUTCOME FROM BOC_GAMES WHERE STATUS = \"concluded\" AND BOARD_ID = ? AND GAME_ID != ?", (board_id, game_id)).fetchall()

    # 3. Calculate the game counts and the step size
    N = db.execute("SELECT COUNT(*) AS N FROM BOC_GAMES WHERE BOC_GAMES.STATUS = \"concluded\" AND BOC_GAMES.BOARD_ID = ?", (board_id,)).fetchone()["N"]
    N_d = db.execute("SELECT COUNT(*) AS N FROM BOC_GAMES WHERE BOC_GAMES.STATUS = \"concluded\" AND BOC_GAMES.OUTCOME = \"draw\" AND BOC_GAMES.BOARD_ID = ?", (board_id,)).fetchone()["N"]
    step_size = rm_params["RATING_ADJUSTMENT_STEP_SCALE"] * N / (N + rm_params["RIGIDITY"])


    # 4. Prior estimates
    p_prior = (rm_params["INITIAL_ESTIMATE_DRAW_PROBABILITY"] + N * board_hot["p_draw"] / rm_params["RIGIDITY"]) / (1.0 + N / rm_params["RIGIDITY"])
    h_prior = N * board_hot["h"] / (N + rm_params["RIGIDITY"])
    h_std_prior = (rm_params["INITIAL_ESTIMATE_HANDICAP_STD"] + N * board_hot["h_std"] / rm_params["RIGIDITY"]) / (1.0 + N / rm_params["RIGIDITY"])

    log_regularisation = 0.01

    try:
        # 5. log-prior
        def log_prior(h, kappa):
            if kappa < 0:
                return -np.inf
            h_term = -0.5 * ((h - h_prior) / h_std_prior) * ((h - h_prior) / h_std_prior)
            kappa_term = N * p_prior * np.log(kappa + log_regularisation) - (N + 2) * np.log(kappa + 2) #regularised
            return(h_term + kappa_term)

        # 6. log-likelihood
        def log_likelihood(h, kappa):
            if kappa < 0:
                return(log_likelihood(h, 0.0))
            res_sum = 0.0
            for prior_game in board_prior_games:
                x = (prior_game["DELTA_R"] + h) / rm_params["RATING_DIFFERENCE_SCALE"]
                #power_of_x = np.power(10, x)
                #res_sum -= np.log(power_of_x + 1 / power_of_x + kappa + log_regularisation)
                res_sum -= safe_power_sum(x, kappa)
                if prior_game["OUTCOME"] == "A":
                    res_sum += x * np.log(10)
                elif prior_game["OUTCOME"] == "B":
                    res_sum -= x * np.log(10)
            return(res_sum)

        # 7. maximum of log posterior
        def log_posterior(params):

            h, kappa = params
            return(log_prior(h, kappa) + log_likelihood(h, kappa))
        max_res = minimize(
                lambda params: -log_posterior(params),
                x0 = [h_prior, 2 * p_prior / (1.0 - p_prior)],
                bounds = [(None, None), (0, None)]
            )
        h_max, kappa_max = max_res.x
        log_post_max = log_posterior(max_res.x)

        # 8. Finding bounds around the max
        bounds_factor = 5.0
        h_bounds_min = h_max - bounds_factor * h_std_prior
        h_bounds_max = h_max + bounds_factor * h_std_prior
        # we calculate approximate kappa_std from the Beta distribution properties
        kappa_std = 2 * p_prior / (N + 1)
        kappa_bounds_max = kappa_max + bounds_factor * kappa_std

        # 9. unnormalised posterior
        def unnorm_posterior(params):
            h, kappa = params
            return(np.exp( log_prior(h, kappa) + log_likelihood(h, kappa) - log_post_max ))

        # 10. Find the normalisation coefficient
        Z_raw, Z_err_raw = cubature(unnorm_posterior,
                2, 1,
                np.array([h_bounds_min, 0]), np.array([h_bounds_max, kappa_bounds_max])
            )
        Z = Z_raw[0]
        Z_err = Z_err_raw[0]

        # 11. Find the functions for all the expectation values you want to calculate
        def func_A_win(params):
            h, kappa = params
            x = (delta_R + h) / rm_params["RATING_DIFFERENCE_SCALE"]
            return( unnorm_posterior(params) * r_sigma(x, kappa) / Z)

        def func_draw(params):
            h, kappa = params
            if kappa < 0:
                return(func_draw(h, 0))
            x = (delta_R + h) / rm_params["RATING_DIFFERENCE_SCALE"]
            return( unnorm_posterior(params) * kappa / (Z * ( np.power(10, x) + np.power(10, -x) + kappa )))

        def func_h(params):
            h, kappa = params
            return( unnorm_posterior(params) * h / Z)

        def func_h_sq(params):
            h, kappa = params
            return( unnorm_posterior(params) * h * h / Z)

        def func_kappa(params):
            h, kappa = params
            return( unnorm_posterior(params) * kappa / Z)

        # 12. Find the expectationp_draw_std values
        exp_A_win_raw, exp_A_win_err_raw = cubature(func_A_win,
                2, 1,
                np.array([h_bounds_min, 0]), np.array([h_bounds_max, kappa_bounds_max])
            )
        exp_A_win = exp_A_win_raw[0]
        exp_A_win_err = exp_A_win_err_raw[0]

        exp_draw_raw, exp_draw_err_raw = cubature(func_draw,
                2, 1,
                np.array([h_bounds_min, 0]), np.array([h_bounds_max, kappa_bounds_max])
            )
        exp_draw = exp_draw_raw[0]
        exp_draw_err = exp_draw_err_raw[0]

        exp_h_raw, exp_h_err_raw = cubature(func_h,
                2, 1,
                np.array([h_bounds_min, 0]), np.array([h_bounds_max, kappa_bounds_max])
            )
        exp_h = exp_h_raw[0]
        exp_h_err = exp_h_err_raw[0]

        exp_h_sq_raw, exp_h_sq_err_raw = cubature(func_h_sq,
                2, 1,
                np.array([h_bounds_min, 0]), np.array([h_bounds_max, kappa_bounds_max])
            )
        exp_h_sq = exp_h_sq_raw[0]
        exp_h_sq_err = exp_h_sq_err_raw[0]

        exp_kappa_raw, exp_kappa_err_raw = cubature(func_kappa,
                2, 1,
                np.array([h_bounds_min, 0]), np.array([h_bounds_max, kappa_bounds_max])
            )
        exp_kappa = exp_kappa_raw[0]
        exp_kappa_err = exp_kappa_err_raw[0]

        exp_S_A = exp_A_win + 0.5 * exp_draw

        new_h_std = np.sqrt(exp_h_sq - exp_h * exp_h)

        # 13. Calculate the score of player A and their rating adjustment

        if outcome == "A":
            S_A = 1.0
        elif outcome == "B":
            S_A = 0.0
        elif outcome == "draw":
            S_A = 0.5

        R_A_adjustment = step_size * (S_A - exp_S_A)

        # 14. Log the routine and return the new values
        log_msg = f"Game rated with h_max = {h_max}, kappa_max = {kappa_max}, h bounds ({h_bounds_min}:{h_bounds_max}), kappa bounds (0:{kappa_bounds_max}), log_post_max = {log_post_max}, Z = {Z} pm {Z_err}, exp_A_win = {exp_A_win} pm {exp_A_win_err}, exp_draw = {exp_draw} pm {exp_draw_err}, exp_h = {exp_h} pm {exp_h_err}, exp_h_sq = {exp_h_sq} pm {exp_h_sq_err}, exp_kappa = {exp_kappa} pm {exp_kappa_err}; calc. result is R_A_ADJ = {R_A_adjustment}, new h = {exp_h} pm {new_h_std}, new kappa = {exp_kappa}, new step size = {step_size}"
        db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (9, \"db.rate_game\", ?)", (log_msg, ))

        # 15. If not frozen, mark the date of the earliest game on the board
        update_earliest_date = False
        if rm_params["FREEZING_CONDITION"] is None:
            update_earliest_date = True
        elif N < rm_params["FREEZING_CONDITION"]:
            update_earliest_date = True

        if update_earliest_date:
            db.execute("""
                UPDATE BOC_HOUSEKEEPING_LOGS
                    SET D_EARLIEST_RECALC = (SELECT MIN(D_FINISHED) FROM BOC_GAMES WHERE BOARD_ID = ?)
                WHERE D_PERFORMED = \"SCHEDULED\"
                """, (board_id,))


        db.commit()
        return(R_A_adjustment, exp_h, new_h_std, exp_kappa, step_size)


    except Exception as e:
        db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (4, \"db.rate_game\", ?)", (str(e),))
        db.commit()

        # We calculate the rating adjustment naively, without adjusting the handicap
        x = (delta_R + board_hot["h"]) / rm_params["RATING_DIFFERENCE_SCALE"]
        exp_S_A = ( np.power(10, x) + board_hot["kappa"] / 2.0 ) / ( np.power(10, x) + np.power(10, -x) + board_hot["kappa"] )

        if outcome == "A":
            S_A = 1.0
        elif outcome == "B":
            S_A = 0.0
        elif outcome == "draw":
            S_A = 0.5

        return(step_size * (S_A - exp_S_A), board_hot["h"], board_hot["h_std"], board_hot["kappa"], step_size)



def rating_housekeeping():
    db = get_db()

    try:
        # Start timing benchmark
        start_time = time.monotonic()

        # Find the scheduled housekeeping row
        scheduled_housekeeping_row = db.execute("SELECT PROCESS_ID, D_EARLIEST_RECALC FROM BOC_HOUSEKEEPING_LOGS WHERE D_PERFORMED = \"SCHEDULED\" LIMIT 1").fetchone()

        if scheduled_housekeeping_row is None:
            # This should never happen
            db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (2, \"db.rating_housekeeping\", \"The housekeeping daemon found no job scheduled. A housekeeping job is being scheduled automatically.\")")
            db.execute("INSERT INTO BOC_HOUSEKEEPING_LOGS (D_PERFORMED) VALUES (\"SCHEDULED\")")
            db.commit()
            close_db()
            return(-1)

        # Select the total number of games, boards, and users, for stats.
        total_games = db.execute("SELECT COUNT(*) AS COUNT_GAMES FROM BOC_GAMES WHERE STATUS = \"concluded\"").fetchone()["COUNT_GAMES"]
        total_boards = db.execute("SELECT COUNT(*) AS COUNT_BOARDS FROM BOC_BOARDS WHERE IS_PUBLIC = 1").fetchone()["COUNT_BOARDS"]
        total_users = db.execute("SELECT COUNT(*) AS COUNT_USERS FROM BOC_USER WHERE STATUS = \"active\"").fetchone()["COUNT_USERS"]

        if scheduled_housekeeping_row["D_EARLIEST_RECALC"] is None:
            # No user interaction warranted any recalculations (possibly due to zero game submissions). This is fine.
            db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (9, \"db.rating_housekeeping\", \"No user interaction warranted any recalculations (possibly due to zero game submissions). This is fine.\")")
            db.execute("UPDATE BOC_HOUSEKEEPING_LOGS SET D_PERFORMED = CURRENT_TIMESTAMP, TIME_TAKEN = 0, GAMES_AFFECTED = 0, USERS_AFFECTED = 0, BOARDS_AFFECTED = 0, GAMES_TOTAL = ?, USERS_TOTAL = ?, BOARDS_TOTAL = ? WHERE PROCESS_ID = ?", (total_games, total_users, total_boards, scheduled_housekeeping_row["PROCESS_ID"]))
            # Schedule the next job
            db.execute("INSERT INTO BOC_HOUSEKEEPING_LOGS (D_PERFORMED) VALUES (\"SCHEDULED\")")
            db.commit()
            close_db()
            return(0)

        # Now we know there is a job scheduled which asks for a recalculation. Let's go.
        count_affected_games = db.execute("SELECT COUNT(*) AS AFFECTED_GAMES FROM BOC_GAMES WHERE STATUS = \"concluded\" AND D_FINISHED > :d_recalc", {"d_recalc" : scheduled_housekeeping_row["D_EARLIEST_RECALC"]}).fetchone()["AFFECTED_GAMES"]
        if count_affected_games == 0:
            # No game was affected
            db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (9, \"db.rating_housekeeping\", \"No game was affected by scheduled recalculation. This is fine.\")")
            db.execute("UPDATE BOC_HOUSEKEEPING_LOGS SET D_PERFORMED = CURRENT_TIMESTAMP, TIME_TAKEN = 0, GAMES_AFFECTED = 0, USERS_AFFECTED = 0, BOARDS_AFFECTED = 0, GAMES_TOTAL = ?, USERS_TOTAL = ?, BOARDS_TOTAL = ? WHERE PROCESS_ID = ?", (total_games, total_users, total_boards, scheduled_housekeeping_row["PROCESS_ID"]))
            # Schedule the next job
            db.execute("INSERT INTO BOC_HOUSEKEEPING_LOGS (D_PERFORMED) VALUES (\"SCHEDULED\")")
            db.commit()
            close_db()
            return(0)

        # We create a temp table of affected users
        initial_rating = db.execute("SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_RATING\"").fetchone()["PARAMETER_VALUE"]
        db.execute("DROP TABLE IF EXISTS HK_USERS")
        db.execute("""
            CREATE TEMP TABLE HK_USERS (
                USERNAME TEXT PRIMARY KEY,
                RATING REAL
            )
            """)
        db.execute("""
            INSERT INTO HK_USERS (USERNAME, RATING)
            SELECT DISTINCT username, NULL
            FROM (
                SELECT PLAYER_A AS username
                FROM BOC_GAMES
                WHERE STATUS = \"concluded\"
                AND D_FINISHED > :d_recalc
                UNION
                SELECT PLAYER_B AS username
                FROM BOC_GAMES
                WHERE STATUS = \"concluded\"
                AND D_FINISHED > :d_recalc
            )
            """, {"d_recalc" : scheduled_housekeeping_row["D_EARLIEST_RECALC"]})

        count_affected_users = db.execute("SELECT COUNT(*) AS AFFECTED_USERS FROM HK_USERS").fetchone()["AFFECTED_USERS"]

        # We now sum up all the rating differences from games which are NOT to be recalculated, to reach the "snapshotted" hot values of player rating for affected players
        db.execute("""
            WITH RATING_ADJUSTMENTS AS (
                SELECT PLAYER_A AS USERNAME, IFNULL(SUM(R_A_ADJUSTMENT), 0) AS TOTAL
                FROM BOC_GAMES
                WHERE STATUS = \"concluded\" AND D_FINISHED <= :d_recalc
                GROUP BY PLAYER_A
                UNION ALL
                SELECT PLAYER_B AS USERNAME, IFNULL(SUM(-R_A_ADJUSTMENT), 0) AS TOTAL
                FROM BOC_GAMES
                WHERE STATUS = \"concluded\" AND D_FINISHED <= :d_recalc
                GROUP BY PLAYER_B
            ),
            AGGREGATED_ADJUSTMENT AS (
                SELECT USERNAME, SUM(TOTAL) AS TOTAL
                FROM RATING_ADJUSTMENTS
                GROUP BY USERNAME
            )
            UPDATE HK_USERS
            SET RATING = (:r_init
                + COALESCE((SELECT TOTAL FROM AGGREGATED_ADJUSTMENT WHERE AGGREGATED_ADJUSTMENT.USERNAME = HK_USERS.USERNAME), 0)
            )
            """, {"r_init" : initial_rating, "d_recalc" : scheduled_housekeeping_row["D_EARLIEST_RECALC"]})

        # now we loop through affected games ordered by D_FINISHED and calculate the new rating adjustments
        affected_games = db.execute("""
            SELECT
                BOC_GAMES.GAME_ID AS GAME_ID, BOC_GAMES.PLAYER_A AS PLAYER_A, BOC_GAMES.PLAYER_B AS PLAYER_B, BOC_GAMES.OUTCOME AS OUTCOME,
                BOC_BOARDS.HANDICAP AS HANDICAP, BOC_BOARDS.KAPPA AS KAPPA, BOC_BOARDS.STEP_SIZE AS STEP_SIZE
            FROM
                BOC_GAMES
                INNER JOIN BOC_BOARDS ON BOC_BOARDS.BOARD_ID = BOC_GAMES.BOARD_ID
            WHERE BOC_GAMES.STATUS = \"concluded\" AND BOC_GAMES.D_FINISHED > :d_recalc
            ORDER BY D_FINISHED ASC
            """, {"d_recalc" : scheduled_housekeeping_row["D_EARLIEST_RECALC"]}).fetchall()

        count_affected_boards = db.execute("SELECT COUNT(DISTINCT BOARD_ID) AS AFFECTED_BOARDS FROM BOC_GAMES WHERE BOC_GAMES.STATUS = \"concluded\" AND BOC_GAMES.D_FINISHED > :d_recalc", {"d_recalc" : scheduled_housekeeping_row["D_EARLIEST_RECALC"]}).fetchone()["AFFECTED_BOARDS"]

        # Initialise dicts for intermediate updates
        dict_hk_users = {row["USERNAME"] : row["RATING"] for row in db.execute("SELECT USERNAME, RATING FROM HK_USERS").fetchall()}
        dict_game_updates = {}

        rating_difference_scale = db.execute("SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"RATING_DIFFERENCE_SCALE\"").fetchone()["PARAMETER_VALUE"]

        for affected_game in affected_games:
            # We calculate the new rating
            delta_R = dict_hk_users[affected_game["PLAYER_A"]] - dict_hk_users[affected_game["PLAYER_B"]]
            x = (delta_R + affected_game["HANDICAP"]) / rating_difference_scale
            exp_S_A = ( np.power(10, x) + affected_game["KAPPA"] / 2.0 ) / ( np.power(10, x) + np.power(10, -x) + affected_game["KAPPA"] )

            S_A = {"A": 1.0, "B": 0.0, "draw": 0.5}[affected_game["OUTCOME"]]

            new_rating_adj = affected_game["STEP_SIZE"] * (S_A - exp_S_A)
            dict_game_updates[affected_game["GAME_ID"]] = new_rating_adj
            dict_hk_users[affected_game["PLAYER_A"]] += new_rating_adj
            dict_hk_users[affected_game["PLAYER_B"]] -= new_rating_adj

        db.executemany(
            "UPDATE BOC_USER SET RATING = ? WHERE USERNAME = ?",
            [(r, u) for u, r in dict_hk_users.items()]
        )
        db.executemany(
            "UPDATE BOC_GAMES SET R_A_ADJUSTMENT = ? WHERE GAME_ID = ?",
            [(r, g) for g, r in dict_game_updates.items()]
        )

        # Note down benchmark time
        end_time = time.monotonic()
        elapsed_ms = int((end_time - start_time) * 1000)

        # Now update the log and schedule a new job
        db.execute("UPDATE BOC_HOUSEKEEPING_LOGS SET D_PERFORMED = CURRENT_TIMESTAMP, TIME_TAKEN = ?, GAMES_AFFECTED = ?, USERS_AFFECTED = ?, BOARDS_AFFECTED = ?, GAMES_TOTAL = ?, USERS_TOTAL = ?, BOARDS_TOTAL = ? WHERE PROCESS_ID = ?", (elapsed_ms, count_affected_games, count_affected_users, count_affected_boards, total_games, total_users, total_boards, scheduled_housekeeping_row["PROCESS_ID"]))
        db.execute("INSERT INTO BOC_HOUSEKEEPING_LOGS (D_PERFORMED) VALUES (\"SCHEDULED\")")
        db.commit()
    except Exception as e:
        db.rollback()
        db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (2, \"db.rating_housekeeping\", ?)", (str(e),))
        db.commit()

    close_db()
    return(0)







