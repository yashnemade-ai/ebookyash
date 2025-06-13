# app.py  
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)
import os, json
import werkzeug.security as ws  # for password hashing

app = Flask(__name__)
app.secret_key = "replace-with-real-secret-key"

# ────────── File names ──────────
BOOKS_FILE  = "books.json"
USERS_FILE  = "users.json"

# ────────── Helpers: books ──────
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE) as f:
            return json.load(f)
    return []

def save_books(data):
    with open(BOOKS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ────────── Helpers: users ──────
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ────────── Public: Welcome ─────
@app.route("/")
def welcome():
    img_dir = os.path.join(app.static_folder, "images")
    images  = [f for f in os.listdir(img_dir)
               if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    return render_template("welcome.html", images=images)

# ────────── Auth: Sign-up ───────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        users = load_users()
        if any(u["email"] == email for u in users):
            flash("User already exists. Please log in.", "error")
            return redirect(url_for("login"))

        hash_pw = ws.generate_password_hash(password)
        users.append({"email": email, "password": hash_pw})
        save_users(users)

        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# ────────── Auth: Login ─────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("login"))

        users = load_users()
        user  = next((u for u in users if u["email"] == email), None)

        if user and ws.check_password_hash(user["password"], password):
            session["user"] = user["email"]
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# ────────── Auth: Logout ────────
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("welcome"))

# ────────── Protected: Home ─────
# ────────── Protected: Home ──────────
@app.route("/home")
def home():
    """
    Title search   : ?q=<keyword>      (case-insensitive)
    Category filter: ?category=<value> (friendly or exact JSON name)
    Combined search: both filters applied (AND)

    • When a category is selected we always return *up to the
      first three* books in that category (≥0 and ≤3).
    """
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    # what came from the query-string
    raw_q        = request.args.get("q",        "").strip()
    raw_category = request.args.get("category", "").strip()

    # ------------------------------------------------------------------ #
    # 1) normalise the requested category so it matches JSON categories  #
    # ------------------------------------------------------------------ #
    alias_map = {
        "self-help"     : "Self-Help Book",
        "self help"     : "Self-Help Book",
        "biography"     : "Autobiography",
        "bio"           : "Autobiography",
        "nonfiction"    : "Non-fiction",
        "personalfinance": "Personal Finance",
        "fiction"       : "Fiction / Inspirational / Philosophical",
        "action"        : "Action-book",
        "value"         : "value investing-educational",
        "sci-fi"        : "Sci-Fi",                      # if you ever add such books
        "adventure"     : "Adventure"                    # idem
    }

    canonical_category = alias_map.get(raw_category.lower(), raw_category)

    # ------------------------------------------------------------------ #
    # 2) pull the books and apply filters                                #
    # ------------------------------------------------------------------ #
    books = load_books()

    # filter by (canonical) category first
    if canonical_category:
        books = [
            b for b in books
            if b["category"].lower() == canonical_category.lower()
        ]
        # keep *max* first three
        books = books[:3]

    # filter by keyword afterwards (AND logic)
    if raw_q:
        keyword = raw_q.lower()
        books = [b for b in books if keyword in b["title"].lower()]

    # ------------------------------------------------------------------ #
    # 3) render the template                                             #
    # ------------------------------------------------------------------ #
    return render_template(
        "home.html",
        books              = books,
        search_term        = raw_q,
        selected_category  = raw_category
    )
    # pass the filters back to the template so
    # the <input> and <select> keep their values
    return render_template(
        "home.html",
        books            = books,
        search_term      = keyword,
        selected_category= category.lower() or "all"
    )
    
@app.route('/home')
def home():
    session.pop('show_feedback_popup', None)
    return render_template("home.html")

from datetime import datetime

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if "user" not in session:
        flash("Please log in to submit feedback.", "warning")
        return redirect(url_for("login"))

    feedback_text = request.form.get("feedback", "").strip()
    if not feedback_text:
        flash("Feedback cannot be empty.", "error")
        return redirect(url_for("home"))

    feedback_entry = {
        "username": session["user"],
        "feedback": feedback_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    if os.path.exists("feedback.json"):
        with open("feedback.json") as f:
            feedback_list = json.load(f)
    else:
        feedback_list = []

    feedback_list.append(feedback_entry)
    with open("feedback.json", "w") as f:
        json.dump(feedback_list, f, indent=2)

    flash("Thanks for your feedback!", "success")
    return redirect(url_for("home"))



# ────────── Protected: Book pages
@app.route("/book/<int:id>")
def book_page(id):
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    book = next((b for b in load_books() if b["id"] == id), None)
    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("home"))
    return render_template("book_page.html", book=book)

@app.route("/book/pdf/<int:id>")
def book_pdf(id):
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    book = next((b for b in load_books() if b["id"] == id), None)
    if not book:
        flash("PDF not found.", "danger")
        return redirect(url_for("home"))
    return redirect(url_for("static", filename=book["pdf_file"]))

@app.route("/read/<int:id>")
def read_book(id):
    return redirect(url_for("book_pdf", id=id))

# ────────── Seed sample data ────
@app.before_first_request
def seed_books():
    if load_books():
        return
    sample = [
        {
            "id": 1,
            "title": "Deep Work",
            "author": "Cal Newport",
            "category": "Self-Help",
            "description": "Rules for focused success in a distracted world.",
            "pdf_file": "pdf/Deep-Work.pdf",
            "image_url": "images/deepwork.jpg"
        },
        {
            "id": 2,
            "title": "Rich Dad Poor Dad",
            "author": "Robert Kiyosaki",
            "category": "Finance",
            "description": "What the rich teach their kids about money.",
            "pdf_file": "pdf/Rich Dad Poor Dad.pdf",
            "image_url": "images/richdad.jpg"
        },
        {
            "id": 3,
            "title": "The Alchemist",
            "author": "Paulo Coelho",
            "category": "Fiction",
            "description": "A journey of self-discovery.",
            "pdf_file": "pdf/The_Alchemist.pdf",
            "image_url": "images/alchemist.jpg"
        }
    ]
    save_books(sample)
    print("📚  sample books added → books.json")

# ────────── Run ────────────────
if __name__ == "__main__":
    app.run(debug=True)
