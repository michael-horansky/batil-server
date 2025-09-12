import os
import json
import random
import string
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
    cur.execute(f"INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, D_CREATED, D_CHANGED, PRIVILEGE, STATUS, PROFILE_PICTURE_EXTENSION) VALUES( 'batil', 'dvojka@110zbor.sk', '{generate_password_hash('loopinsohard')}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ADMIN', 'ACTIVE', 1 )")
    cur.execute(f"INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, D_CREATED, D_CHANGED, PRIVILEGE, STATUS, PROFILE_PICTURE_EXTENSION) VALUES( 'dvojka110', 'dvojka@110zbor.sk', '{generate_password_hash('Allegro4Ever')}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ADMIN', 'ACTIVE', 2 )")
    #cur.execute("INSERT INTO BOC_USER_RELATIONSHIPS (USER_1, USER_2, STATUS, D_STATUS) VALUES('batil', 'dvojka110', 'friends', CURRENT_TIMESTAMP)")

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
        "INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, AUTH_CODE, N_FAILS, D_CREATED, D_CHANGED, PRIVILEGE, STATUS) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, \'USER\', \'PENDING\')",
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
    # otherwise he just unsaves it
    db = get_db()
    no_one_saved_the_board_data = db.execute("SELECT 1 FROM BOC_USER_SAVED_BOARDS WHERE BOARD_ID = ? AND USERNAME != ? LIMIT 1", (board_id, username)).fetchone()
    no_one_saved_the_board = no_one_saved_the_board_data is None
    no_chal_used_the_board_data = db.execute("SELECT 1 FROM BOC_CHALLENGES WHERE BOARD_ID = ? LIMIT 1", (board_id,)).fetchone()
    no_chal_used_the_board = no_chal_used_the_board_data is None
    no_game_used_the_board_data = db.execute("SELECT 1 FROM BOC_GAMES WHERE BOARD_ID = ? LIMIT 1", (board_id,)).fetchone()
    no_game_used_the_board = no_game_used_the_board_data is None

    if no_one_saved_the_board and no_chal_used_the_board and no_game_used_the_board:
        db.execute("DELETE FROM BOC_USER_SAVED_BOARDS WHERE BOARD_ID = ? AND USERNAME = ?", (board_id, username))
        db.execute("DELETE FROM BOC_BOARDS WHERE BOARD_ID = ?", (board_id,))
        db.commit()
    else:
        db.execute("DELETE FROM BOC_USER_SAVED_BOARDS WHERE BOARD_ID = ? AND USERNAME = ?", (board_id, username))
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


