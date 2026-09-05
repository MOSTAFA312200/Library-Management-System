from database import get_connection
from werkzeug.security import check_password_hash


def authenticate_user(username, password):
    connection = get_connection()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    connection.close()

    if user is None:
        return None

    if not check_password_hash(user["password_hash"], password):
        return None

    return user
