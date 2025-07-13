from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import check_password_hash
import pymysql.cursors

# Funzione per ottenere la connessione al DB
def get_db_connection():
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '23042005',
        'db': 'registro_accademico',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Errore di connessione al database: {e}")
        return None

# Creazione del Blueprint
auth_bp = Blueprint('auth_bp', __name__,
                    template_folder='templates',
                    static_folder='static')

@auth_bp.route('/login')
def login():
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    # Pulisce tutte le chiavi della sessione
    session.clear()
    return redirect(url_for('auth_bp.login'))

@auth_bp.route('/api/login', methods=['POST'])
def handle_login_api():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email e password sono obbligatorie'}), 400

    email = data['email']
    password_candidate = data['password']

    connection = get_db_connection()
    if connection is None:
        return jsonify({'error': 'Errore di connessione al database'}), 500
    
    try:
        with connection.cursor() as cursor:
            # --- MODIFICA: Selezioniamo anche il campo 'ruolo' ---
            sql = "SELECT idDocente, Nome, Cognome, Email, Password, Ruolo FROM registro_accademico.Docente WHERE Email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['Password'], password_candidate):
                # --- MODIFICA: Salviamo ID, nome e RUOLO nella sessione ---
                session['user_id'] = user['idDocente']
                session['user_name'] = user['Nome']
                session['user_role'] = user['Ruolo']
                
                # --- MODIFICA: Decidiamo dove reindirizzare in base al ruolo ---
                redirect_url = ''
                if user['Ruolo'] == 'manager':
                    redirect_url = url_for('manager_bp.dashboard')
                elif user['Ruolo'] == 'docente':
                    redirect_url = url_for('teacher_bp.serve_dashboard_page')
                else:
                    # Se il ruolo non è riconosciuto, impedisci il login
                    session.clear()
                    return jsonify({'error': 'Ruolo utente non valido o non autorizzato.'}), 403

                return jsonify({
                    'message': 'Login effettuato con successo!',
                    'redirect_url': redirect_url
                })
            else:
                return jsonify({'error': 'Credenziali non valide'}), 401

    except pymysql.Error as e:
        print(f"Errore durante il login: {e}")
        return jsonify({'error': 'Errore del server durante il login'}), 500
    finally:
        if connection:
            connection.close()
