# app.py  ──────────────────────────────────────────────
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)
import os, json
import werkzeug.security as ws      # for password hashing

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
        with open(USERS_FILE) as f:
            return json.load(f)
    return []

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ────────── Public: Welcome ─────
@app.route("/")
def welcome():
    # show a scrolling wall of covers on the landing page
    img_dir = os.path.join(app.static_folder, "images")
    images  = [f for f in os.listdir(img_dir)
               if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    return render_template("welcome.html", images=images)

# ────────── Auth: Sign-up ───────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        # Store users in a simple file or dict (in production use DB)
        user_data = {"email": email, "password": password}
        with open("users.json", "a") as f:
            f.write(json.dumps(user_data) + "\n")

        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# ────────── Auth: Login ─────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"].lower().strip()
        password = request.form["password"]

        user = next((u for u in load_users()
                     if u["email"] == email), None)

        if user and ws.check_password_hash(user["password"], password):
            session["user"] = email
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

# ────────── Auth: Logout ────────
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("welcome"))

# ────────── Protected: Home ─────
@app.route("/home")
def home():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    return render_template("home.html", books=load_books())

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
    # Serve the file inside /static/…
    return redirect(url_for("static", filename=book["pdf_file"]))

# legacy link
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
