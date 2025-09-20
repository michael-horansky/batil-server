
from batil import create_app
from batil.db import rating_housekeeping

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        rating_housekeeping()
