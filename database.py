import sqlite3
from werkzeug.security import generate_password_hash


DATABASE_NAME = "library.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    # =====================================================
    # Users Table
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member'
                CHECK(role IN ('member', 'librarian')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # Books Table
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            isbn TEXT NOT NULL UNIQUE,
            description TEXT,
            available INTEGER NOT NULL DEFAULT 1
        )
    """)

    # =====================================================
    # Membership Requests Table
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS membership_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # Borrowings Table
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrowings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            book_id INTEGER NOT NULL,

            borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            returned_at TIMESTAMP NULL,

            status TEXT NOT NULL DEFAULT 'borrowed'
                CHECK(status IN ('borrowed', 'returned')),

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (book_id)
                REFERENCES books(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # Default Librarian
    # =====================================================

    cursor.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, ("admin",))

    librarian = cursor.fetchone()

    if librarian is None:

        cursor.execute("""
            INSERT INTO users
            (
                full_name,
                username,
                email,
                password_hash,
                role
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Library Administrator",
            "admin",
            "admin@library.com",
            generate_password_hash("admin123"),
            "librarian"
        ))

    # =====================================================
    # Demo Books
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM books
    """)

    book_count = cursor.fetchone()["count"]

    if book_count == 0:

        books = [

            (
                "Clean Code",
                "Robert C. Martin",
                "Programming",
                "9780132350884",
                "A practical guide to writing clean and maintainable code."
            ),

            (
                "Python Crash Course",
                "Eric Matthes",
                "Programming",
                "9781593279288",
                "A hands-on introduction to Python programming."
            ),

            (
                "Artificial Intelligence",
                "Stuart Russell",
                "Artificial Intelligence",
                "9780134610993",
                "An introduction to artificial intelligence concepts."
            ),

            (
                "Database System Concepts",
                "Abraham Silberschatz",
                "Database",
                "9780078022159",
                "Fundamentals of database systems and database management."
            )
        ]

        cursor.executemany("""
            INSERT INTO books
            (
                title,
                author,
                category,
                isbn,
                description
            )
            VALUES (?, ?, ?, ?, ?)
        """, books)

    connection.commit()
    connection.close()


# =========================================================
# Reset Member Password
# =========================================================

def reset_member_password(username, new_password):

    connection = get_connection()

    cursor = connection.cursor()

    password_hash = generate_password_hash(new_password)

    cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE username = ?
          AND role = 'member'
    """, (
        password_hash,
        username
    ))

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated