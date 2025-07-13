# # app.py
# from flask import Flask, request, jsonify, render_template, redirect, url_for, session
# from flask_cors import CORS
# import pymysql.cursors
# from werkzeug.security import check_password_hash
# from datetime import date 
# import os

# # INIZIALIZZAZIONE CORRETTA
# app = Flask(__name__, template_folder='templates', static_folder='static')
# CORS(app)

# # --- NUOVA CONFIGURAZIONE CHIAVE SEGRETA PER LE SESSIONI ---
# # FONDAMENTALE: La secret key è necessaria per firmare crittograficamente i dati
# # della sessione (il cookie). In produzione, usa una stringa complessa e casuale
# # e caricala da una variabile d'ambiente per sicurezza.
# app.secret_key = os.urandom(24) # Genera una chiave sicura ad ogni avvio

# # --- CONFIGURAZIONE DATABASE MYSQL (invariata) ---
# DB_CONFIG = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': '23042005', # Ricorda di usare variabili d'ambiente per le credenziali
#     'db': 'registro_accademico',
#     'charset': 'utf8mb4',
#     'cursorclass': pymysql.cursors.DictCursor
# }

# def get_db_connection():
#     try:
#         connection = pymysql.connect(**DB_CONFIG)
#         return connection
#     except pymysql.Error as e:
#         print(f"Errore di connessione al database: {e}")
#         return None

# # --- ROTTE PER SERVIRE LE PAGINE HTML ---

# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/dashboard')
# def serve_dashboard_page():
#     # --- MODIFICA: Protezione della rotta ---
#     # Se l'ID del docente non è in sessione, significa che non ha fatto il login.
#     # Reindirizzalo alla pagina di login.
#     if 'teacher_id' not in session:
#         return redirect(url_for('login'))
    
#     # Passiamo il nome del docente al template per un saluto personalizzato
#     teacher_name = session.get('teacher_name', 'Docente')
#     return render_template('teacher/teacher_home.html', teacher_name=teacher_name)

# # --- NUOVA ROTTA PER IL LOGOUT ---
# @app.route('/logout')
# def logout():
#     """
#     Rimuove i dati del docente dalla sessione e reindirizza alla pagina di login.
#     """
#     session.pop('teacher_id', None)
#     session.pop('teacher_name', None)
#     return redirect(url_for('login'))


# # --- ROTTA API PER IL LOGIN (AGGIORNATA PER USARE LE SESSIONI) ---
# @app.route('/api/login', methods=['POST'])
# def handle_login_api():
#     data = request.get_json()
#     if not data or 'email' not in data or 'password' not in data:
#         return jsonify({'error': 'Email e password sono obbligatorie'}), 400

#     email = data['email']
#     password_candidate = data['password']

#     connection = get_db_connection()
#     if connection is None:
#         return jsonify({'error': 'Errore di connessione al database'}), 500
    
#     try:
#         with connection.cursor() as cursor:
#             sql = "SELECT idDocente, Nome, Cognome, Email, Password FROM registro_accademico.Docente WHERE Email = %s"
#             cursor.execute(sql, (email,))
#             teacher = cursor.fetchone()

#             if teacher and check_password_hash(teacher['Password'], password_candidate):
#                 # --- MODIFICA: Salvataggio dati in sessione ---
#                 # Se le credenziali sono corrette, salviamo l'ID e il nome del docente
#                 # nella sessione. Flask gestirà il cookie per noi.
#                 session['teacher_id'] = teacher['idDocente']
#                 session['teacher_name'] = teacher['Nome']
                
#                 return jsonify({
#                     'message': 'Login effettuato con successo!',
#                     'teacher': {
#                         'id': teacher['idDocente'],
#                         'name': teacher['Nome'],
#                         'surname': teacher['Cognome'],
#                         'email': teacher['Email']
#                     }
#                 })
#             else:
#                 return jsonify({'error': 'Credenziali non valide'}), 401

#     except pymysql.Error as e:
#         print(f"Errore durante il login: {e}")
#         return jsonify({'error': 'Errore del server durante il login'}), 500
#     finally:
#         if connection:
#             connection.close()


# # --- ROTTA PER LA PAGINA DEL MENU (AGGIORNATA E PROTETTA) ---
# @app.route('/seleziona_lezione')
# def serve_appello_page():
#     """
#     Serve la pagina per la selezione della lezione, mostrando SOLO le lezioni
#     del docente loggato.
#     """
#     # --- MODIFICA: Protezione e recupero ID docente ---
#     if 'teacher_id' not in session:
#         return redirect(url_for('login'))
#     id_docente_loggato = session['teacher_id']

#     lezioni = []
#     oggi = date.today()
#     connection = get_db_connection()

#     if connection is None:
#         return "Errore: Impossibile connettersi al database.", 500

#     try:
#         with connection.cursor() as cursor:
#             # --- MODIFICA: Query aggiornata per filtrare per docente ---
#             # La query ora unisce la tabella Cattedra per trovare le lezioni
#             # associate all'ID del docente recuperato dalla sessione.
#             sql = """
#                 SELECT
#                     L.idLezione,
#                     I.Nome,
#                     TIME(L.ora_inizio) AS OraInizio
#                 FROM Lezione AS L
#                 JOIN Insegnamento AS I ON L.insegnamento = I.idInsegnamento
#                 JOIN Cattedra AS C ON I.idInsegnamento = C.insegnamento
#                 WHERE DATE(L.ora_inizio) = %s AND C.docente = %s
#                 ORDER BY OraInizio
#             """
#             cursor.execute(sql, (oggi, id_docente_loggato))
#             lezioni = cursor.fetchall()

#             for lezione in lezioni:
#                 if 'OraInizio' in lezione and lezione['OraInizio']:
#                     total_seconds = int(lezione['OraInizio'].total_seconds())
#                     hours = total_seconds // 3600
#                     minutes = (total_seconds % 3600) // 60
#                     lezione['OraInizio_formatted'] = f"{hours:02d}:{minutes:02d}"

#     except pymysql.Error as e:
#         print(f"Errore durante il recupero delle lezioni: {e}")
#         lezioni = []
#     finally:
#         if connection:
#             connection.close()

#     return render_template('teacher/lessons_menu.html', lezioni=lezioni)
# # -------------------------------------------------------------


# # --- ROTTA PER LA PAGINA DI REGISTRAZIONE PRESENZE (PROTETTA) ---
# @app.route('/registra-presenze')
# def serve_registra_presenze_page():
#     """
#     Mostra la griglia degli studenti. Aggiungiamo un controllo per assicurare
#     che il docente loggato sia autorizzato a vedere questa lezione.
#     """
#     # --- MODIFICA: Protezione rotta ---
#     if 'teacher_id' not in session:
#         return redirect(url_for('login'))
#     id_docente_loggato = session['teacher_id']

#     id_lezione = request.args.get('lezione', type=int)
#     if not id_lezione:
#         return "Errore: ID della lezione non specificato.", 400

#     connection = get_db_connection()
#     if connection is None:
#         return "Errore: Impossibile connettersi al database.", 500

#     lezione_info = None
#     studenti = []

#     try:
#         with connection.cursor() as cursor:
#             # --- MODIFICA: Controllo di autorizzazione ---
#             # Verifichiamo che la lezione richiesta appartenga effettivamente
#             # al docente che ha fatto il login.
#             sql_auth_check = """
#                 SELECT L.idLezione FROM Lezione L
#                 JOIN Cattedra C ON L.insegnamento = C.insegnamento
#                 WHERE L.idLezione = %s AND C.docente = %s
#             """
#             cursor.execute(sql_auth_check, (id_lezione, id_docente_loggato))
#             if cursor.fetchone() is None:
#                 # Se la query non restituisce risultati, il docente non è autorizzato.
#                 return "Accesso non autorizzato a questa lezione.", 403

#             # Se l'autorizzazione è ok, procedi a recuperare i dati
#             sql_lezione = """
#                 SELECT I.Nome, L.ora_inizio
#                 FROM Lezione L
#                 JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
#                 WHERE L.idLezione = %s
#             """
#             cursor.execute(sql_lezione, (id_lezione,))
#             lezione_raw = cursor.fetchone()

#             if lezione_raw:
#                 lezione_info = {
#                     'idLezione': id_lezione,
#                     'nomeMateria': lezione_raw['Nome'],
#                     'data': lezione_raw['ora_inizio'].strftime('%d/%m/%Y'),
#                     'ora': lezione_raw['ora_inizio'].strftime('%H:%M')
#                 }

#             sql_studenti = """
#                 SELECT S.matricola, S.Nome, S.Cognome
#                 FROM Studente S
#                 JOIN Iscrizione I ON S.matricola = I.studente
#                 JOIN Lezione L ON I.insegnamento = L.insegnamento
#                 WHERE L.idLezione = %s
#                 ORDER BY S.Cognome, S.Nome
#             """
#             cursor.execute(sql_studenti, (id_lezione,))
#             studenti = cursor.fetchall()

#     except pymysql.Error as e:
#         print(f"Errore durante il recupero dei dati per l'appello: {e}")
#     finally:
#         if connection:
#             connection.close()
    
#     if not lezione_info:
#         return "Errore: Lezione non trovata.", 404

#     return render_template('teacher/appello.html', lezione=lezione_info, studenti=studenti)
# # -------------------------------------------------------------


# # --- ROTTA PER SALVARE LE PRESENZE (invariata, la logica è già sicura) ---
# @app.route('/salva-presenze', methods=['POST'])
# def salva_presenze():
#     id_lezione = request.form.get('idLezione')
#     if not id_lezione:
#         return "Errore: ID Lezione mancante nel form.", 400

#     studenti_da_salvare_ids = []
#     for key, value in request.form.items():
#         if key.startswith('studente_') and value == 'presente':
#             id_studente = key.split('_')[1]
#             studenti_da_salvare_ids.append(id_studente)

#     if not studenti_da_salvare_ids:
#         print(f"Nessuno studente segnato come presente per la lezione ID {id_lezione}. Nessun dato salvato.")
#         return redirect(url_for('serve_dashboard_page'))

#     connection = get_db_connection()
#     if connection is None:
#         return "Errore di connessione al database", 500

#     try:
#         with connection.cursor() as cursor:
#             sql_gia_presenti = "SELECT studente FROM Presenza WHERE lezione = %s"
#             cursor.execute(sql_gia_presenti, (id_lezione,))
#             risultato_gia_presenti = cursor.fetchall()
#             studenti_gia_presenti_ids = {str(item['studente']) for item in risultato_gia_presenti}

#             studenti_nuovi_presenti_ids = [
#                 id_studente for id_studente in studenti_da_salvare_ids
#                 if id_studente not in studenti_gia_presenti_ids
#             ]

#             if not studenti_nuovi_presenti_ids:
#                 print(f"Nessuna nuova presenza da registrare per la lezione ID {id_lezione}.")
#                 return redirect(url_for('serve_dashboard_page'))

#             sql_insert = "INSERT INTO Presenza (studente, lezione) VALUES (%s, %s)"
#             dati_da_inserire = [(id_studente, id_lezione) for id_studente in studenti_nuovi_presenti_ids]
            
#             cursor.executemany(sql_insert, dati_da_inserire)
        
#         connection.commit()
#         print(f"Salvate con successo {cursor.rowcount} NUOVE presenze per la lezione ID {id_lezione}.")

#     except pymysql.Error as e:
#         print(f"ERRORE durante il salvataggio delle presenze: {e}")
#         connection.rollback()
#         return "Si è verificato un errore durante il salvataggio. Riprova.", 500
#     finally:
#         if connection:
#             connection.close()

#     return redirect(url_for('serve_dashboard_page'))
# # ---------------------------------------------------



# # --- ROTTA PER FIRMA PRESENZA DOCENTE (AGGIORNATA E PROTETTA) ---
# @app.route('/firma-presenza')
# def serve_firma_presenza_page():
#     # --- MODIFICA: Protezione e recupero ID docente ---
#     if 'teacher_id' not in session:
#         return redirect(url_for('login'))
#     id_docente_loggato = session['teacher_id']

#     lezioni = []
#     oggi = date.today()
#     connection = get_db_connection()
#     if connection is None: return "Errore di connessione al database", 500
#     try:
#         with connection.cursor() as cursor:
#             # --- MODIFICA: Query aggiornata per usare l'ID del docente loggato ---
#             # Non usiamo più un ID di esempio, ma quello reale dalla sessione.
#             sql = """
#                 SELECT L.idLezione, I.Nome, TIME(L.ora_inizio) AS OraInizio
#                 FROM Lezione L
#                 JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
#                 JOIN Cattedra C ON I.idInsegnamento = C.insegnamento
#                 WHERE DATE(L.ora_inizio) = %s
#                   AND C.docente = %s
#                 ORDER BY OraInizio
#             """
#             cursor.execute(sql, (oggi, id_docente_loggato))
#             lezioni = cursor.fetchall()
            
#             for lezione in lezioni:
#                 if 'OraInizio' in lezione and lezione['OraInizio']:
#                     total_seconds = int(lezione['OraInizio'].total_seconds())
#                     hours = total_seconds // 3600
#                     minutes = (total_seconds % 3600) // 60
#                     lezione['OraInizio_formatted'] = f"{hours:02d}:{minutes:02d}"

#     except pymysql.Error as e:
#         print(f"Errore durante il recupero delle lezioni per la firma: {e}")
#         lezioni = []
#     finally:
#         if connection: connection.close()
#     return render_template('teacher/firma_presenza.html', lezioni=lezioni)



# # --- ROTTA SALVA FIRMA (AGGIORNATA E PROTETTA) ---
# @app.route('/salva-firma-docente', methods=['POST'])
# def salva_firma_docente():
#     # --- MODIFICA: Protezione e recupero ID docente ---
#     if 'teacher_id' not in session:
#         return redirect(url_for('login'))
#     id_docente_loggato = session['teacher_id']

#     id_lezione = request.form.get('lezione')
#     note = request.form.get('note', '')
#     presenza_valore = True if request.form.get('conferma_presenza') == 'on' else False

#     if not id_lezione: return "Errore: Selezionare una lezione.", 400
    
#     connection = get_db_connection()
#     if connection is None: return "Errore di connessione al database", 500
#     try:
#         with connection.cursor() as cursor:
#             # --- MODIFICA: Inserimento firma con l'ID del docente loggato ---
#             # Non usiamo più un ID di esempio.
#             sql = """
#                 INSERT INTO Docenza (docente, lezione, presenza, note)
#                 VALUES (%s, %s, %s, %s)
#             """
#             cursor.execute(sql, (id_docente_loggato, id_lezione, presenza_valore, note))
#         connection.commit()
#         print(f"Firma registrata con successo per la lezione ID {id_lezione} dal docente ID {id_docente_loggato} con stato presenza: {presenza_valore}.")
#     except pymysql.Error as e:
#         print(f"ERRORE durante la registrazione della firma: {e}")
#         connection.rollback()
#         return "Si è verificato un errore durante la firma. Riprova.", 500
#     finally:
#         if connection: connection.close()
#     return redirect(url_for('serve_dashboard_page'))


# if __name__ == '__main__':
#     app.run(debug=True, port=5000)









from flask import Flask, render_template
from flask_cors import CORS
import os

# Importa i Blueprints dai tuoi nuovi file
from auth_routes import auth_bp
from teacher_routes import teacher_bp
from manager_routes import manager_bp

def create_app():
    """
    Crea e configura un'istanza dell'applicazione Flask.
    Questa è una "Application Factory".
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Configurazione
    CORS(app)
    # La secret key è fondamentale per le sessioni
    app.config['SECRET_KEY'] = os.urandom(24)

    # Registra i Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(manager_bp) # Quando lo creerai

    # Aggiungi una rotta di base
    @app.route('/')
    def home():
        return render_template('home.html')

    return app

# Questo blocco viene eseguito solo quando avvii lo script direttamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
