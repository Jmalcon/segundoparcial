from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura

# Función para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar la base de datos
def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()

# Inicializar la base de datos al iniciar la aplicación
init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                        (username, password))
            conn.commit()
            flash('Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Nombre de usuario ya existe')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, title, content, created_at) VALUES (?, ?, ?, ?)',
                    (session['user_id'], title, content, now))
        conn.commit()
        conn.close()
        
        flash('Publicación creada exitosamente')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC',
                        (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', username=session['username'], posts=posts)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ? AND user_id = ?', 
                       (post_id, session['user_id'])).fetchone()
    
    if post is None:
        conn.close()
        flash('Post no encontrado o no tienes permiso para editarlo')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ? AND user_id = ?',
                    (title, content, post_id, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Post actualizado exitosamente')
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ? AND user_id = ?', 
                       (post_id, session['user_id'])).fetchone()
    
    if post is None:
        conn.close()
        flash('Post no encontrado o no tienes permiso para eliminarlo')
        return redirect(url_for('dashboard'))
    
    conn.execute('DELETE FROM posts WHERE id = ? AND user_id = ?', (post_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Post eliminado exitosamente')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
