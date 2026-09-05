from database import get_connection


def borrow_book(user_id, book_id):
    connection = get_connection()

    book = connection.execute("""
        SELECT *
        FROM books
        WHERE id = ?
    """, (book_id,)).fetchone()

    if book is None:
        connection.close()
        return False, "Book not found."

    if book["available"] == 0:
        connection.close()
        return False, "Book is not available."

    active_borrowing = connection.execute("""
        SELECT id
        FROM borrowings
        WHERE user_id = ?
          AND book_id = ?
          AND status = 'borrowed'
    """, (
        user_id,
        book_id
    )).fetchone()

    if active_borrowing:
        connection.close()
        return False, "You already borrowed this book."

    connection.execute("""
        INSERT INTO borrowings
        (
            user_id,
            book_id,
            status
        )
        VALUES (?, ?, 'borrowed')
    """, (
        user_id,
        book_id
    ))

    connection.execute("""
        UPDATE books
        SET available = 0
        WHERE id = ?
    """, (book_id,))

    connection.commit()
    connection.close()

    return True, "Book borrowed successfully."


def return_book(borrowing_id, user_id):
    connection = get_connection()

    borrowing = connection.execute("""
        SELECT *
        FROM borrowings
        WHERE id = ?
          AND user_id = ?
          AND status = 'borrowed'
    """, (
        borrowing_id,
        user_id
    )).fetchone()

    if borrowing is None:
        connection.close()
        return False

    connection.execute("""
        UPDATE borrowings
        SET status = 'returned',
            returned_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (borrowing_id,))

    connection.execute("""
        UPDATE books
        SET available = 1
        WHERE id = ?
    """, (borrowing["book_id"],))

    connection.commit()
    connection.close()

    return True


def get_user_borrowing_history(user_id):
    connection = get_connection()

    borrowings = connection.execute("""
        SELECT
            b.id,
            b.borrowed_at,
            b.returned_at,
            b.status,
            books.title,
            books.author,
            books.isbn
        FROM borrowings b
        JOIN books
            ON b.book_id = books.id
        WHERE b.user_id = ?
        ORDER BY b.borrowed_at DESC
    """, (user_id,)).fetchall()

    connection.close()

    return borrowings


def get_library_history():
    connection = get_connection()

    history = connection.execute("""
        SELECT
            b.id,
            b.borrowed_at,
            b.returned_at,
            b.status,

            users.full_name,
            users.username,

            books.title,
            books.author,
            books.isbn

        FROM borrowings b

        JOIN users
            ON b.user_id = users.id

        JOIN books
            ON b.book_id = books.id

        ORDER BY b.borrowed_at DESC
    """).fetchall()

    connection.close()

    return history


def get_borrowing_statistics():
    connection = get_connection()

    total_borrowings = connection.execute("""
        SELECT COUNT(*) AS count
        FROM borrowings
    """).fetchone()["count"]

    active_borrowings = connection.execute("""
        SELECT COUNT(*) AS count
        FROM borrowings
        WHERE status = 'borrowed'
    """).fetchone()["count"]

    returned_borrowings = connection.execute("""
        SELECT COUNT(*) AS count
        FROM borrowings
        WHERE status = 'returned'
    """).fetchone()["count"]

    connection.close()

    return {
        "total_borrowings": total_borrowings,
        "active_borrowings": active_borrowings,
        "returned_borrowings": returned_borrowings
    }