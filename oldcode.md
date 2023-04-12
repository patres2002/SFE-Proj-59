# EC page

@app.route('/ec', methods=['GET', 'POST'])
def ec() -> str:
if request.method == 'POST':
try: # Connect to the database
conn = sqlite3.connect('system.db')
c = conn.cursor()

            # Get the details from the form and insert into the database
            title = request.form['title']
            description = request.form['description']
            status = 'pending'
            user_id = session['user_id']
            c.execute("INSERT INTO ecs (user_id, title, description, status) VALUES (?, ?, ?, ?)",
                      (user_id, title, description, status))
            conn.commit()

            # Close the database
            conn.close()
        except Exception as e:
            # Handle errors
            return render_template('error.html', message="An error occurred while accessing the database.")

    if 'username' in session:
        return render_template('ec.html', username = session['username'])
    return redirect(url_for('login'))

# homepage base

<title>Home - StuCare</title>
<link
  rel="stylesheet"
  href="{{ url_for('static', filename='css/home.css') }}"
/>
{% endblock %} {% block body %}
<h1>This is home</h1>
<p>You are logged in as {{ username }}</p>
{% endblock %}
