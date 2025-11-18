from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from batil import create_app

# Your actual Flask app
flask_app = create_app({"CONFIG_FILE": "config_prod.py"})

# Fix proxy headers (crucial for SCRIPT_NAME)
flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_prefix=1)

# Dispatcher routes /batil → flask_app
# and uses a tiny lambda for the default root app
def empty_app(environ, start_response):
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']

app = DispatcherMiddleware(
    empty_app,
    {
        '/batil': flask_app
    }
)
