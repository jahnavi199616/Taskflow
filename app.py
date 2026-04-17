from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE'] = os.path.join(app.instance_path, 'taskflow.sqlite')
os.makedirs(app.instance_path, exist_ok=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped

@app.cli.command('init-db')
def init_db_command():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        db.commit()
        print('Initialized the database.')

@app.route('/')
def index():
    if not session.get('user_id'):
        return render_template('index.html', todos=[])
    db = get_db()
    todos = db.execute('SELECT id, title, done FROM todos WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    return render_template('index.html', todos=todos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
            flash('Username already exists')
            return redirect(url_for('register'))
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, generate_password_hash(password)))
        db.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('auth.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('auth.html', title='Login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
@login_required
def add_todo():
    title = request.form['title'].strip()
    if title:
        db = get_db()
        db.execute('INSERT INTO todos (user_id, title, done) VALUES (?, ?, 0)', (session['user_id'], title))
        db.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:todo_id>')
@login_required
def complete_todo(todo_id):
    db = get_db()
    db.execute('UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?', (todo_id, session['user_id']))
    db.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    db = get_db()
    db.execute('DELETE FROM todos WHERE id = ? AND user_id = ?', (todo_id, session['user_id']))
    db.commit()
    return redirect(url_for('index'))
