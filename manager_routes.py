from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

# --- CREAZIONE DEL BLUEPRINT PER IL MANAGER ---
manager_bp = Blueprint('manager_bp', __name__,
                       url_prefix='/manager',  # Aggiunge '/manager' prima di tutte le rotte
                       template_folder='templates',
                       static_folder='static')

# --- DECORATOR PER LA PROTEZIONE DELLE ROTTE DEL MANAGER ---
# Questo decorator ora controlla che l'utente in sessione abbia il ruolo 'manager'.
# NOTA: Affinché funzioni, la rotta di login deve salvare 'user_role' nella sessione.
def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Controlla se il ruolo è presente in sessione e se è 'manager'
        if session.get('user_role') != 'manager':
            # Se non è un manager, reindirizza al login.
            # In futuro, potresti reindirizzare a una pagina "Accesso Negato".
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


# --- ROTTA PRINCIPALE PER LA DASHBOARD DEL MANAGER ---
# Applichiamo il decorator a tutte le rotte del manager per proteggerle.
@manager_bp.route('/dashboard')
@manager_required
def dashboard():
    """
    Mostra la dashboard principale del manager con le 4 opzioni.
    """
    return render_template('manager/manager_home.html')


# --- ROTTE SEGNAPOSTO PER LE FUNZIONALITÀ DI GESTIONE ---

@manager_bp.route('/insegnamenti')
@manager_required
def gestione_insegnamenti():
    """
    Pagina per la gestione degli insegnamenti (corsi/materie).
    Qui andrà la logica per visualizzare, creare, modificare ed eliminare insegnamenti.
    """
    return "<h1>Pagina Gestione Insegnamenti</h1><p>Work in progress...</p>"


@manager_bp.route('/studenti')
@manager_required
def gestione_studenti():
    """
    Pagina per la gestione delle anagrafiche degli studenti.
    Qui andrà la logica per visualizzare, aggiungere e gestire gli studenti.
    """
    return "<h1>Pagina Gestione Studenti</h1><p>Work in progress...</p>"


@manager_bp.route('/docenti')
@manager_required
def gestione_docenti():
    """
    Pagina per la gestione dei docenti e delle loro cattedre.
    """
    return "<h1>Pagina Gestione Docenti</h1><p>Work in progress...</p>"


@manager_bp.route('/lezioni')
@manager_required
def gestione_lezioni():
    """
    Pagina per la pianificazione del calendario delle lezioni.
    """
    return "<h1>Pagina Gestione Lezioni</h1><p>Work in progress...</p>"
