from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import json
import os
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Paths
UPLOAD_FOLDER = 'static/uploads/'
DATA_FOLDER = 'data'
BOOKS_FILE = os.path.join(DATA_FOLDER, 'books.json')
USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
FEEDBACK_FILE = os.path.join(DATA_FOLDER, 'feedback.json')

# Ensure necessary folders and files exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

for filepath, default_content in [
    (USERS_FILE, []),
    (BOOKS_FILE, []),
    (FEEDBACK_FILE, [])
]:
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_content, f, indent=4)

# ------------------ Helper Functions ------------------

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        print("✅ Users saved:", users)
    except Exception as e:
        print("❌ Error saving users:", e)

def load_books():
    with open(BOOKS_FILE, 'r') as f:
        return json.load(f)

def save_books(books):
    with open(BOOKS_FILE, 'w') as f:
        json.dump(books, f, indent=4)

def load_feedback():
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    return []

def save_feedback(feedback_list):
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_list, f, indent=4)

# ------------------ Routes ------------------

@app.route('/')
def welcome():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('welcome.html')

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please log in to access the books.', 'warning')
        return redirect(url_for('login'))
    books = load_books()
    return render_template('home.html', books=books)

@app.route('/search')
def search_books():
    query = request.args.get('query', '').lower()
    books = load_books()
    filtered_books = [book for book in books if query in book['title'].lower() or query in book['author'].lower()]
    return render_template('home.html', books=filtered_books)

@app.route('/book/<int:id>')
def book_page(id):
    if 'username' not in session:
        flash('Please log in to view the book details.', 'warning')
        return redirect(url_for('login'))
    book = next((b for b in load_books() if b['id'] == id), None)
    if not book:
        return "Book not found!", 404
    return render_template('book_page.html', book=book)

@app.route('/book/<int:id>/pdf')
def book_pdf(id):
    if 'username' not in session:
        flash('Please log in to access the PDF.', 'warning')
        return redirect(url_for('login'))
    book = next((b for b in load_books() if b['id'] == id), None)
    if not book:
        return "Book not found!", 404
    filename = os.path.basename(book['pdf_file'])
    return send_from_directory(os.path.dirname(book['pdf_file']), filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    users_db = load_users()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = next((u for u in users_db if u['email'] == email and u['password'] == password), None)
        if user:
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('auth.html', action='login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    users_db = load_users()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if any(u['username'] == username for u in users_db):
            flash('Username already exists.', 'danger')
        elif any(u['email'] == email for u in users_db):
            flash('Email already exists.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            new_user = {'username': username, 'email': email, 'password': password}
            users_db.append(new_user)
            print("📝 Adding user:", new_user)  # Debug print
            save_users(users_db)
            flash('Account created successfully! You can log in now.', 'success')
            return redirect(url_for('login'))
    return render_template('auth.html', action='signup')

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session:
        flash('Please log in to access the admin dashboard.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    users_db = load_users()
    user = next((u for u in users_db if u['username'] == username), None)

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('welcome'))

    is_admin = (users_db.index(user) == 0)

    if not is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        description = request.form['description']
        pdf_file = request.files['pdf_file']
        image_file = request.files['image_file']

        if pdf_file and image_file:
            pdf_filename = secure_filename(pdf_file.filename)
            image_filename = secure_filename(image_file.filename)
            pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)

            pdf_file.save(pdf_path)
            image_file.save(image_path)

            books = load_books()
            new_book = {
                'id': len(books) + 1,
                'title': title,
                'author': author,
                'description': description,
                'pdf_file': pdf_path,
                'image_url': image_path
            }
            books.append(new_book)
            save_books(books)
            flash('Book uploaded successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('admin_dashboard.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'username' not in session:
        flash('You must be logged in to submit feedback.', 'warning')
        return redirect(url_for('login'))

    feedback_list = load_feedback()
    feedback = {
        'username': session['username'],
        'feedback': request.form['feedback'],
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    feedback_list.append(feedback)
    save_feedback(feedback_list)
    flash('Feedback submitted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/admin/feedback')
def admin_feedback():
    if 'username' not in session:
        flash('You must be logged in to access the feedback.', 'warning')
        return redirect(url_for('login'))

    users_db = load_users()
    user = next((u for u in users_db if u['username'] == session['username']), None)

    if not user or users_db.index(user) != 0:
        flash('You do not have permission to view feedback.', 'danger')
        return redirect(url_for('home'))

    feedback_list = load_feedback()
    return render_template('admin_feedback.html', feedback_list=feedback_list)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('welcome'))

# ------------------ Run Server ------------------

if __name__ == "__main__":
    app.run(debug=True)
