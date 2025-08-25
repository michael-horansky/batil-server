import os

from flask import Flask

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
        DATABASE=os.path.join(app.instance_path, 'batil.sqlite'),
    )

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
    from . import auth
    app.register_blueprint(auth.bp)

    # Game blueprint and id converter
    # Register converter
    app.url_map.converters['regex'] = RegexConverter
    from . import game
    app.register_blueprint(game.bp)

    # Home blueprint
    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index')

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
