from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from werkzeug.security import check_password_hash
import pymysql
import re

from extensions import limiter
from database import get_db_connection

auth_bp = Blueprint('auth_bp', __name__,
                    template_folder='templates',
                    static_folder='static')

# --- DEFINIZIONE DEL FORM (MODIFICATO) ---
# Ora definiamo i campi che ci aspettiamo dal form.
# Flask-WTF li userà per la validazione automatica, incluso il CSRF.
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired("L'email è obbligatoria."), Email("Formato email non valido.")])
    password = PasswordField('Password', validators=[DataRequired("La password è obbligatoria.")])

@auth_bp.route('/login')
def login():
    form = LoginForm()
    # Questa rotta ora passa un form completo al template, 
    # che dovrà renderizzare form.hidden_tag() per includere il token CSRF.
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))


# --- ROTTA API DI LOGIN (MODIFICATA SIGNIFICATIVAMENTE) ---
@auth_bp.route('/api/login', methods=['POST'])
@limiter.limit("10 per hour; 5 per minute")
def handle_login_api():
    """Gestisce la richiesta di login validando il form, inclusa la protezione CSRF."""
    form = LoginForm()

    # 'validate_on_submit()' controlla automaticamente:
    # 1. Che sia una richiesta POST.
    # 2. Che il token CSRF sia valido.
    # 3. Che i campi (email, password) rispettino i validatori definiti sopra.
    if form.validate_on_submit():
        email = form.email.data
        password_candidate = form.password.data

        try:
            connection = get_db_connection()
        except ConnectionError as e:
            print(e)
            return jsonify({'error': 'Errore di connessione al database'}), 503

        try:
            with connection.cursor() as cursor:
                sql = "SELECT idDocente, Nome, Cognome, Email, Password, Ruolo FROM Docente WHERE Email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()

                if user and check_password_hash(user['Password'], password_candidate):
                    session.clear()
                    session['user_id'] = user['idDocente']
                    session['user_name'] = user['Nome']
                    session['user_role'] = user['Ruolo']
                    session.permanent = True

                    redirect_url = ''
                    if user['Ruolo'] == 'manager':
                        redirect_url = url_for('manager_bp.dashboard')
                    elif user['Ruolo'] == 'docente':
                        redirect_url = url_for('teacher_bp.serve_dashboard_page')
                    else:
                        session.clear()
                        return jsonify({'error': 'Ruolo utente non valido o non autorizzato.'}), 403

                    return jsonify({
                        'message': 'Login effettuato con successo!',
                        'redirect_url': redirect_url
                    })
                else:
                    return jsonify({'error': 'Credenziali non valide'}), 401

        except pymysql.Error as e:
            print(f"Errore del database durante il login: {e}")
            return jsonify({'error': 'Errore interno del server.'}), 500
        finally:
            if connection:
                connection.close()
    else:
        # Se la validazione fallisce, 'form.errors' conterrà la ragione esatta.
        # Questo risolve l'errore 400 e ti dice esattamente perché.
        print("Errore di validazione del form:", form.errors)
        return jsonify({'error': 'Dati del form non validi.', 'details': form.errors}), 400