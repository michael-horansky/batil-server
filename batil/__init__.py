import os

from flask import Flask
#from batil.batil_flask_extensions import mail

from werkzeug.routing import BaseConverter

# Custom regex converter, to automatically reject game_ids which do not match the regex
class RegexConverter(BaseConverter):
    def __init__(self, map, *items):
        super().__init__(map)
        self.regex = items[0]

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        SESSION_COOKIE_NAME=os.getenv("SESSION_COOKIE_NAME", "session"),
        DATABASE=os.path.join(app.instance_path, 'batil.sqlite'),
    )

    # Initialise mail server
    """app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='noreply@batil.com',
        MAIL_PASSWORD='loopinsohard',
        MAIL_DEFAULT_SENDER=('Batil', 'noreply@batil.com')
    )"""

    #mail.init_app(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # init database
    from . import db
    db.init_app(app)

    # BLUEPRINTS
    # Authentification blueprint
    from .routes import auth
    app.register_blueprint(auth.bp)

    # Game blueprint and id converter
    # Register converter
    app.url_map.converters['regex'] = RegexConverter
    from .routes import game
    app.register_blueprint(game.bp)

    # Board editor blueprint
    from .routes import board_editor
    app.register_blueprint(board_editor.bp)

    # Board editor blueprint
    from .routes import tutorial
    app.register_blueprint(tutorial.bp)

    # User viewer blueprint
    from .routes import user
    app.register_blueprint(user.bp)

    # Admin access point blueprint
    from .routes import admin
    app.register_blueprint(admin.bp)

    # Home blueprint
    from .routes import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index')

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
