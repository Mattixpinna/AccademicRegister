from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from werkzeug.security import check_password_hash
import pymysql
import re

from extensions import limiter
from database import get_db_connection

# Configurare il Blueprint per le rotte di autenticazione, specificando le cartelle per template e file statici
auth_bp = Blueprint('auth_bp', __name__,
                    template_folder='templates',
                    static_folder='static')

# Definire i campi attesi dal form. Flask-WTF li userà per la validazione automatica, incluso il CSRF.
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired("L'email è obbligatoria."), Email("Formato email non valido.")])
    password = PasswordField('Password', validators=[DataRequired("La password è obbligatoria.")])

@auth_bp.route('/login')
def login():
    # Inizializzare il form vuoto per passarlo al template HTML
    form = LoginForm()
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    # Rimuovere tutti i dati dalla sessione per disconnettere l'utente e reindirizzare al login
    session.clear()
    return redirect(url_for('auth_bp.login'))


# Definire la rotta per gestire il login API con limitazione della velocità
@auth_bp.route('/api/login', methods=['POST'])
@limiter.limit("10 per hour; 5 per minute")
def handle_login_api():
    """Gestisce la richiesta di login validando il form, inclusa la protezione CSRF."""
    form = LoginForm()

    # Verificare se la richiesta è POST e validare i dati del form tramite 'validate_on_submit()', incluso il token CSRF.
    if form.validate_on_submit():
        # Estrarre i dati puliti dal form dopo la validazione
        email = form.email.data
        password_candidate = form.password.data

        try:
            # Tentare di stabilire una connessione al database
            connection = get_db_connection()
        except ConnectionError as e:
            print(e)
            return jsonify({'error': 'Errore di connessione al database'}), 503

        try:
            with connection.cursor() as cursor:
                # Eseguire una query parametrizzata per cercare l'utente tramite email, evitando SQL injection
                sql = "SELECT idDocente, Nome, Cognome, Email, Password, Ruolo FROM Docente WHERE Email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

                # Verificare se l'utente esiste e se l'hash della password nel DB corrisponde a quella fornita
                if user and check_password_hash(user['Password'], password_candidate):
                    # Login riuscito: pulire la vecchia sessione e salvare i nuovi dati identificativi
                    session.clear()
                    session['user_id'] = user['idDocente']
                    session['user_name'] = user['Nome']
                    session['user_role'] = user['Ruolo']
                    session.permanent = True # Impostare la sessione come permanente (durata default Flask: 31 giorni)

                    # Gestire la logica condizionale per reindirizzare l'utente alla dashboard corretta in base al ruolo
                    redirect_url = ''
                    if user['Ruolo'] == 'manager':
                        redirect_url = url_for('manager_bp.dashboard')
                    elif user['Ruolo'] == 'docente':
                        redirect_url = url_for('teacher_bp.serve_dashboard_page')
                    else:
                        # Se il ruolo non è riconosciuto, invalidare la sessione immediatamente
                        session.clear()
                        return jsonify({'error': 'Ruolo utente non valido o non autorizzato.'}), 403

                    return jsonify({
                        'message': 'Login effettuato con successo!',
                        'redirect_url': redirect_url
                    })
                else:
                    # Restituire un errore generico per credenziali errate
                    return jsonify({'error': 'Credenziali non valide'}), 401

        except pymysql.Error as e:
            print(f"Errore del database durante il login: {e}")
            return jsonify({'error': 'Errore interno del server.'}), 500
        finally:
            # Assicurare la chiusura della connessione al database per liberare le risorse
            if connection:
                connection.close()
    else:
        print("Errore di validazione del form:", form.errors)
        return jsonify({'error': 'Dati del form non validi.', 'details': form.errors}), 400