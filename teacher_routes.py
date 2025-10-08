from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from datetime import date, datetime, time
import pymysql.cursors
from functools import wraps
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
            # ... (il codice per il controllo autorizzazione e recupero lezione_info rimane invariato)
            sql_auth_check = """
                SELECT L.idLezione FROM Lezione L
                JOIN Cattedra C ON L.insegnamento = C.insegnamento
                WHERE L.idLezione = %s AND C.docente = %s
            """
            cursor.execute(sql_auth_check, (id_lezione, id_docente_loggato))
            if cursor.fetchone() is None:
                return "Accesso non autorizzato a questa lezione.", 403

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

                # ... (il codice per calcolare l'anno accademico rimane invariato)
                data_lezione = lezione_raw['ora_inizio']
                anno_lezione = data_lezione.year
                mese_lezione = data_lezione.month
                
                if mese_lezione >= 9:
                    anno_accademico_lezione = f"{anno_lezione}/{anno_lezione + 1}"
                else:
                    anno_accademico_lezione = f"{anno_lezione - 1}/{anno_lezione}"
                
                # Recupera la lista di tutti gli studenti iscritti
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
                
                # --- NUOVO BLOCCO: RECUPERA STATO PRESENZE ---
                # 1. Ottieni gli ID degli studenti già segnati come presenti
                sql_presenti = "SELECT studente FROM Presenza WHERE lezione = %s"
                cursor.execute(sql_presenti, (id_lezione,))
                presenti_result = cursor.fetchall()
                studenti_presenti_ids = {str(item['studente']) for item in presenti_result}

                # 2. Aggiungi lo stato ('presente' o 'assente') a ogni studente
                for studente in studenti:
                    if str(studente['matricola']) in studenti_presenti_ids:
                        studente['stato'] = 'presente'
                    else:
                        studente['stato'] = 'assente'
                # --- FINE NUOVO BLOCCO ---
                
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
        flash("Errore: ID Lezione non trovato.", 'error')
        return redirect(url_for('teacher_bp.serve_appello_page'))

    # Estrai gli studenti segnati come 'presente'
    studenti_presenti_ids = {
        key.split('_')[1] for key, value in request.form.items()
        if key.startswith('studente_') and value == 'presente'
    }

    if not studenti_presenti_ids:
        flash("Nessuno studente selezionato. Nessuna presenza è stata registrata.", 'warning')
        return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))

    connection = get_db_connection()
    if connection is None:
        flash("Errore di connessione al database.", "error")
        return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))
    
    try:
        with connection.cursor() as cursor:
            sql_lezione = "SELECT ora_inizio FROM Lezione WHERE idLezione = %s"
            cursor.execute(sql_lezione, (id_lezione,))
            lezione_db = cursor.fetchone()

            if not lezione_db or not lezione_db.get('ora_inizio'):
                flash("Errore: impossibile trovare l'orario di inizio per questa lezione.", 'error')
                return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))
            
            # L'orario viene restituito come oggetto time
            orario_inizio_lezione = lezione_db['ora_inizio']

            # Recupera gli studenti GIÀ presenti nel DB per evitare duplicati
            sql_gia_presenti = "SELECT studente FROM Presenza WHERE lezione = %s"
            cursor.execute(sql_gia_presenti, (id_lezione,))
            studenti_gia_presenti_ids = {str(item['studente']) for item in cursor.fetchall()}
            
            # Filtra per ottenere solo i NUOVI studenti da inserire
            studenti_nuovi_da_inserire_ids = studenti_presenti_ids - studenti_gia_presenti_ids

            if not studenti_nuovi_da_inserire_ids:
                flash("Tutti gli studenti selezionati erano già stati segnati come presenti.", 'info')
                return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))

            # Prepara i dati per l'inserimento
            dati_da_inserire = []
            oggi = date.today()

            for sid in studenti_nuovi_da_inserire_ids:
                orario_form = request.form.get(f'orario_{sid}')

                if orario_form:
                    # Se l'utente ha inserito un orario, usa quello
                    try:
                        ore, minuti = map(int, orario_form.split(':'))
                        orario_ingresso = datetime.combine(oggi, time(hour=ore, minute=minuti))
                    except (ValueError, TypeError):
                        # Fallback in caso di formato non valido (puoi mantenerlo o cambiarlo)
                        orario_ingresso = datetime.combine(oggi, orario_inizio_lezione)
                else:
                    # ---> MODIFICA 2: Se non viene specificato un orario, combina la data
                    # di oggi con l'orario di inizio della lezione recuperato prima.
                    orario_ingresso = orario_inizio_lezione
                
                dati_da_inserire.append((sid, id_lezione, orario_ingresso))

            # Esegui l'inserimento
            if dati_da_inserire:
                sql_insert = "INSERT INTO Presenza (studente, lezione, orario_ingresso) VALUES (%s, %s, %s)"
                cursor.executemany(sql_insert, dati_da_inserire)
                connection.commit()
                
                num_presenze = len(dati_da_inserire)
                flash(f"{num_presenze} nuove presenze registrate con successo!", 'success')

    except pymysql.Error as e:
        print(f"ERRORE durante il salvataggio delle presenze: {e}")
        connection.rollback()
        flash("Si è verificato un errore durante il salvataggio.", 'error')
    finally:
        if connection:
            connection.close()
            
    return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))





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

    if not id_lezione:
        flash('Errore: Devi selezionare una lezione.', 'error')
        return redirect(url_for('teacher_bp.serve_firma_page'))

    connection = get_db_connection()
    if connection is None:
        flash("Errore di connessione al database.", "error")
        return redirect(url_for('teacher_bp.serve_dashboard_page'))
    
    try:
        with connection.cursor() as cursor:
            # Controlla se la firma per questa lezione esiste già
            # Selezioniamo '1' per efficienza: ci interessa solo sapere se la riga esiste.
            sql_check = "SELECT 1 FROM Docenza WHERE docente = %s AND lezione = %s" # <-- RIGA MODIFICATA
            cursor.execute(sql_check, (id_docente_loggato, id_lezione))
            
            if cursor.fetchone():
                flash('Hai già firmato per questa lezione.', 'warning')
                return redirect(url_for('teacher_bp.serve_firma_presenza_page'))

            sql_insert = "INSERT INTO Docenza (docente, lezione, presenza, note) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_insert, (id_docente_loggato, id_lezione, presenza_valore, note))
            connection.commit()
            
            flash('Firma registrata con successo!', 'success')
            
    except pymysql.Error as e:
        print(f"ERRORE durante la registrazione della firma: {e}")
        connection.rollback()
        flash('Si è verificato un errore durante la registrazione della firma.', 'error')
    finally:
        if connection:
            connection.close()
            
    return redirect(url_for('teacher_bp.serve_firma_presenza_page'))
