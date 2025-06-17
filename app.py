from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)
from flask_dance.contrib.google import make_google_blueprint, google
import os, json
import werkzeug.security as ws
from datetime import datetime

app = Flask(__name__)
app.secret_key = "replace-with-real-secret-key"

# ────── Google OAuth ──────
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
google_bp = make_google_blueprint(
    client_id="133669733575-lhah8j60ep069r2pmjifj14kcb5776ev.apps.googleusercontent.com",
    client_secret="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",
    redirect_to="google_login"
)
app.register_blueprint(google_bp, url_prefix="/login")

BOOKS_FILE = "books.json"
USERS_FILE = "users.json"
FEEDBACK_FILE = "feedback.json"

# ────── Load & Save Helpers ──────
def load_json(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ────── Public: Welcome ──────
@app.route("/")
def welcome():
    img_dir = os.path.join(app.static_folder, "images")
    images = [f for f in os.listdir(img_dir)
              if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    return render_template("welcome.html", images=images)

# ────── Signup ──────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        users = load_json(USERS_FILE)
        if any(u["email"] == email for u in users):
            flash("User already exists. Please log in.", "error")
            return redirect(url_for("login"))

        users.append({"email": email, "password": ws.generate_password_hash(password)})
        save_json(USERS_FILE, users)

        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

# ────── Login ──────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("login"))

        users = load_json(USERS_FILE)
        user = next((u for u in users if u["email"] == email), None)

        if user and ws.check_password_hash(user["password"], password):
            session["user"] = user["email"]
            session["show_feedback_popup"] = True
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# ────── Google OAuth Login ──────
@app.route("/google-login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        session["user"] = resp.json()["email"]
        flash("Logged in with Google!", "success")
        return redirect(url_for("home"))
    else:
        flash("Google login failed.", "error")
        return redirect(url_for("login"))

# ────── Logout ──────
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("welcome"))

# ────── Home ──────
@app.route("/home")
def home():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    raw_q = request.args.get("q", "").strip()
    raw_category = request.args.get("category", "").strip()

    alias_map = {
        "self-help": "Self-Help",
        "self help": "Self-Help",
        "biography": "Autobiography",
        "bio": "Autobiography",
        "nonfiction": "Non-fiction",
        "personalfinance": "Personal Finance",
        "fiction": "Fiction",
        "action": "Action",
        "value": "Value Investing",
        "sci-fi": "Sci-Fi",
        "adventure": "Adventure"
    }
    canonical_category = alias_map.get(raw_category.lower(), raw_category)
    books = load_json(BOOKS_FILE)

    if canonical_category:
        books = [b for b in books if b["category"].lower() == canonical_category.lower()][:3]
    if raw_q:
        keyword = raw_q.lower()
        books = [b for b in books if keyword in b["title"].lower()]

    return render_template(
        "home.html",
        books=books,
        search_term=raw_q,
        selected_category=raw_category,
        show_feedback_popup=session.pop("show_feedback_popup", False)
    )

# ────── Feedback ──────
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if "user" not in session:
        flash("Please log in to submit feedback.", "warning")
        return redirect(url_for("login"))

    feedback = request.form.get("feedback", "").strip()
    if not feedback:
        flash("Feedback cannot be empty.", "error")
        return redirect(url_for("home"))

    feedback_entry = {
        "username": session["user"],
        "feedback": feedback,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    feedback_list = load_json(FEEDBACK_FILE)
    feedback_list.append(feedback_entry)
    save_json(FEEDBACK_FILE, feedback_list)

    session["show_feedback_popup"] = True
    flash("Thanks for your feedback!", "success")
    return redirect(url_for("home"))

# ────── Book Pages ──────
@app.route("/book/<int:id>")
def book_page(id):
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    book = next((b for b in load_json(BOOKS_FILE) if b["id"] == id), None)
    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("home"))
    return render_template("book_page.html", book=book)

@app.route("/book/pdf/<int:id>")
def book_pdf(id):
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    book = next((b for b in load_json(BOOKS_FILE) if b["id"] == id), None)
    if not book:
        flash("PDF not found.", "danger")
        return redirect(url_for("home"))
    return redirect(url_for("static", filename=book["pdf_file"]))

@app.route("/read/<int:id>")
def read_book(id):
    return redirect(url_for("book_pdf", id=id))

# ────── Seed sample data (Flask 2/3 safe) ──────
@app.before_first_request
def seed_books():
    if load_json(BOOKS_FILE):
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
    save_json(BOOKS_FILE, sample)
    print("\U0001F4DA Sample books seeded → books.json")

# ────── Run app locally ──────
if __name__ == "__main__":
    app.run(debug=True)
