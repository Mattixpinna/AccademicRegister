# from flask import Blueprint, request, render_template, redirect, url_for, session
# from datetime import date, datetime
# import pymysql.cursors
# from functools import wraps

# # Funzione per ottenere la connessione al DB
# def get_db_connection():
#     DB_CONFIG = {
#         'host': 'localhost',
#         'user': 'root',
#         'password': '23042005',
#         'db': 'registro_accademico',
#         'charset': 'utf8mb4',
#         'cursorclass': pymysql.cursors.DictCursor
#     }
#     try:
#         connection = pymysql.connect(**DB_CONFIG)
#         return connection
#     except pymysql.Error as e:
#         print(f"Errore di connessione al database: {e}")
#         return None

# # --- Decorator per i docenti ---
# def teacher_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if str(session.get('user_role')).lower() != 'docente':
#             return redirect(url_for('auth_bp.login'))
#         return f(*args, **kwargs)
#     return decorated_function

# # Creazione del Blueprint
# teacher_bp = Blueprint('teacher_bp', __name__,
#                        template_folder='templates',
#                        static_folder='static')


# @teacher_bp.route('/dashboard')
# @teacher_required
# def serve_dashboard_page():
#     teacher_name = session.get('user_name', 'Docente')
#     return render_template('teacher/teacher_home.html', teacher_name=teacher_name)


# @teacher_bp.route('/seleziona_lezione')
# @teacher_required
# def serve_appello_page():
#     id_docente_loggato = session['user_id']
#     lezioni = []
#     oggi = date.today()
#     connection = get_db_connection()

#     if connection is None:
#         return "Errore: Impossibile connettersi al database.", 500

#     try:
#         with connection.cursor() as cursor:
#             sql = """
#                 SELECT L.idLezione, I.Nome, TIME(L.ora_inizio) AS OraInizio
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

# @teacher_bp.route('/registra-presenze')
# @teacher_required
# def serve_registra_presenze_page():
#     id_docente_loggato = session['user_id']
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
#             # Controlla che il docente sia autorizzato per questa lezione
#             sql_auth_check = """
#                 SELECT L.idLezione FROM Lezione L
#                 JOIN Cattedra C ON L.insegnamento = C.insegnamento
#                 WHERE L.idLezione = %s AND C.docente = %s
#             """
#             cursor.execute(sql_auth_check, (id_lezione, id_docente_loggato))
#             if cursor.fetchone() is None:
#                 return "Accesso non autorizzato a questa lezione.", 403

#             # Recupera i dettagli della lezione
#             sql_lezione = """
#                 SELECT I.Nome, L.ora_inizio FROM Lezione L
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

#                 # ### INIZIO MODIFICA ###
#                 # 1. Calcola l'anno accademico basandosi sulla data della lezione
#                 data_lezione = lezione_raw['ora_inizio']
#                 anno_lezione = data_lezione.year
#                 mese_lezione = data_lezione.month
                
#                 if mese_lezione >= 9:
#                     anno_accademico_lezione = f"{anno_lezione}/{anno_lezione + 1}"
#                 else:
#                     anno_accademico_lezione = f"{anno_lezione - 1}/{anno_lezione}"

#                 # 2. Modifica la query per filtrare gli studenti per l'anno accademico corretto
#                 sql_studenti = """
#                     SELECT S.matricola, S.Nome, S.Cognome 
#                     FROM Studente S
#                     JOIN Iscrizione I ON S.matricola = I.studente
#                     JOIN Lezione L ON I.insegnamento = L.insegnamento
#                     WHERE L.idLezione = %s AND I.anno_accademico = %s
#                     AND L.anno_di_corso = I.anno_di_corso
#                     ORDER BY S.Cognome, S.Nome
#                 """
#                 cursor.execute(sql_studenti, (id_lezione, anno_accademico_lezione))
#                 studenti = cursor.fetchall()
#                 # ### FINE MODIFICA ###
                
#     except pymysql.Error as e:
#         print(f"Errore durante il recupero dei dati per l'appello: {e}")
#     finally:
#         if connection:
#             connection.close()
    
#     if not lezione_info:
#         return "Errore: Lezione non trovata.", 404

#     return render_template('teacher/appello.html', lezione=lezione_info, studenti=studenti)


# @teacher_bp.route('/salva-presenze', methods=['POST'])
# @teacher_required
# def salva_presenze():
#     id_lezione = request.form.get('idLezione')
#     if not id_lezione:
#         return "Errore: ID Lezione mancante nel form.", 400

#     studenti_da_salvare_ids = [
#         key.split('_')[1] for key, value in request.form.items()
#         if key.startswith('studente_') and value == 'presente'
#     ]

#     if not studenti_da_salvare_ids:
#         return redirect(url_for('teacher_bp.serve_dashboard_page'))

#     connection = get_db_connection()
#     if connection is None: return "Errore di connessione al database", 500
#     try:
#         with connection.cursor() as cursor:
#             sql_gia_presenti = "SELECT studente FROM Presenza WHERE lezione = %s"
#             cursor.execute(sql_gia_presenti, (id_lezione,))
#             studenti_gia_presenti_ids = {str(item['studente']) for item in cursor.fetchall()}
#             studenti_nuovi_presenti_ids = [
#                 sid for sid in studenti_da_salvare_ids if sid not in studenti_gia_presenti_ids
#             ]
#             if not studenti_nuovi_presenti_ids:
#                 return redirect(url_for('teacher_bp.serve_dashboard_page'))
#             sql_insert = "INSERT INTO Presenza (studente, lezione) VALUES (%s, %s)"
#             dati_da_inserire = [(sid, id_lezione) for sid in studenti_nuovi_presenti_ids]
#             cursor.executemany(sql_insert, dati_da_inserire)
#             connection.commit()
#     except pymysql.Error as e:
#         print(f"ERRORE durante il salvataggio delle presenze: {e}")
#         connection.rollback()
#     finally:
#         if connection:
#             connection.close()
#     return redirect(url_for('teacher_bp.serve_dashboard_page'))


# @teacher_bp.route('/firma-presenza')
# @teacher_required
# def serve_firma_presenza_page():
#     id_docente_loggato = session['user_id']
#     lezioni = []
#     oggi = date.today()
#     connection = get_db_connection()
#     if connection is None: return "Errore di connessione al database", 500
#     try:
#         with connection.cursor() as cursor:
#             sql = """
#                 SELECT L.idLezione, I.Nome, TIME(L.ora_inizio) AS OraInizio, L.anno_di_corso
#                 FROM Lezione L
#                 JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
#                 JOIN Cattedra C ON I.idInsegnamento = C.insegnamento
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
#         print(f"Errore durante il recupero delle lezioni per la firma: {e}")
#         lezioni = []
#     finally:
#         if connection: connection.close()
#     return render_template('teacher/firma_presenza.html', lezioni=lezioni)


# @teacher_bp.route('/salva-firma-docente', methods=['POST'])
# @teacher_required
# def salva_firma_docente():
#     id_docente_loggato = session['user_id']
#     id_lezione = request.form.get('lezione')
#     note = request.form.get('note', '')
#     presenza_valore = 'conferma_presenza' in request.form

#     if not id_lezione: return "Errore: Selezionare una lezione.", 400
    
#     connection = get_db_connection()
#     if connection is None: return "Errore di connessione al database", 500
#     try:
#         with connection.cursor() as cursor:
#             sql = "INSERT INTO Docenza (docente, lezione, presenza, note) VALUES (%s, %s, %s, %s)"
#             cursor.execute(sql, (id_docente_loggato, id_lezione, presenza_valore, note))
#             connection.commit()
#     except pymysql.Error as e:
#         print(f"ERRORE durante la registrazione della firma: {e}")
#         connection.rollback()
#     finally:
#         if connection: connection.close()
            
#     return redirect(url_for('teacher_bp.serve_dashboard_page'))











from flask import Blueprint, request, render_template, redirect, url_for, session
from datetime import date, datetime
import pymysql.cursors
from functools import wraps

# Importa la funzione per la connessione dal modulo centralizzato
from database import get_db_connection

# --- Decorator per i docenti ---
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if str(session.get('user_role')).lower() != 'docente':
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# Creazione del Blueprint
teacher_bp = Blueprint('teacher_bp', __name__,
                       template_folder='templates',
                       static_folder='static')

@teacher_bp.route('/dashboard')
@teacher_required
def serve_dashboard_page():
    teacher_name = session.get('user_name', 'Docente')
    return render_template('teacher/teacher_home.html', teacher_name=teacher_name)

@teacher_bp.route('/seleziona_lezione')
@teacher_required
def serve_appello_page():
    id_docente_loggato = session['user_id']
    lezioni = []
    oggi = date.today()
    connection = get_db_connection()

    if connection is None:
        return "Errore: Impossibile connettersi al database.", 500

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT L.idLezione, I.Nome, TIME(L.ora_inizio) AS OraInizio
                FROM Lezione AS L
                JOIN Insegnamento AS I ON L.insegnamento = I.idInsegnamento
                JOIN Cattedra AS C ON I.idInsegnamento = C.insegnamento
                WHERE DATE(L.ora_inizio) = %s AND C.docente = %s
                ORDER BY OraInizio
            """
            cursor.execute(sql, (oggi, id_docente_loggato))
            lezioni = cursor.fetchall()

            for lezione in lezioni:
                if 'OraInizio' in lezione and lezione['OraInizio']:
                    total_seconds = int(lezione['OraInizio'].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    lezione['OraInizio_formatted'] = f"{hours:02d}:{minutes:02d}"
    except pymysql.Error as e:
        print(f"Errore durante il recupero delle lezioni: {e}")
        lezioni = []
    finally:
        if connection:
            connection.close()

    return render_template('teacher/lessons_menu.html', lezioni=lezioni)

@teacher_bp.route('/registra-presenze')
@teacher_required
def serve_registra_presenze_page():
    id_docente_loggato = session['user_id']
    id_lezione = request.args.get('lezione', type=int)
    if not id_lezione:
        return "Errore: ID della lezione non specificato.", 400

    connection = get_db_connection()
    if connection is None:
        return "Errore: Impossibile connettersi al database.", 500

    lezione_info = None
    studenti = []
    try:
        with connection.cursor() as cursor:
            # Controlla che il docente sia autorizzato per questa lezione
            sql_auth_check = """
                SELECT L.idLezione FROM Lezione L
                JOIN Cattedra C ON L.insegnamento = C.insegnamento
                WHERE L.idLezione = %s AND C.docente = %s
            """
            cursor.execute(sql_auth_check, (id_lezione, id_docente_loggato))
            if cursor.fetchone() is None:
                return "Accesso non autorizzato a questa lezione.", 403

            # Recupera i dettagli della lezione
            sql_lezione = """
                SELECT I.Nome, L.ora_inizio FROM Lezione L
                JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
                WHERE L.idLezione = %s
            """
            cursor.execute(sql_lezione, (id_lezione,))
            lezione_raw = cursor.fetchone()

            if lezione_raw:
                lezione_info = {
                    'idLezione': id_lezione,
                    'nomeMateria': lezione_raw['Nome'],
                    'data': lezione_raw['ora_inizio'].strftime('%d/%m/%Y'),
                    'ora': lezione_raw['ora_inizio'].strftime('%H:%M')
                }

                # ### INIZIO MODIFICA ###
                # 1. Calcola l'anno accademico basandosi sulla data della lezione
                data_lezione = lezione_raw['ora_inizio']
                anno_lezione = data_lezione.year
                mese_lezione = data_lezione.month
                
                if mese_lezione >= 9:
                    anno_accademico_lezione = f"{anno_lezione}/{anno_lezione + 1}"
                else:
                    anno_accademico_lezione = f"{anno_lezione - 1}/{anno_lezione}"

                # 2. Modifica la query per filtrare gli studenti per l'anno accademico corretto
                sql_studenti = """
                    SELECT S.matricola, S.Nome, S.Cognome 
                    FROM Studente S
                    JOIN Iscrizione I ON S.matricola = I.studente
                    JOIN Lezione L ON I.insegnamento = L.insegnamento
                    WHERE L.idLezione = %s AND I.anno_accademico = %s
                    AND L.anno_di_corso = I.anno_di_corso
                    ORDER BY S.Cognome, S.Nome
                """
                cursor.execute(sql_studenti, (id_lezione, anno_accademico_lezione))
                studenti = cursor.fetchall()
                # ### FINE MODIFICA ###
                
    except pymysql.Error as e:
        print(f"Errore durante il recupero dei dati per l'appello: {e}")
    finally:
        if connection:
            connection.close()
    
    if not lezione_info:
        return "Errore: Lezione non trovata.", 404

    return render_template('teacher/appello.html', lezione=lezione_info, studenti=studenti)


@teacher_bp.route('/salva-presenze', methods=['POST'])
@teacher_required
def salva_presenze():
    id_lezione = request.form.get('idLezione')
    if not id_lezione:
        return "Errore: ID Lezione mancante nel form.", 400

    studenti_da_salvare_ids = [
        key.split('_')[1] for key, value in request.form.items()
        if key.startswith('studente_') and value == 'presente'
    ]

    if not studenti_da_salvare_ids:
        return redirect(url_for('teacher_bp.serve_dashboard_page'))

    connection = get_db_connection()
    if connection is None: return "Errore di connessione al database", 500
    try:
        with connection.cursor() as cursor:
            sql_gia_presenti = "SELECT studente FROM Presenza WHERE lezione = %s"
            cursor.execute(sql_gia_presenti, (id_lezione,))
            studenti_gia_presenti_ids = {str(item['studente']) for item in cursor.fetchall()}
            studenti_nuovi_presenti_ids = [
                sid for sid in studenti_da_salvare_ids if sid not in studenti_gia_presenti_ids
            ]
            if not studenti_nuovi_presenti_ids:
                return redirect(url_for('teacher_bp.serve_dashboard_page'))
            sql_insert = "INSERT INTO Presenza (studente, lezione) VALUES (%s, %s)"
            dati_da_inserire = [(sid, id_lezione) for sid in studenti_nuovi_presenti_ids]
            cursor.executemany(sql_insert, dati_da_inserire)
            connection.commit()
    except pymysql.Error as e:
        print(f"ERRORE durante il salvataggio delle presenze: {e}")
        connection.rollback()
    finally:
        if connection:
            connection.close()
    return redirect(url_for('teacher_bp.serve_dashboard_page'))


@teacher_bp.route('/firma-presenza')
@teacher_required
def serve_firma_presenza_page():
    id_docente_loggato = session['user_id']
    lezioni = []
    oggi = date.today()
    connection = get_db_connection()
    if connection is None: return "Errore di connessione al database", 500
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT L.idLezione, I.Nome, TIME(L.ora_inizio) AS OraInizio, L.anno_di_corso
                FROM Lezione L
                JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
                JOIN Cattedra C ON I.idInsegnamento = C.insegnamento
                WHERE DATE(L.ora_inizio) = %s AND C.docente = %s
                ORDER BY OraInizio
            """
            cursor.execute(sql, (oggi, id_docente_loggato))
            lezioni = cursor.fetchall()
            for lezione in lezioni:
                if 'OraInizio' in lezione and lezione['OraInizio']:
                    total_seconds = int(lezione['OraInizio'].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    lezione['OraInizio_formatted'] = f"{hours:02d}:{minutes:02d}"
    except pymysql.Error as e:
        print(f"Errore durante il recupero delle lezioni per la firma: {e}")
        lezioni = []
    finally:
        if connection: connection.close()
    return render_template('teacher/firma_presenza.html', lezioni=lezioni)


@teacher_bp.route('/salva-firma-docente', methods=['POST'])
@teacher_required
def salva_firma_docente():
    id_docente_loggato = session['user_id']
    id_lezione = request.form.get('lezione')
    note = request.form.get('note', '')
    presenza_valore = 'conferma_presenza' in request.form

    if not id_lezione: return "Errore: Selezionare una lezione.", 400
    
    connection = get_db_connection()
    if connection is None: return "Errore di connessione al database", 500
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO Docenza (docente, lezione, presenza, note) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (id_docente_loggato, id_lezione, presenza_valore, note))
            connection.commit()
    except pymysql.Error as e:
        print(f"ERRORE durante la registrazione della firma: {e}")
        connection.rollback()
    finally:
        if connection: connection.close()
            
    return redirect(url_for('teacher_bp.serve_dashboard_page'))
