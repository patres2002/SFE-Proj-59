from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

app.secret_key = 'group59'

# Connect to the database
conn = sqlite3.connect('system.db')
c = conn.cursor()

# Create the users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (username text, password text)''')


# Check if the table is empty
c.execute("SELECT COUNT(*) FROM users")
row_count = c.fetchone()[0]

# Insert example data only if the table is empty
if row_count == 0:
    c.execute("INSERT INTO users VALUES ('admin', 'admin')")
    c.execute("INSERT INTO users VALUES ('student', 'student')")
    conn.commit()

# Create the tickets table for issues
c.execute('''CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

# Save the changes and close the database
conn.commit()
conn.close()

# Login page, or home page if logged in
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        # print("about to post")
        # Connect to the database
        conn = sqlite3.connect('system.db')
        # print("connected")
        c = conn.cursor()

        # Get the details from the form
        # print("getting the details")
        username = request.form['username']
        password = request.form['password']
        # print(username, password)
        # Check if the details are correct
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        data = c.fetchone()

        # If the details are correct, log the user in
        if data is not None:
            session['username'] = request.form['username']
            # print("here")
            return redirect(url_for('home'))

        # Close the database
        conn.close()

    # If the details are incorrect, show the login page
    return render_template('login.html')

# Home page
@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username = session['username'])
    return redirect(url_for('login'))

# EC page
@app.route('/ec')
def ec():
    if 'username' in session:
        return render_template('ec.html', username = session['username'])
    return redirect(url_for('login'))

# Issues page
@app.route('/issues')
def issues():
    if 'username' in session:
        return render_template('issues.html', username = session['username'])
    return redirect(url_for('login'))

# Logout page
@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()