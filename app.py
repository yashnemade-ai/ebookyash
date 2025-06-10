from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'

BOOKS_FILE = 'books.json'

def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_books(books):
    with open(BOOKS_FILE, 'w') as f:
        json.dump(books, f, indent=4)

@app.route("/")
def welcome():
    image_folder = os.path.join(app.static_folder, 'images')
    images = [img for img in os.listdir(image_folder) if img.endswith(('.jpg', '.png', '.jpeg'))]
    return render_template("welcome.html", images=images)

@app.route("/home")
def home():
    books = load_books()
    return render_template("home.html", books=books)

@app.route("/read/<int:book_id>")
def read_book(book_id):
    books = load_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if book:
        return redirect(url_for('static', filename=book["pdf_file"]))
    else:
        flash("Book not found.")
        return redirect(url_for("home"))

@app.before_first_request
def populate_books_if_empty():
    books = load_books()
    if not books:
        sample_books = [
            {
                "id": 1,
                "title": "Deep Work",
                "author": "Cal Newport",
                "description": "Rules for focused success in a distracted world.",
                "pdf_file": "pdf/Deep-Work.pdf",
                "image_url": "images/deepwork.jpg"
            },
            {
                "id": 2,
                "title": "Rich Dad Poor Dad",
                "author": "Robert Kiyosaki",
                "description": "What the rich teach their kids about money.",
                "pdf_file": "pdf/Rich Dad Poor Dad.pdf",
                "image_url": "images/richdad.jpg"
            },
            {
                "id": 3,
                "title": "The Alchemist",
                "author": "Paulo Coelho",
                "description": "A journey of self-discovery.",
                "pdf_file": "pdf/The_Alchemist.pdf",
                "image_url": "images/alchemist.jpg"
            }
        ]
        save_books(sample_books)
        print("📚 Sample books added to books.json")

if __name__ == "__main__":
    app.run(debug=True)
