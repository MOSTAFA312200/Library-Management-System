from database import get_connection


def get_all_books(search=""):
    connection = get_connection()

    if search:
        search_value = f"%{search}%"

        books = connection.execute("""
            SELECT *
            FROM books
            WHERE title LIKE ?
               OR author LIKE ?
               OR category LIKE ?
               OR isbn LIKE ?
            ORDER BY id DESC
        """, (
            search_value,
            search_value,
            search_value,
            search_value
        )).fetchall()
    else:
        books = connection.execute("""
            SELECT *
            FROM books
            ORDER BY id DESC
        """).fetchall()

    connection.close()

    return books


def get_book_by_id(book_id):
    connection = get_connection()

    book = connection.execute("""
        SELECT *
        FROM books
        WHERE id = ?
    """, (book_id,)).fetchone()

    connection.close()

    return book


def add_book(title, author, category, isbn, description):
    connection = get_connection()

    connection.execute("""
        INSERT INTO books
        (
            title,
            author,
            category,
            isbn,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        title,
        author,
        category,
        isbn,
        description
    ))

    connection.commit()
    connection.close()


def update_book(book_id, title, author, category, isbn, description):
    connection = get_connection()

    connection.execute("""
        UPDATE books
        SET title = ?,
            author = ?,
            category = ?,
            isbn = ?,
            description = ?
        WHERE id = ?
    """, (
        title,
        author,
        category,
        isbn,
        description,
        book_id
    ))

    connection.commit()
    connection.close()


def delete_book(book_id):
    connection = get_connection()

    active_borrowing = connection.execute("""
        SELECT id
        FROM borrowings
        WHERE book_id = ?
          AND status = 'borrowed'
    """, (book_id,)).fetchone()

    if active_borrowing:
        connection.close()
        return False

    connection.execute("""
        DELETE FROM books
        WHERE id = ?
    """, (book_id,))

    connection.commit()
    connection.close()

    return True


def is_book_available(book_id):
    connection = get_connection()

    book = connection.execute("""
        SELECT available
        FROM books
        WHERE id = ?
    """, (book_id,)).fetchone()

    connection.close()

    if book is None:
        return False

    return bool(book["available"])


def set_book_availability(book_id, available):
    connection = get_connection()

    connection.execute("""
        UPDATE books
        SET available = ?
        WHERE id = ?
    """, (
        1 if available else 0,
        book_id
    ))

    connection.commit()
    connection.close()