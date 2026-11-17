"""Shared isolated database setup; import before importing the application."""
import atexit
import os
import tempfile

# Configure isolated SQLite before importing app, which creates tables at import.
_db_file = tempfile.NamedTemporaryFile(prefix="team-task-test-", suffix=".sqlite", delete=False)
_db_file.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _db_file.name
os.environ["SECRET_KEY"] = "test-secret-not-for-production"

from app import app, db, User  # noqa: E402


def close_test_database():
    """Release pooled SQLite connections and remove the temporary test DB."""
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    try:
        os.unlink(_db_file.name)
    except FileNotFoundError:
        pass


atexit.register(close_test_database)

