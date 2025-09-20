# Entry point for WSGI

from batil import create_app

app = create_app({"CONFIG_FILE" : "config_prod.py"})
