from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from datetime import date
import pymysql.cursors
from functools import wraps

from auth_routes import get_db_connection  # Assicurati che questa importazione sia corretta

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

@manager_bp.route('/insegnamenti', methods=['GET', 'POST'])
@manager_required
def gestione_insegnamenti():
    """
    Pagina per la gestione degli insegnamenti.
    GET: Mostra il form e la lista degli insegnamenti.
    POST: Aggiunge o elimina un insegnamento.
    """
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # --- LOGICA POST (AGGIUNTA O ELIMINAZIONE) ---
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            id_insegnamento = request.form['idInsegnamento']
            nome_insegnamento = request.form['nome']
            id_corso = request.form['corso']
            anno_corso = request.form['annoCorso']
            durata_ore = request.form['durataOre']

            try:
                # --- MODIFICA 1: Logica di inserimento migliorata ---
                # Prima controlliamo se l'insegnamento esiste già. Se non esiste, lo creiamo.
                cursor.execute("INSERT INTO Insegnamento (idInsegnamento, Nome) VALUES (%s, %s) ON DUPLICATE KEY UPDATE Nome=Nome", 
                               (id_insegnamento, nome_insegnamento))
                
                # Poi inseriamo il collegamento nel piano di studi, gestendo eventuali duplicati.
                cursor.execute("""
                    INSERT INTO PianoDiStudi (insegnamento, corso, anno_di_corso, durata) 
                    VALUES (%s, %s, %s, %s)
                """, (id_insegnamento, id_corso, anno_corso, durata_ore))
                
                conn.commit()
                flash('Insegnamento aggiunto al piano di studi con successo!', 'success')

            except pymysql.err.IntegrityError:
                # Questo errore scatta se si tenta di aggiungere una combinazione insegnamento-corso che già esiste
                flash('Questo insegnamento è già presente in questo piano di studi.', 'warning')
                conn.rollback()
            except pymysql.Error as err:
                flash(f"Errore durante l'aggiunta: {err}", 'danger')
                conn.rollback()

        elif action == 'delete':
            # --- MODIFICA 2: Logica di eliminazione intelligente ---
            # Per eliminare in modo specifico, abbiamo bisogno sia dell'ID dell'insegnamento che dell'ID del corso.
            id_insegnamento_da_eliminare = request.form['id_insegnamento_da_eliminare']
            id_corso_da_cui_eliminare = request.form['id_corso_da_cui_eliminare']
            
            try:
                # 1. Eliminiamo solo la riga specifica dalla tabella di collegamento `PianoDiStudi`.
                cursor.execute("DELETE FROM PianoDiStudi WHERE insegnamento = %s AND corso = %s", 
                               (id_insegnamento_da_eliminare, id_corso_da_cui_eliminare))
                
                # 2. Controlliamo se l'insegnamento è rimasto "orfano" (non più presente in nessun piano di studi).
                cursor.execute("SELECT COUNT(*) AS count FROM PianoDiStudi WHERE insegnamento = %s", (id_insegnamento_da_eliminare,))
                count_result = cursor.fetchone()
                
                # 3. Se il conteggio è 0, eliminiamo l'insegnamento dalla tabella principale `Insegnamenti`.
                if count_result and count_result['count'] == 0:
                    cursor.execute("DELETE FROM Insegnamento WHERE idInsegnamento = %s", (id_insegnamento_da_eliminare,))
                    flash('Insegnamento rimosso dal piano di studi e dalla lista generale perché non più utilizzato.', 'success')
                else:
                    flash('Insegnamento rimosso correttamente dal piano di studi.', 'success')

                conn.commit()

            except pymysql.Error as err:
                flash(f"Errore durante l'eliminazione: {err}", 'danger')
                conn.rollback()
        
        return redirect(url_for('manager_bp.gestione_insegnamenti'))

    # --- LOGICA GET (VISUALIZZAZIONE PAGINA) ---
    
    # 1. Query per ottenere tutti gli insegnamenti con i dettagli del corso
    # --- MODIFICA 3: Aggiunto C.idCorso per passarlo al form di eliminazione ---
    query_insegnamenti = """
        SELECT 
            I.idInsegnamento, 
            I.Nome AS nome_insegnamento,
            C.idCorso, 
            C.Nome AS nome_corso,
            C.Tipologia AS tipologia_corso,
            P.anno_di_corso, 
            P.durata
        FROM PianoDiStudi P
        JOIN Insegnamento I ON P.insegnamento = I.idInsegnamento
        JOIN Corso C ON P.corso = C.idCorso
        ORDER BY C.Nome, I.Nome
    """
    cursor.execute(query_insegnamenti)
    lista_insegnamenti = cursor.fetchall()

    # 2. Query per ottenere la lista dei corsi per il menu a tendina
    # --- MODIFICA 4: Concatena Nome e Tipologia per il menu a tendina ---
    cursor.execute("""
        SELECT 
            idCorso, 
            CONCAT(Nome, ' - ', Tipologia) AS nome_completo 
        FROM Corso 
        ORDER BY Nome
    """)
    lista_corsi = cursor.fetchall()

    cursor.close()
    conn.close()

    # Assicurati che il nome del template sia corretto
    return render_template('manager/teaching_management.html', 
                           insegnamenti=lista_insegnamenti, 
                           corsi=lista_corsi)


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




@manager_bp.route('/lezioni', methods=['GET', 'POST'])
@manager_required
def gestione_lezioni():
    """
    Pagina per la gestione e pianificazione del calendario delle lezioni.
    """
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            insegnamento = request.form['insegnamento']
            aula = request.form['aula']
            ora_inizio = request.form['ora_inizio']
            ora_fine = request.form['ora_fine']
            
            try:
                sql = "INSERT INTO Lezione (insegnamento, aula, ora_inizio, ora_fine) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (insegnamento, aula, ora_inizio, ora_fine))
                conn.commit()
                flash('Lezione aggiunta al calendario con successo!', 'success')
            except pymysql.Error as err:
                flash(f"Errore durante l'aggiunta della lezione: {err}", 'danger')
                conn.rollback()

        elif action == 'delete':
            id_lezione_da_eliminare = request.form.get('idLezioneDaEliminare')
            try:
                cursor.execute("DELETE FROM Lezione WHERE idLezione = %s", (id_lezione_da_eliminare,))
                conn.commit()
                flash('Lezione eliminata con successo!', 'success')
            except pymysql.Error as err:
                flash(f"Errore durante l'eliminazione: {err}", 'danger')
                conn.rollback()
        
        cursor.close()
        conn.close()
        return redirect(url_for('manager_bp.gestione_lezioni'))

    # Logica GET: Prepara i dati per il form
    # Query per popolare il menu a tendina degli insegnamenti
    cursor.execute("SELECT idInsegnamento, Nome FROM Insegnamento ORDER BY Nome")
    insegnamenti = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('manager/lesson_management.html', insegnamenti=insegnamenti)


@manager_bp.route('/lezioni/api')
@manager_required
def lezioni_api():
    """
    Rotta API per fornire le lezioni al calendario in formato JSON.
    Ora filtra i risultati in base all'intervallo di date fornito da FullCalendar.
    """
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 1. Ottieni i parametri start e end inviati da FullCalendar
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    # Se i parametri non sono presenti, la query fallirebbe. 
    # Anche se FullCalendar li invia sempre, questo è un controllo di sicurezza.
    if not start_date or not end_date:
        return jsonify([])

    try:
        # 2. Modifica la query per usare i parametri in una clausola WHERE
        # Questo seleziona solo gli eventi visibili nella finestra temporale corrente.
        # La logica è: dammi gli eventi che iniziano prima della fine della finestra
        # e finiscono dopo l'inizio della finestra.
        query = """
            SELECT 
                L.idLezione AS id,
                I.Nome AS title,
                L.ora_inizio AS start,
                L.ora_fine AS end,
                L.aula AS extended_aula 
            FROM Lezione L
            JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
            WHERE L.ora_inizio < %s AND L.ora_fine > %s
        """
        cursor.execute(query, (end_date, start_date))
        lezioni = cursor.fetchall()
        
        # 3. Converti le date in formato stringa ISO (fondamentale per JSON)
        for lezione in lezioni:
            if lezione.get('start'):
                lezione['start'] = lezione['start'].isoformat()
            if lezione.get('end'):
                lezione['end'] = lezione['end'].isoformat()

        cursor.close()
        conn.close()
        
        return jsonify(lezioni)

    except pymysql.Error as err:
        # Se c'è un errore SQL, stampalo nel terminale di Flask per il debug
        print(f"Errore API Lezioni: {err}")
        # E restituisci un errore 500 esplicito
        return jsonify({"error": "Errore interno del server"}), 500

