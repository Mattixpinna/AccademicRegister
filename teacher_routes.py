from flask import Blueprint, request, render_template, redirect, url_for, session, flash
import pymysql.cursors
from functools import wraps
from database import get_db_connection
from datetime import date, datetime, time, timedelta
import pymysql

# Decoratore per proteggere le rotte riservate ai docenti
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

# Gestione della rotta per la dashboard del docente
@teacher_bp.route('/dashboard')
@teacher_required
def serve_dashboard_page():
    teacher_name = session.get('user_name', 'Docente')
    return render_template('teacher/teacher_home.html', teacher_name=teacher_name)

# Gestione della rotta per la selezione della lezione
@teacher_bp.route('/seleziona_lezione')
@teacher_required
def serve_appello_page():
    id_docente_loggato = session['user_id']
    lezioni = []
    today = date.today()
    
    # --- CALCOLO ANNO ACCADEMICO CORRENTE ---
    # Se il mese è prima di Settembre (1-8), siamo nella seconda parte dell'anno accademico (es. 2024/2025 se oggi è Marzo 2025)
    # Se il mese è Settembre o dopo (9-12), siamo nella prima parte (es. 2024/2025 se oggi è Nov 2024)
    if today.month < 9:
        anno_accademico_corrente = f"{today.year - 1}/{today.year}"
    else:
        anno_accademico_corrente = f"{today.year}/{today.year + 1}"
    # ----------------------------------------

    connection = get_db_connection()

    if connection is None:
        return "Errore: Impossibile connettersi al database.", 500

    try:
        with connection.cursor() as cursor:
            # Aggiunta la condizione sulla tabella Cattedra
            sql = """
                SELECT L.idLezione, I.Nome, TIME(L.ora_inizio) AS OraInizio
                FROM Lezione AS L
                JOIN Insegnamento AS I ON L.insegnamento = I.idInsegnamento
                JOIN Cattedra AS C ON I.idInsegnamento = C.insegnamento
                WHERE DATE(L.ora_inizio) = %s 
                  AND C.docente = %s
                  AND C.anno_accademico = %s
                ORDER BY OraInizio
            """
            # Passiamo anno_accademico_corrente come terzo parametro
            cursor.execute(sql, (today, id_docente_loggato, anno_accademico_corrente))
            lezioni = cursor.fetchall()

            for lezione in lezioni:
                if 'OraInizio' in lezione and lezione['OraInizio']:
                    total_seconds = int(lezione['OraInizio'].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    lezione['OraInizio_formatted'] = f"{hours:02d}:{minutes:02d}"
                    
    except pymysql.Error as e:
        # È utile loggare anche l'anno accademico che ha generato l'errore per debug
        print(f"Errore durante il recupero delle lezioni (A.A. {anno_accademico_corrente}): {e}")
        lezioni = []
    finally:
        if connection:
            connection.close()

    return render_template('teacher/lessons_menu.html', lezioni=lezioni)


# Gestione della rotta per la registrazione delle presenze degli studenti
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
        # Controlla se il docente ha accesso alla lezione specificata
        with connection.cursor() as cursor:
            sql_auth_check = """
                SELECT L.idLezione FROM Lezione L
                JOIN Cattedra C ON L.insegnamento = C.insegnamento
                WHERE L.idLezione = %s AND C.docente = %s
            """
            cursor.execute(sql_auth_check, (id_lezione, id_docente_loggato))
            if cursor.fetchone() is None:
                return "Accesso non autorizzato a questa lezione.", 403
            
            # Recupera le informazioni della lezione
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

                # Calcola l'anno accademico della lezione
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
                
                
                # Ottieni ID e orario degli studenti già presenti
                sql_presenti = "SELECT studente, orario_ingresso FROM Presenza WHERE lezione = %s"
                cursor.execute(sql_presenti, (id_lezione,))
                presenti_result = cursor.fetchall()
                
                # Creare un dizionario per accesso rapido: { 'matricola': orario_datetime, ... }
                map_presenze = {str(row['studente']): row['orario_ingresso'] for row in presenti_result}

                # Aggiungere lo stato e l'orario a ogni studente
                for studente in studenti:
                    matricola_str = str(studente['matricola'])
                    
                    if matricola_str in map_presenze:
                        studente['stato'] = 'presente'
                        # Formattare l'orario per inserirlo nel value dell'input time (HH:MM)
                        orario_db = map_presenze[matricola_str]
                        if isinstance(orario_db, timedelta):
                            # Gestione caso timedelta (alcuni driver MySQL ritornano timedelta per campi TIME)
                            tot_seconds = int(orario_db.total_seconds())
                            hours = tot_seconds // 3600
                            minutes = (tot_seconds % 3600) // 60
                            studente['orario_esistente'] = f"{hours:02d}:{minutes:02d}"
                        elif orario_db:
                            # Gestione caso datetime o time
                            studente['orario_esistente'] = orario_db.strftime('%H:%M')
                        else:
                             studente['orario_esistente'] = ""
                    else:
                        studente['stato'] = 'assente'
                        studente['orario_esistente'] = "" # O l'orario di default della lezione se preferisci
                
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
    
    # Verifica che l'ID lezione esista, altrimenti torna indietro (ad una pagina sicura, es. home docente)
    if not id_lezione:
        flash("Errore: ID Lezione non trovato.", 'error')
        # Sostituisci 'teacher_bp.home' con la tua rotta principale se necessario
        return redirect(url_for('teacher_bp.home'))

    # 1. INSIEME A (FORM): Studenti che il docente ha spuntato come 'presente'
    # Se la checkbox non è spuntata, il browser non invia il valore, quindi qui avremo solo i presenti desiderati.
    studenti_form_ids = {
        key.split('_')[1] for key, value in request.form.items()
        if key.startswith('studente_') and value == 'presente'
    }

    connection = get_db_connection()
    if connection is None:
        flash("Errore di connessione al database.", "error")
        # Tenta di tornare alla pagina di inserimento. 
        # NOTA: Assicurati che il nome della funzione qui sotto sia ESATTO.
        return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))
    
    try:
        with connection.cursor() as cursor:
            # Recupera orario lezione (serve come fallback per l'orario di ingresso)
            sql_lezione = "SELECT ora_inizio FROM Lezione WHERE idLezione = %s"
            cursor.execute(sql_lezione, (id_lezione,))
            lezione_db = cursor.fetchone()

            if not lezione_db:
                flash("Errore: lezione non trovata nel database.", 'error')
                return redirect(url_for('teacher_bp.serve_registra_presenze_page', lezione=id_lezione))
            
            orario_inizio_lezione = lezione_db['ora_inizio']

            # 2. INSIEME B (DATABASE): Studenti che risultano GIÀ segnati come presenti nel DB
            sql_gia_presenti = "SELECT studente FROM Presenza WHERE lezione = %s"
            cursor.execute(sql_gia_presenti, (id_lezione,))
            studenti_db_ids = {str(item['studente']) for item in cursor.fetchall()}
            
            # --- CALCOLO DELLE DIFFERENZE (LOGICA TOGGLE) ---
            
            # DA AGGIUNGERE: Presenti nel Form MA assenti nel DB
            ids_da_aggiungere = studenti_form_ids - studenti_db_ids
            
            # DA RIMUOVERE: Presenti nel DB MA assenti nel Form (deselezionati)
            ids_da_rimuovere = studenti_db_ids - studenti_form_ids

            messaggi = []

            # --- FASE 1: RIMOZIONE ---
            if ids_da_rimuovere:
                # Genera lista di tuple (id_studente, id_lezione)
                params_delete = [(sid, id_lezione) for sid in ids_da_rimuovere]
                sql_delete = "DELETE FROM Presenza WHERE studente = %s AND lezione = %s"
                cursor.executemany(sql_delete, params_delete)
                messaggi.append(f"Rimosse {len(ids_da_rimuovere)} presenze")

            # --- FASE 2: INSERIMENTO ---
            if ids_da_aggiungere:
                dati_da_inserire = []
                oggi = date.today()

                for sid in ids_da_aggiungere:
                    orario_form = request.form.get(f'orario_{sid}')
                    orario_ingresso = None

                    # Tenta di usare l'orario specifico inserito nel form
                    if orario_form:
                        try:
                            ore, minuti = map(int, orario_form.split(':'))
                            orario_ingresso = datetime.combine(oggi, time(hour=ore, minute=minuti))
                        except (ValueError, TypeError):
                            orario_ingresso = None # Formato non valido, passa al fallback
                    
                    # Fallback: usa l'orario di inizio della lezione
                    if not orario_ingresso:
                        # Gestione robusta del tipo di dato (datetime vs time vs timedelta)
                        if isinstance(orario_inizio_lezione, datetime):
                             orario_ingresso = orario_inizio_lezione
                        elif isinstance(orario_inizio_lezione, time):
                             orario_ingresso = datetime.combine(oggi, orario_inizio_lezione)
                        elif isinstance(orario_inizio_lezione, timedelta):
                             # Se il DB restituisce un timedelta (es. MySQL a volte lo fa per campi TIME)
                             base_time = (datetime.min + orario_inizio_lezione).time()
                             orario_ingresso = datetime.combine(oggi, base_time)
                        else:
                             # Caso estremo
                             orario_ingresso = datetime.now()

                    dati_da_inserire.append((sid, id_lezione, orario_ingresso))

                sql_insert = "INSERT INTO Presenza (studente, lezione, orario_ingresso) VALUES (%s, %s, %s)"
                cursor.executemany(sql_insert, dati_da_inserire)
                messaggi.append(f"Aggiunte {len(dati_da_inserire)} presenze")

            connection.commit()
            
            if messaggi:
                flash(". ".join(messaggi) + ".", 'success')
            elif not ids_da_aggiungere and not ids_da_rimuovere:
                flash("Nessuna modifica effettuata.", 'info')

    except pymysql.Error as e:
        print(f"ERRORE SQL durante il salvataggio delle presenze: {e}")
        if connection:
            connection.rollback()
        flash("Si è verificato un errore tecnico durante il salvataggio.", 'error')
    finally:
        if connection:
            connection.close()
            
    # --- ATTENZIONE QUI ---
    # Usa il nome ESATTO della funzione Python che renderizza la pagina.
    # Se il tuo file ha "def serve_firma_presenza_page():", scrivi 'teacher_bp.serve_firma_presenza_page'
    # Se il tuo file ha "def serve_registra_presenze_page():", scrivi 'teacher_bp.serve_registra_presenze_page'
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



@teacher_bp.route('/agenda', methods=['GET'])
@teacher_required
def serve_agenda_page():
    id_docente = session.get('user_id') 
    id_insegnamento_selected = request.args.get('id_insegnamento', type=int)

    conn = get_db_connection()
    insegnamenti = []
    lezioni = []
    nome_insegnamento_selezionato = ""

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Recupera gli insegnamenti
            sql_insegnamenti = """
                SELECT I.idInsegnamento, I.Nome, C.anno_accademico
                FROM Cattedra C
                JOIN Insegnamento I ON C.insegnamento = I.idInsegnamento
                WHERE C.docente = %s
                ORDER BY C.anno_accademico DESC, I.Nome ASC
            """
            cursor.execute(sql_insegnamenti, (id_docente,))
            insegnamenti = cursor.fetchall()

            # 2. Recupera le lezioni se un insegnamento è selezionato
            if id_insegnamento_selected:
                check_ins = next((i for i in insegnamenti if i['idInsegnamento'] == id_insegnamento_selected), None)
                
                if check_ins:
                    nome_insegnamento_selezionato = check_ins['Nome']
                
                    sql_lezioni = """
                        SELECT 
                            DATE_FORMAT(L.ora_inizio, '%%d/%%m/%%Y') as data_str,
                            DATE_FORMAT(L.ora_inizio, '%%H:%%i') as ora_inizio,
                            DATE_FORMAT(L.ora_fine, '%%H:%%i') as ora_fine,
                            COALESCE(D.presenza, 0) as is_svolta,
                            D.note
                        FROM Lezione L
                        LEFT JOIN Docenza D ON L.idLezione = D.lezione AND D.docente = %s
                        WHERE L.insegnamento = %s
                        ORDER BY L.ora_inizio DESC
                    """
                    cursor.execute(sql_lezioni, (id_docente, id_insegnamento_selected))
                    lezioni = cursor.fetchall()
                    
                    # Nota: Non serve più il ciclo for in Python per formattare la data,
                    # perché lo abbiamo fatto direttamente in SQL con 'data_str'.
                    
                else:
                    flash("Insegnamento non valido o non assegnato.", "danger")

    except pymysql.Error as e:
        print(f"Errore DB: {e}")
        flash("Errore nel recupero dell'agenda.", "danger")
    finally:
        conn.close()

    return render_template('teacher/agenda.html', 
                           insegnamenti=insegnamenti,
                           lezioni=lezioni,
                           selected_id=id_insegnamento_selected,
                           nome_insegnamento=nome_insegnamento_selezionato)
