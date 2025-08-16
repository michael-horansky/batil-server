import os
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
    # Create table structure
    with current_app.open_resource('database/boc_db_init_sqlite.sql') as f:
        db.executescript(f.read().decode('utf8'))
    # Populate with static data
    with current_app.open_resource('database/boc_db_static_data.sql') as f:
        db.executescript(f.read().decode('utf8'))
    # Default admin user
    db.execute(f"INSERT INTO BOC_USER VALUES( 'admin', 'dvojka@110zbor.sk', '{generate_password_hash('Allegro4Ever')}', 'omitted', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, 'ADMIN', 'ACTIVE' )")
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
