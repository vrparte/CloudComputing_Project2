from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'CHANGE_ME_TO_SOMETHING_RANDOM'  # for sessions

DATABASE = '/var/www/html/flaskapp/users.db'
UPLOAD_FOLDER = '/var/www/html/flaskapp/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------------------------------------------------------
# Helper function to initialize the DB and create table if necessary
# -------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  password TEXT NOT NULL,
                  firstname TEXT,
                  lastname TEXT,
                  email TEXT,
                  address TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

# --------------------------------------------------------
# Registration Page: username + password (store in DB)
# --------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Insert into DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  (username, password))
        user_id = c.lastrowid
        conn.commit()
        conn.close()

        # Store user_id in session
        session['user_id'] = user_id

        # Redirect to details page
        return redirect(url_for('details'))
    else:
        return render_template('register.html')

# --------------------------------------------------------
# Details Page: first name, last name, email, address
# --------------------------------------------------------
@app.route('/details', methods=['GET', 'POST'])
def details():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        address = request.form.get('address')

        user_id = session.get('user_id')
        if user_id is None:
            return redirect(url_for('register'))

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("""UPDATE users
                     SET firstname=?, lastname=?, email=?, address=?
                     WHERE id=?""",
                  (firstname, lastname, email, address, user_id))
        conn.commit()
        conn.close()

        # Extra Credit: file upload (Limerick-1-1.txt)
        uploaded_file = request.files.get('limerick')
        if uploaded_file:
            filename = "limerick_uploaded.txt"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)

            # count words
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                word_count = len(text.split())
            session['word_count'] = word_count
            session['filename'] = filename

        return redirect(url_for('display'))
    else:
        return render_template('details.html')

# --------------------------------------------------------
# Display Page: shows user data & optional word count
# --------------------------------------------------------
@app.route('/display')
def display():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Ensures column access by name
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user is None:
        return "Error: User not found", 404

    word_count = session.get('word_count', None)
    return render_template('display.html', user=user, word_count=word_count)


# --------------------------------------------------------
# Re-login Page: retrieve user info
# --------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect(url_for('display'))
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>."
    else:
        return render_template('login.html')

# --------------------------------------------------------
# Extra: Download route if you want to retrieve uploaded file
# --------------------------------------------------------
from flask import send_file

@app.route('/download')
def download():
    filename = session.get('filename', None)
    if filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
    return "No file available for download", 404


# -----------------------------------------------------------------
# Run the Flask app (only if debugging directly, not via mod_wsgi)
# -----------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
