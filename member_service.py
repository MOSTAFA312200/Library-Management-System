from database import get_connection
from werkzeug.security import generate_password_hash


def get_all_members():
    connection = get_connection()

    members = connection.execute("""
        SELECT
            u.id,
            u.full_name,
            u.username,
            u.email,
            u.created_at,
            COUNT(b.id) AS borrowing_count
        FROM users u
        LEFT JOIN borrowings b
            ON u.id = b.user_id
        WHERE u.role = 'member'
        GROUP BY u.id
        ORDER BY u.id DESC
    """).fetchall()

    connection.close()

    return members


def get_member_by_id(member_id):
    connection = get_connection()

    member = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
          AND role = 'member'
    """, (member_id,)).fetchone()

    connection.close()

    return member


def get_member_by_username(username):
    connection = get_connection()

    member = connection.execute("""
        SELECT *
        FROM users
        WHERE username = ?
          AND role = 'member'
    """, (username,)).fetchone()

    connection.close()

    return member


def username_exists(username):
    connection = get_connection()

    user = connection.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    connection.close()

    return user is not None


def email_exists(email):
    connection = get_connection()

    user = connection.execute("""
        SELECT id
        FROM users
        WHERE email = ?
    """, (email,)).fetchone()

    connection.close()

    return user is not None


def get_membership_requests(status=None):
    connection = get_connection()

    if status:
        requests = connection.execute("""
            SELECT *
            FROM membership_requests
            WHERE status = ?
            ORDER BY id DESC
        """, (status,)).fetchall()
    else:
        requests = connection.execute("""
            SELECT *
            FROM membership_requests
            ORDER BY id DESC
        """).fetchall()

    connection.close()

    return requests


def create_membership_request(
    full_name,
    phone,
    address,
    username,
    email,
    password
):
    connection = get_connection()

    password_hash = generate_password_hash(password)

    connection.execute("""
        INSERT INTO membership_requests
        (
            full_name,
            phone,
            address,
            username,
            email,
            password_hash
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        full_name,
        phone,
        address,
        username,
        email,
        password_hash
    ))

    connection.commit()
    connection.close()


def approve_membership(request_id):
    connection = get_connection()

    membership_request = connection.execute("""
        SELECT *
        FROM membership_requests
        WHERE id = ?
    """, (request_id,)).fetchone()

    if membership_request is None:
        connection.close()
        return False

    connection.execute("""
        INSERT INTO users
        (
            full_name,
            username,
            email,
            password_hash,
            role
        )
        VALUES (?, ?, ?, ?, 'member')
    """, (
        membership_request["full_name"],
        membership_request["username"],
        membership_request["email"],
        membership_request["password_hash"]
    ))

    connection.execute("""
        UPDATE membership_requests
        SET status = 'approved'
        WHERE id = ?
    """, (request_id,))

    connection.commit()
    connection.close()

    return True


def reject_membership(request_id):
    connection = get_connection()

    connection.execute("""
        UPDATE membership_requests
        SET status = 'rejected'
        WHERE id = ?
    """, (request_id,))

    connection.commit()

    updated = connection.total_changes

    connection.close()

    return updated > 0