from flask import Flask, render_template, redirect, url_for, flash
import os, json

app = Flask(__name__)
app.secret_key = "your-secret-key"

BOOKS_FILE = "books.json"

# ────────── Helpers ──────────
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_books(data):
    with open(BOOKS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ────────── Routes ──────────
@app.route("/")
def welcome():
    # Optional welcome page showing all book covers
    img_dir = os.path.join(app.static_folder, "images")
    images = [f for f in os.listdir(img_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    return render_template("welcome.html", images=images)

@app.route("/home")
def home():
    if "user" not in session:
        flash("You must log in first.")
        return redirect(url_for("login"))
    return render_template("home.html", books=load_books())

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.")
    return redirect(url_for("welcome"))

@app.route("/book/<int:id>")
def book_page(id):
    book = next((b for b in load_books() if b["id"] == id), None)
    if not book:
        flash("Book not found.")
        return redirect(url_for("home"))
    return render_template("book_page.html", book=book)

@app.route("/book/pdf/<int:id>")
def book_pdf(id):
    book = next((b for b in load_books() if b["id"] == id), None)
    if not book:
        flash("PDF not found.")
        return redirect(url_for("home"))
    return redirect(url_for("static", filename=book["pdf_file"]))

@app.route("/read/<int:id>")
def read_book(id):
    # Legacy route redirecting to new PDF reader
    return redirect(url_for("book_pdf", id=id))

# ────────── Bootstrap Sample Data ──────────
@app.before_first_request
def populate_if_empty():
    if load_books():
        return

    sample_books = [
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

    save_books(sample_books)
    print("📚 Sample books added to books.json")

# ────────── Run the app ──────────
if __name__ == "__main__":
    app.run(debug=True)
