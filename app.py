from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'group59'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/<string:page_name>')
def render_static(page_name):
    return render_template('%s.html' % page_name)


if __name__ == "__main__":
    app.run(debug=True)