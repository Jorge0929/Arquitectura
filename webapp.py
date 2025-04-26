from flask import Flask, render_template_string, request, redirect, session
import mysql.connector
import psycopg2

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configuraciones de bases de datos
MYSQL_CONFIG = {
    'host': '10.138.2.4',
    'user': 'admin31',
    'password': 'Josue-030619',
    'database': 'your_mysql_db'
}

POSTGRES_CONFIG = {
    'host': '10.138.0.4',
    'user': 'admin31',
    'password': 'Josue-030619',
    'dbname': 'your_pg_db'
}

# Plantillas simples
home_html = """
<h1>Bienvenido a la App</h1>
<a href="/login">Login</a> | <a href="/register">Registro</a>
"""

login_html = """
<h2>Login</h2>
<form method="post">
    Usuario: <input name="username"><br>
    Contraseña: <input type="password" name="password"><br>
    <input type="submit" value="Ingresar">
</form>
"""

register_html = """
<h2>Registro</h2>
<form method="post">
    Nombre: <input name="nombre"><br>
    Apellido: <input name="apellido"><br>
    Usuario: <input name="username"><br>
    Correo: <input name="correo"><br>
    Contraseña: <input type="password" name="password"><br>
    <input type="submit" value="Registrar">
</form>
"""

user_html = """
<h2>Hola {{ username }}</h2>
<a href="/logout">Cerrar sesión</a>
"""

def save_user_mysql(data):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (nombre, apellido, username, correo, password) VALUES (%s, %s, %s, %s, %s)", data)
    conn.commit()
    cursor.close()
    conn.close()

def save_user_postgres(data):
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (nombre, apellido, username, correo, password) VALUES (%s, %s, %s, %s, %s)", data)
    conn.commit()
    cursor.close()
    conn.close()

def validate_user(username, password):
    # Intenta en MySQL primero
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return True

    # Intenta en PostgreSQL si no está en MySQL
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return bool(result)

@app.route('/')
def home():
    return render_template_string(home_html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_user(username, password):
            session['username'] = username
            return redirect('/user')
        else:
            return 'Credenciales inválidas'
    return render_template_string(login_html)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = (
            request.form['nombre'],
            request.form['apellido'],
            request.form['username'],
            request.form['correo'],
            request.form['password']
        )
        save_user_mysql(data)
        save_user_postgres(data)
        return redirect('/login')
    return render_template_string(register_html)

@app.route('/user')
def user():
    if 'username' in session:
        return render_template_string(user_html, username=session['username'])
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='10.138.33.4', port=80)
