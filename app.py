import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = 'group59'

# Connect to the database
conn = sqlite3.connect('system.db')
c = conn.cursor()

# Create the users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')

# Check if the table is empty
c.execute("SELECT COUNT(*) FROM users")
row_count = c.fetchone()[0]

# Insert example data only if the table is empty
if row_count == 0:
    c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('student', 'student', 'student')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('itladmin', 'itl', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('eeadmin', 'ee', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('ecadmin', 'ec', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('itsadmin', 'itsadmin', 'admin')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('moduleorganiser', 'module', 'module_organiser')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('moduleorganiser2', 'module', 'module_organiser')")
    c.execute("INSERT INTO users (username, password, role) VALUES ('student2', 'student', 'student')")
    conn.commit()

# Create the tickets table for issues
c.execute('''CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id))''')

# Create the ecs table for ECs
c.execute('''CREATE TABLE IF NOT EXISTS ecs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    course_name TEXT NOT NULL,
    instructor TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evidence TEXT,
    claim_type TEXT NOT NULL,
    delegated_to INTEGER)''')

# Save the changes and close the database
conn.commit()
conn.close()

# Login page, or home page if logged in
@app.route('/', methods=['GET', 'POST'])
def login() -> str:
    form_submitted = False  # A flag to check if the form has been submitted

    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            # Set the flag to True when form is submitted
            form_submitted = True

            # Connect to the database
            conn = sqlite3.connect('system.db')
            c = conn.cursor()

            # Get the details from the form
            username = request.form['username']
            password = request.form['password']

            # Check if the details are correct
            c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            data = c.fetchone()

            # If the details are correct, log the user in
            if data is not None:
                session['username'] = request.form['username']
                # Store the user ID in the session
                session['user_id'] = data[0]
                session['role'] = data[3]
                return redirect(url_for('home'))

            # Close the database
            conn.close()
        except Exception as e:
            # Handle errors
            return render_template('error.html', message=e)

    # If the details are incorrect and the form has been submitted, show the error message
    error = "Incorrect username or password" if form_submitted else None
    return render_template('login.html', error=error)

# Home page
@app.route('/home')
def home() -> str:
    if 'username' in session:
        role = session['role']
        if role == 'admin':
            return render_template('admin.html', username=session['username'])
        elif role == 'module_organiser':
            return render_template('moduleo.html', username=session['username'])
        elif role == 'student':
            return render_template('home.html', username=session['username'])
        else:
            return render_template('error.html', message='Invalid role')
    return redirect(url_for('login'))

# Issues page
@app.route('/issues', methods=['GET', 'POST'])
def issues():
    if 'username' in session:
        role = session['role']

        # Connect to the database
        conn = sqlite3.connect('system.db')
        c = conn.cursor()

        if request.method == 'POST':
            # Get the form data
            title = request.form['title']
            type = request.form['type']
            description = request.form['description']
            user_id = session['user_id']
            status = 'pending'

            try:
                # Send the data to the database
                c.execute("INSERT INTO tickets (user_id, title, type, description, status) VALUES (?, ?, ?, ?, ?)",(user_id, title, type, description, status))
                conn.commit()
                message = "Your issue has been submitted."
                return render_template('message.html', message=message)
            except Exception as e:
                conn.rollback()
                return render_template('error.html', message=e)
        # if admin or module organizer, return all the tickets in the database
        elif role == 'admin':
            try:
                c.execute("SELECT users.username, tickets.type, tickets.title, tickets.description, tickets.status, tickets.created_at FROM tickets INNER JOIN users ON users.id = user_id")
                # this should be different for each admin
                issues = c.fetchall()
                conn.close()
                return render_template('issues.html', username=session['username'], issues=issues)
            except Exception as e:
                # Handle errors
                conn.rollback()
                return render_template('error.html', message=e)
        # Else if student then just return the page as normal
        else:
            types = [
                {'value': 'eelab', 'label': 'EE Lab'},
                {'value': 'itl', 'label': 'ITL'},
                {'value': 'its', 'label': 'ITS'}
            ]
            return render_template('issues.html', username=session['username'], types=types)
    return redirect(url_for('login'))

# EC Page
@app.route('/ecs', methods=['GET', 'POST'])
def ec():
    if 'username' in session:
        role = session['role']

        # Connect to the database
        conn = sqlite3.connect('system.db')
        c = conn.cursor()

        if request.method == 'POST':
            # Get the form data
            description = request.form['description']
            course_name = request.form['course_name']
            instructor = request.form['instructor']
            user_id = session['user_id']
            status = 'pending'
            filename = None
            claim_type = request.form['claim_type']

            # Check if the user has reached the limit for self-certified claims
            if request.form['claim_type'] == 'option-2':
                current_year = datetime.datetime.now().year
                c.execute("SELECT COUNT(*) FROM ecs WHERE user_id = ? AND strftime('%Y', created_at) = ? AND claim_type = 'self_certified'", (user_id, current_year))
                count = c.fetchone()[0]
                if count >= 3:
                    message = "You have reached the limit of 3 self-certified ECs per year."
                    return render_template('message.html', message=message)

            # Save the uploaded file
            uploaded_file = request.files.get('evidence')
            if uploaded_file:
                print('uploading')
                filename = f"{user_id}_{uploaded_file.filename}"
                file_path = os.path.join('static', 'uploads', filename)
                uploaded_file.save(file_path)

            try:
                # Send the data to the database
                print("about to insert")
                conn = sqlite3.connect('system.db')
                c = conn.cursor()
                c.execute("INSERT INTO ecs (user_id, course_name, instructor, description, status, evidence, claim_type) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, course_name, instructor, description, status, filename, claim_type))
                print("inserting data")
                conn.commit()
                message = "Your EC has been submitted."
                return render_template('message.html', message=message)
            except Exception as e:
                conn.rollback()
                return render_template('error.html', message=e)

        # Fetch submitted ECs for students
        if session['role'] == 'student':
            try:
                user_id = session['user_id']
                c.execute("SELECT * FROM ecs WHERE user_id = ?", (user_id,))
                submitted_ecs = c.fetchall()
                conn.close()
                return render_template('ec.html', username=session['username'], submitted_ecs=submitted_ecs)
            except Exception as e:
                # Handle errors
                conn.rollback()
                return render_template('error.html', message=e)

        # if ecadmin return all the ec in the database
        elif session['username'] == 'ecadmin':
            try:
                c.execute("SELECT ecs.id, users.username, ecs.course_name, ecs.instructor, ecs.description, ecs.status, ecs.created_at, ecs.evidence, ecs.claim_type, ecs.delegated_to FROM ecs INNER JOIN users ON users.id = user_id")
                ecs = c.fetchall()

                # Get the list of module organizers
                # print("About to get module organisers")
                c.execute("SELECT id, username FROM users WHERE role = 'module_organiser'")
                # print("here")
                module_organisers = c.fetchall()
                # print(module_organisers)

                conn.close()
                # print("closed connection")
                # print(ecs)
                return render_template('ec.html', username=session['username'], ecs=ecs, module_organisers=module_organisers)
            except Exception as e:
                # Handle errors
                conn.rollback()
                return render_template('error.html', message=e)
        elif session['role'] == 'module_organiser':
            try:
                # print("here")
                module_organiser_id = session['user_id']
                c.execute("SELECT ecs.id, users.username, ecs.course_name, ecs.instructor, ecs.description, ecs.status, ecs.created_at, ecs.evidence, ecs.claim_type FROM ecs INNER JOIN users ON users.id = user_id WHERE ecs.delegated_to = ? AND ecs.status == 'pending'", (module_organiser_id,))
                ecs = c.fetchall()
                # print(session['user_id'])
                # print(ecs)
                conn.close()
                return render_template('ec.html', username=session['username'], ecs=ecs)
            except Exception as e:
                # Handle errors
                conn.rollback()
                return render_template('error.html', message=e)
        else:
            return render_template('ec.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/delegate_claim', methods=['POST'])
def delegate_claim():
    if 'username' in session and session['role'] == 'admin':
        # Parse the request data
        data = request.get_json()
        claim_id = data['claim_id']
        delegated_to = data['delegated_to']

        print(f"Updating claim_id: {claim_id} with delegated_to: {delegated_to}")

        # Update the delegated_to field in the database
        conn = sqlite3.connect('system.db')
        c = conn.cursor()

        try:
            c.execute("UPDATE ecs SET delegated_to = ? WHERE id = ?", (delegated_to, claim_id))
            conn.commit()
            print("Delegation updated successfully in the database")
            conn.close()
            return jsonify(success=True)
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error during updating delegation: {str(e)}")
            return jsonify(success=False, error=str(e))
    else:
        return jsonify(success=False, error="Unauthorized")

# Logout page
@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/update_claim_status', methods=['POST'])
def update_claim_status():
    if 'username' in session and session['role'] == 'module_organiser':
        # Parse the request data
        data = request.get_json()
        print("Received data:", data)  # Add a print statement here
        claim_id = data['claim_id']
        status = data['status']

        # Update the status field in the database
        conn = sqlite3.connect('system.db')
        c = conn.cursor()

        try:
            c.execute("UPDATE ecs SET status = ? WHERE id = ?", (status, claim_id))
            conn.commit()
            conn.close()
            return jsonify(success=True)
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify(success=False, error=str(e))
    else:
        return jsonify(success=False, error="Unauthorized")

if __name__ == '__main__':
    app.debug = True
    app.run()