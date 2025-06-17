from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Load books from JSON
def load_books():
    with open('books.json', 'r') as f:
        return json.load(f)

# Load users from JSON
def load_users():
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as f:
            json.dump({}, f)
    with open('users.json', 'r') as f:
        return json.load(f)

# Save users to JSON
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if email in users:
            flash('Email already exists. Please login.', 'error')
            return redirect(url_for('signup'))
        users[email] = {'password': password}
        save_users(users)
        flash('Signup successful. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if email in users and users[email]['password'] == password:
            session['user'] = email
            flash('Login successful.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    books = load_books()
    category = request.args.get('category', '')
    search = request.args.get('search', '').lower()
    
    filtered_books = books
    
    if category:
        filtered_books = [book for book in filtered_books if book['category'].lower() == category.lower()]
        filtered_books = filtered_books[:3]
    
    if search:
        filtered_books = [book for book in filtered_books if search in book['title'].lower()]
    
    return render_template('home.html', books=filtered_books, user=session['user'])

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.form.get('feedback')
    print("Feedback received:", data)  # You can log this or save it
    flash("Thanks for your feedback!", "success")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
