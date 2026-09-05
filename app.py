from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database import get_connection, init_database
from auth_service import authenticate_user
from book_service import (
    get_all_books,
    get_book_by_id,
    add_book as service_add_book,
    update_book as service_update_book,
    delete_book as service_delete_book
)
from member_service import (
    username_exists,
    email_exists,
    create_membership_request,
    get_all_members,
    get_membership_requests,
    approve_membership as service_approve_membership,
    reject_membership as service_reject_membership
)
from borrowing_service import (
    borrow_book as service_borrow_book,
    return_book as service_return_book,
    get_user_borrowing_history,
    get_library_history,
    get_borrowing_statistics
)


app = Flask(__name__)

app.secret_key = "library-management-system-secret-key"


# =========================================================
# Authentication
# =========================================================

def login_required(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "danger")
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapper


def librarian_required(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "danger")
            return redirect(url_for("login"))

        if session.get("role") != "librarian":
            flash("Librarian access required.", "danger")
            return redirect(url_for("home"))

        return view_function(*args, **kwargs)

    return wrapper


# =========================================================
# Home
# =========================================================

@app.route("/")
def home():
    return render_template("home.html")


# =========================================================
# Books
# =========================================================

@app.route("/books")
def books():

    search = request.args.get("search", "").strip()

    books_list = get_all_books(search)

    return render_template(
        "books.html",
        books=books_list,
        search=search
    )


@app.route("/books/<int:book_id>")
def book_details(book_id):

    book = get_book_by_id(book_id)

    if book is None:
        flash("Book not found.", "danger")
        return redirect(url_for("books"))

    return render_template(
        "book_details.html",
        book=book
    )


# =========================================================
# Membership Registration
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not all([
            full_name,
            phone,
            address,
            username,
            email,
            password
        ]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )
            return redirect(url_for("register"))

        if username_exists(username) or email_exists(email):

            flash(
                "Username or email already exists.",
                "danger"
            )

            return redirect(url_for("register"))

        try:

            create_membership_request(
                full_name,
                phone,
                address,
                username,
                email,
                password
            )

            flash(
                "Membership request submitted successfully.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception:

            flash(
                "Username or email already exists.",
                "danger"
            )

            return redirect(url_for("register"))

    return render_template("register.html")


# =========================================================
# Login
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:

            flash(
                "Please enter username and password.",
                "danger"
            )

            return redirect(url_for("login"))

        user = authenticate_user(username, password)

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            flash(
                "Login successful.",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template("login.html")


# =========================================================
# Logout
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("home"))


# =========================================================
# Dashboard
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    if session.get("role") == "librarian":
        return redirect(url_for("librarian_dashboard"))

    return render_template("member_dashboard.html")


# =========================================================
# Librarian Dashboard
# =========================================================

@app.route("/librarian")
@librarian_required
def librarian_dashboard():

    connection = get_connection()

    books_count = connection.execute("""
        SELECT COUNT(*) AS count
        FROM books
    """).fetchone()["count"]

    available_books = connection.execute("""
        SELECT COUNT(*) AS count
        FROM books
        WHERE available = 1
    """).fetchone()["count"]

    members_count = connection.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'member'
    """).fetchone()["count"]

    pending_requests = connection.execute("""
        SELECT COUNT(*) AS count
        FROM membership_requests
        WHERE status = 'pending'
    """).fetchone()["count"]

    connection.close()

    return render_template(
        "librarian_dashboard.html",
        books_count=books_count,
        available_books=available_books,
        members_count=members_count,
        pending_requests=pending_requests
    )


# =========================================================
# Admin - Books
# =========================================================

@app.route("/admin/books")
@librarian_required
def admin_books():

    books_list = get_all_books()

    return render_template(
        "admin_books.html",
        books=books_list
    )


@app.route("/admin/books/add", methods=["POST"])
@librarian_required
def add_book():

    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    category = request.form.get("category", "").strip()
    isbn = request.form.get("isbn", "").strip()
    description = request.form.get("description", "").strip()

    if not all([title, author, category, isbn]):

        flash(
            "Please fill in all required book fields.",
            "danger"
        )

        return redirect(url_for("admin_books"))

    try:

        service_add_book(
            title,
            author,
            category,
            isbn,
            description
        )

        flash(
            "Book added successfully.",
            "success"
        )

    except Exception:

        flash(
            "ISBN already exists.",
            "danger"
        )

    return redirect(url_for("admin_books"))


@app.route(
    "/admin/books/edit/<int:book_id>",
    methods=["GET", "POST"]
)
@librarian_required
def edit_book(book_id):

    book = get_book_by_id(book_id)

    if book is None:

        flash(
            "Book not found.",
            "danger"
        )

        return redirect(url_for("admin_books"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        isbn = request.form.get("isbn", "").strip()
        description = request.form.get("description", "").strip()

        if not all([title, author, category, isbn]):

            flash(
                "Please fill in all required fields.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_book",
                    book_id=book_id
                )
            )

        try:

            service_update_book(
                book_id,
                title,
                author,
                category,
                isbn,
                description
            )

            flash(
                "Book updated successfully.",
                "success"
            )

        except Exception:

            flash(
                "ISBN already exists.",
                "danger"
            )

        return redirect(url_for("admin_books"))

    return render_template(
        "edit_book.html",
        book=book
    )


@app.route(
    "/admin/books/delete/<int:book_id>",
    methods=["POST"]
)
@librarian_required
def delete_book(book_id):

    deleted = service_delete_book(book_id)

    if not deleted:

        flash(
            "Cannot delete a book while it is borrowed.",
            "danger"
        )

        return redirect(url_for("admin_books"))

    flash(
        "Book deleted successfully.",
        "success"
    )

    return redirect(url_for("admin_books"))


# =========================================================
# Manage Members
# =========================================================

@app.route("/admin/members")
@librarian_required
def manage_members():

    members = get_all_members()

    return render_template(
        "admin_members.html",
        members=members
    )


# =========================================================
# Membership Requests
# =========================================================

@app.route("/admin/requests")
@librarian_required
def membership_requests():

    requests_list = get_membership_requests()

    return render_template(
        "admin_requests.html",
        requests=requests_list
    )


@app.route(
    "/admin/requests/<int:request_id>/approve",
    methods=["POST"]
)
@librarian_required
def approve_membership(request_id):

    try:

        approved = service_approve_membership(request_id)

        if approved:

            flash(
                "Membership approved. Member account created.",
                "success"
            )

        else:

            flash(
                "Membership request not found.",
                "danger"
            )

    except Exception:

        flash(
            "Username or email already belongs to a user.",
            "danger"
        )

    return redirect(url_for("membership_requests"))


@app.route(
    "/admin/requests/<int:request_id>/reject",
    methods=["POST"]
)
@librarian_required
def reject_membership(request_id):

    rejected = service_reject_membership(request_id)

    if rejected:

        flash(
            "Membership request rejected.",
            "success"
        )

    else:

        flash(
            "Membership request not found.",
            "danger"
        )

    return redirect(url_for("membership_requests"))


# =========================================================
# Borrow Book
# =========================================================

@app.route(
    "/books/<int:book_id>/borrow",
    methods=["POST"]
)
@login_required
def borrow_book(book_id):

    if session.get("role") != "member":

        flash(
            "Only members can borrow books.",
            "danger"
        )

        return redirect(
            url_for(
                "book_details",
                book_id=book_id
            )
        )

    success, message = service_borrow_book(
        session["user_id"],
        book_id
    )

    if success:

        flash(message, "success")

        return redirect(
            url_for("borrowing_history")
        )

    flash(message, "danger")

    return redirect(
        url_for(
            "book_details",
            book_id=book_id
        )
    )


# =========================================================
# Return Book
# =========================================================

@app.route(
    "/borrowings/<int:borrowing_id>/return",
    methods=["POST"]
)
@login_required
def return_book(borrowing_id):

    returned = service_return_book(
        borrowing_id,
        session["user_id"]
    )

    if not returned:

        flash(
            "Borrowing record not found.",
            "danger"
        )

        return redirect(
            url_for("borrowing_history")
        )

    flash(
        "Book returned successfully.",
        "success"
    )

    return redirect(
        url_for("borrowing_history")
    )


# =========================================================
# Borrowing History
# =========================================================

@app.route("/borrowings")
@login_required
def borrowing_history():

    borrowings = get_user_borrowing_history(
        session["user_id"]
    )

    return render_template(
        "borrowing_history.html",
        borrowings=borrowings
    )


# =========================================================
# Library History
# =========================================================

@app.route("/admin/history")
@librarian_required
def library_history():

    history = get_library_history()

    return render_template(
        "library_history.html",
        history=history
    )


# =========================================================
# Reports
# =========================================================

@app.route("/admin/reports")
@librarian_required
def reports():

    connection = get_connection()

    total_books = connection.execute("""
        SELECT COUNT(*) AS count
        FROM books
    """).fetchone()["count"]

    available_books = connection.execute("""
        SELECT COUNT(*) AS count
        FROM books
        WHERE available = 1
    """).fetchone()["count"]

    borrowed_books = connection.execute("""
        SELECT COUNT(*) AS count
        FROM books
        WHERE available = 0
    """).fetchone()["count"]

    total_members = connection.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'member'
    """).fetchone()["count"]

    pending_requests = connection.execute("""
        SELECT COUNT(*) AS count
        FROM membership_requests
        WHERE status = 'pending'
    """).fetchone()["count"]

    connection.close()

    borrowing_stats = get_borrowing_statistics()

    return render_template(
        "reports.html",
        total_books=total_books,
        available_books=available_books,
        borrowed_books=borrowed_books,
        total_members=total_members,
        total_borrowings=borrowing_stats["total_borrowings"],
        active_borrowings=borrowing_stats["active_borrowings"],
        returned_borrowings=borrowing_stats["returned_borrowings"],
        pending_requests=pending_requests
    )


# =========================================================
# Run Application
# =========================================================

if __name__ == "__main__":

    init_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )