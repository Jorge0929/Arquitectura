# webapp.py
import os
import mysql.connector
import psycopg2
from flask import Flask, render_template_string, request, redirect, session
import logging

# Configura logging básico para ver en Azure App Service Log Stream
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
# Es buena práctica leer también el secret_key de una variable de entorno
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey_fallback')

# --- Nombres de Variables de Entorno Esperadas ---
# Deberás configurar estas variables en Azure App Service -> Configuración -> Configuración de la aplicación
# MYSQL
MYSQL_ENV_HOST = 'DB_HOST_MYSQL'
MYSQL_ENV_USER = 'DB_USER_MYSQL'
MYSQL_ENV_PASS = 'DB_PASS_MYSQL'
MYSQL_ENV_DB = 'DB_NAME_MYSQL' # Nombre de tu base de datos MySQL (ej: 'mydatabase')

# POSTGRESQL
PGSQL_ENV_HOST = 'DB_HOST_PGSQL'
PGSQL_ENV_USER = 'DB_USER_PGSQL'
PGSQL_ENV_PASS = 'DB_PASS_PGSQL'
PGSQL_ENV_DB = 'DB_NAME_PGSQL' # Nombre de tu base de datos PostgreSQL (ej: 'mydatabase' o 'postgres')
# --------------------------------------------------

# Plantillas simples (sin cambios)
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

# --- Funciones de Base de Datos (Modificadas) ---

def get_mysql_connection():
    """Obtiene una conexión MySQL usando variables de entorno."""
    host = os.environ.get(MYSQL_ENV_HOST)
    user = os.environ.get(MYSQL_ENV_USER)
    password = os.environ.get(MYSQL_ENV_PASS)
    database = os.environ.get(MYSQL_ENV_DB)
    if not all([host, user, password, database]):
        logging.error("Faltan variables de entorno para MySQL.")
        raise ValueError("Configuración de MySQL incompleta en variables de entorno.")
    try:
        conn = mysql.connector.connect(
            host=host,          # Usa el FQDN desde la variable de entorno
            user=user,
            password=password,
            database=database,  # Usa el nombre de BD desde la variable de entorno
            connection_timeout=10
        )
        logging.info("Conexión MySQL establecida.")
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Error al conectar a MySQL: {err}")
        raise

def get_postgres_connection():
    """Obtiene una conexión PostgreSQL usando variables de entorno."""
    host = os.environ.get(PGSQL_ENV_HOST)
    user = os.environ.get(PGSQL_ENV_USER)
    password = os.environ.get(PGSQL_ENV_PASS)
    dbname = os.environ.get(PGSQL_ENV_DB)
    if not all([host, user, password, dbname]):
        logging.error("Faltan variables de entorno para PostgreSQL.")
        raise ValueError("Configuración de PostgreSQL incompleta en variables de entorno.")
    try:
        conn_string = f"host='{host}' port=5432 dbname='{dbname}' user='{user}' password='{password}' connect_timeout=10"
        conn = psycopg2.connect(conn_string)
        logging.info("Conexión PostgreSQL establecida.")
        return conn
    except psycopg2.Error as err:
        logging.error(f"Error al conectar a PostgreSQL: {err}")
        raise

def save_user_mysql(data):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        # Asegúrate que tu tabla 'users' exista en MySQL con estas columnas
        cursor.execute("INSERT INTO users (nombre, apellido, username, correo, password) VALUES (%s, %s, %s, %s, %s)", data)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Usuario {data[2]} guardado en MySQL.")
    except Exception as e:
        logging.error(f"Error guardando usuario en MySQL: {e}")
        # Considera cómo manejar el error (ej. reintentar, logear, notificar)

def save_user_postgres(data):
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
         # Asegúrate que tu tabla 'users' exista en PostgreSQL con estas columnas
        cursor.execute("INSERT INTO users (nombre, apellido, username, correo, password) VALUES (%s, %s, %s, %s, %s)", data)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Usuario {data[2]} guardado en PostgreSQL.")
    except Exception as e:
        logging.error(f"Error guardando usuario en PostgreSQL: {e}")
         # Considera cómo manejar el error

def validate_user(username, password):
    # Intenta en MySQL primero
    try:
        conn_mysql = get_mysql_connection()
        cursor = conn_mysql.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        result_mysql = cursor.fetchone()
        cursor.close()
        conn_mysql.close()
        if result_mysql:
            logging.info(f"Usuario {username} validado en MySQL.")
            return True
    except Exception as e:
        logging.error(f"Error validando usuario en MySQL: {e}")

    # Intenta en PostgreSQL si no está en MySQL
    try:
        conn_pg = get_postgres_connection()
        cursor = conn_pg.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        result_pg = cursor.fetchone()
        cursor.close()
        conn_pg.close()
        if result_pg:
            logging.info(f"Usuario {username} validado en PostgreSQL.")
            return True
    except Exception as e:
        logging.error(f"Error validando usuario en PostgreSQL: {e}")

    logging.warning(f"Validación fallida para usuario {username}.")
    return False

# --- Rutas Flask (sin cambios en la lógica principal) ---

@app.route('/')
def home():
    return render_template_string(home_html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            if validate_user(username, password):
                session['username'] = username
                return redirect('/user')
            else:
                return 'Credenciales inválidas'
        except Exception as e:
            # Si falla la conexión a BD durante validación
            return f"Error de base de datos durante el login: {e}"
    return render_template_string(login_html)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = (
            request.form.get('nombre'),
            request.form.get('apellido'),
            request.form.get('username'),
            request.form.get('correo'),
            request.form.get('password') # Considera hashear la contraseña en una app real
        )
        # Verifica que todos los datos necesarios están presentes
        if not all(data):
             return "Error: Faltan datos en el formulario de registro."
        try:
            # Intenta guardar en ambas bases de datos
            save_user_mysql(data)
            # Podrías decidir guardar solo en una o tener lógica más compleja
            # save_user_postgres(data) # Descomenta si quieres guardar en ambas
            return redirect('/login')
        except Exception as e:
             return f"Error de base de datos durante el registro: {e}"
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

# --- Bloque app.run() ELIMINADO ---
# No incluir 'if __name__ == "__main__": app.run(...)'
# Gunicorn se encargará de iniciar la app usando el Comando de Inicio
