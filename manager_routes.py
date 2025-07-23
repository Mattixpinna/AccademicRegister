# from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
# from datetime import date, datetime
# import pymysql.cursors
# from functools import wraps
# from werkzeug.security import generate_password_hash # Import per hashing password

# from auth_routes import get_db_connection  # Assicurati che questa importazione sia corretta

# # --- CREAZIONE DEL BLUEPRINT PER IL MANAGER ---
# manager_bp = Blueprint('manager_bp', __name__,
#                        url_prefix='/manager',  # Aggiunge '/manager' prima di tutte le rotte
#                        template_folder='templates',
#                        static_folder='static')

# # --- DECORATOR PER LA PROTEZIONE DELLE ROTTE DEL MANAGER ---
# def manager_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if session.get('user_role') != 'manager':
#             flash("Accesso non autorizzato. È necessario essere un manager.", "danger")
#             return redirect(url_for('auth_bp.login'))
#         return f(*args, **kwargs)
#     return decorated_function


# # --- ROTTA PRINCIPALE PER LA DASHBOARD DEL MANAGER ---
# @manager_bp.route('/dashboard')
# @manager_required
# def dashboard():
#     return render_template('manager/manager_home.html')


# # --- ROTTA PER LA GESTIONE DEGLI INSEGNAMENTI ---
# @manager_bp.route('/insegnamenti', methods=['GET', 'POST'])
# @manager_required
# def gestione_insegnamenti():
#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return render_template('manager/teaching_management.html', insegnamenti=[], corsi=[])
    
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             if request.method == 'POST':
#                 action = request.form.get('action')
#                 if action == 'add':
#                     # ... (logica di aggiunta invariata)
#                     id_insegnamento = request.form['idInsegnamento']
#                     nome_insegnamento = request.form['nome']
#                     id_corso = request.form['corso']
#                     anno_corso = request.form['annoCorso']
#                     durata_ore = request.form['durataOre']
#                     data_inizio = request.form['dataInizio']
#                     data_fine = request.form['dataFine']

#                     if not data_inizio or not data_fine:
#                         flash("Le date di inizio e fine sono obbligatorie.", 'danger')
#                     else:
#                         try:
#                             cursor.execute("INSERT INTO Insegnamento (idInsegnamento, Nome) VALUES (%s, %s) ON DUPLICATE KEY UPDATE Nome=VALUES(Nome)", 
#                                            (id_insegnamento, nome_insegnamento))
                            
#                             query_piano_studi = """
#                                 INSERT INTO PianoDiStudi (insegnamento, corso, anno_di_corso, durata, data_inizio, data_fine) 
#                                 VALUES (%s, %s, %s, %s, %s, %s)
#                             """
#                             cursor.execute(query_piano_studi, (id_insegnamento, id_corso, anno_corso, durata_ore, data_inizio, data_fine))
                            
#                             conn.commit()
#                             flash('Insegnamento aggiunto al piano di studi con successo!', 'success')

#                         except pymysql.err.IntegrityError:
#                             flash('Questo insegnamento è già presente in questo piano di studi.', 'warning')
#                             conn.rollback()
#                         except pymysql.Error as err:
#                             flash(f"Errore durante l'aggiunta: {err}", 'danger')
#                             conn.rollback()

#                 elif action == 'delete':
#                     # ... (logica di eliminazione invariata)
#                     id_insegnamento_da_eliminare = request.form['id_insegnamento_da_eliminare']
#                     id_corso_da_cui_eliminare = request.form['id_corso_da_cui_eliminare']
#                     data_inizio = request.form['data_inizio']
#                     data_fine = request.form['data_fine']
                    
#                     try:
#                         data_inizio_sql = datetime.strptime(data_inizio, '%d/%m/%Y').strftime('%Y-%m-%d')
#                         data_fine_sql = datetime.strptime(data_fine, '%d/%m/%Y').strftime('%Y-%m-%d')

#                         cursor.execute("DELETE FROM PianoDiStudi WHERE insegnamento = %s AND corso = %s AND data_inizio = %s AND data_fine = %s", 
#                                        (id_insegnamento_da_eliminare, id_corso_da_cui_eliminare, data_inizio_sql, data_fine_sql))

#                         cursor.execute("SELECT COUNT(*) AS count FROM PianoDiStudi WHERE insegnamento = %s", (id_insegnamento_da_eliminare,))
#                         count_result = cursor.fetchone()
                        
#                         if count_result and count_result['count'] == 0:
#                             cursor.execute("DELETE FROM Insegnamento WHERE idInsegnamento = %s", (id_insegnamento_da_eliminare,))
#                             flash('Insegnamento rimosso dal piano di studi e dalla lista generale perché non più utilizzato.', 'success')
#                         else:
#                             flash('Insegnamento rimosso correttamente dal piano di studi.', 'success')

#                         conn.commit()

#                     except pymysql.Error as err:
#                         flash(f"Errore durante l'eliminazione: {err}", 'danger')
#                         conn.rollback()
                
#                 return redirect(url_for('manager_bp.gestione_insegnamenti'))

#             # --- LOGICA GET (VISUALIZZAZIONE PAGINA) ---
#             query_insegnamenti = """
#                 SELECT 
#                     I.idInsegnamento, I.Nome AS nome_insegnamento,
#                     C.idCorso, C.Nome AS nome_corso, C.Tipologia AS tipologia_corso,
#                     P.anno_di_corso, P.durata, P.data_inizio, P.data_fine
#                 FROM PianoDiStudi P
#                 JOIN Insegnamento I ON P.insegnamento = I.idInsegnamento
#                 JOIN Corso C ON P.corso = C.idCorso
#                 ORDER BY C.Nome, I.Nome
#             """
#             cursor.execute(query_insegnamenti)
#             lista_insegnamenti = cursor.fetchall()

#             for ins in lista_insegnamenti:
#                 if ins.get('data_inizio') and isinstance(ins['data_inizio'], date):
#                     ins['data_inizio'] = ins['data_inizio'].strftime('%d/%m/%Y')
#                 if ins.get('data_fine') and isinstance(ins['data_fine'], date):
#                     ins['data_fine'] = ins['data_fine'].strftime('%d/%m/%Y')

#             cursor.execute("SELECT idCorso, CONCAT(Nome, ' - ', Tipologia) AS nome_completo FROM Corso ORDER BY Nome")
#             lista_corsi = cursor.fetchall()

#             return render_template('manager/teaching_management.html', 
#                                    insegnamenti=lista_insegnamenti, 
#                                    corsi=lista_corsi)
#     finally:
#         if conn:
#             conn.close()


# # --- ROTTE PER LA GESTIONE DEGLI STUDENTI ---
# @manager_bp.route('/studenti')
# @manager_required
# def gestione_studenti():
#     conn = get_db_connection()
#     corsi = []
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             cursor.execute("SELECT idCorso, CONCAT(Nome, ' - ', Tipologia) AS nome_completo FROM Corso ORDER BY Nome")
#             corsi = cursor.fetchall()
#     except pymysql.Error as e:
#         flash(f"Errore del database: {e}", "danger")
#     finally:
#         if conn: conn.close()
#     return render_template('manager/student_management.html', corsi=corsi)


# # ==============================================================================
# # === INIZIO SEZIONE GESTIONE DOCENTI (MODIFICATA E CORRETTA) ===================
# # ==============================================================================

# @manager_bp.route('/docenti', methods=['GET'])
# @manager_required
# def gestione_docenti():
#     """
#     Pagina Unica: Carica i dati per i form e gestisce la visualizzazione dell'andamento.
#     """
#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return render_template('manager/teacher_management.html', docenti=[], insegnamenti=[], cattedre=[], risultati=None)

#     docenti, insegnamenti, cattedre, risultati = [], [], [], None
#     docente_selezionato, insegnamento_selezionato = None, None
#     id_docente_corrente = request.args.get('docente_andamento', type=int)
#     id_insegnamento_corrente = request.args.get('insegnamento_andamento', type=int)

#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             # 1. Recupera sempre tutti i docenti per i menu
#             cursor.execute("SELECT idDocente, Nome, Cognome FROM Docente WHERE ruolo = 'docente' ORDER BY Cognome, Nome")
#             docenti = cursor.fetchall()
            
#             # 2. Recupera sempre tutti gli insegnamenti per i menu
#             cursor.execute("SELECT idInsegnamento, Nome FROM Insegnamento ORDER BY Nome")
#             insegnamenti = cursor.fetchall()

#             # 3. Recupera le cattedre per il menu di rimozione (senza idCattedra)
#             sql_cattedre = """
#                 SELECT D.idDocente, I.idInsegnamento, C.anno_accademico,
#                        D.Nome AS NomeDocente, D.Cognome, I.Nome AS NomeInsegnamento
#                 FROM Cattedra C
#                 JOIN Docente D ON C.docente = D.idDocente
#                 JOIN Insegnamento I ON C.insegnamento = I.idInsegnamento
#                 ORDER BY D.Cognome, I.Nome
#             """
#             cursor.execute(sql_cattedre)
#             cattedre = cursor.fetchall()

#             # 4. Se è stata fatta una ricerca per l'andamento, esegui la query
#             if id_docente_corrente and id_insegnamento_corrente:
#                 sql_andamento = """
#                     SELECT DATE_FORMAT(L.ora_inizio, '%%d/%%m/%%Y') AS giorno_lezione, D.presenza, D.note
#                     FROM Docenza D
#                     JOIN Lezione L ON D.lezione = L.idLezione
#                     WHERE D.docente = %s AND L.insegnamento = %s
#                     ORDER BY L.ora_inizio DESC
#                 """
#                 cursor.execute(sql_andamento, (id_docente_corrente, id_insegnamento_corrente))
#                 risultati = cursor.fetchall()
                
#                 docente_selezionato = next((d for d in docenti if d['idDocente'] == id_docente_corrente), None)
#                 insegnamento_selezionato = next((i for i in insegnamenti if i['idInsegnamento'] == id_insegnamento_corrente), None)

#     except pymysql.Error as e:
#         flash(f"Errore nel recupero dei dati: {e}", 'danger')
#     finally:
#         if conn:
#             conn.close()
            
#     return render_template('manager/teacher_management.html', 
#                            docenti=docenti, 
#                            insegnamenti=insegnamenti, 
#                            cattedre=cattedre,
#                            risultati=risultati,
#                            docente_selezionato=docente_selezionato,
#                            insegnamento_selezionato=insegnamento_selezionato,
#                            id_docente_corrente=id_docente_corrente,
#                            id_insegnamento_corrente=id_insegnamento_corrente)

# @manager_bp.route('/docenti/aggiungi', methods=['POST'])
# @manager_required
# def aggiungi_docente():
#     # CORREZIONE: Legge 'idDocente' dal form invece di 'codice_docente'
#     id_docente = request.form.get('idDocente')
#     nome = request.form.get('nome')
#     cognome = request.form.get('cognome')
#     email = request.form.get('email')
#     password = request.form.get('password')

#     if not all([id_docente, nome, cognome, email, password]):
#         flash('Tutti i campi sono obbligatori.', 'warning')
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     password_hash = generate_password_hash(password)
#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     try:
#         with conn.cursor() as cursor:
#             # CORREZIONE: Inserisce il valore di idDocente fornito nel form
#             sql = "INSERT INTO Docente (idDocente, Nome, Cognome, Email, Password, ruolo) VALUES (%s, %s, %s, %s, %s, 'docente')"
#             cursor.execute(sql, (id_docente, nome, cognome, email, password_hash))
#             conn.commit()
#             flash('Nuovo docente aggiunto con successo!', 'success')
#     except pymysql.IntegrityError:
#         flash('Errore: ID Docente o email già esistente.', 'danger')
#     except pymysql.Error as e:
#         flash(f"Errore durante l'inserimento del docente: {e}", 'danger')
#     finally:
#         if conn: conn.close()
            
#     return redirect(url_for('manager_bp.gestione_docenti'))


# @manager_bp.route('/cattedre/assegna', methods=['POST'])
# @manager_required
# def assegna_cattedra():
#     id_docente = request.form.get('docente_cattedra')
#     id_insegnamento = request.form.get('insegnamento_cattedra')
#     anno_accademico = request.form.get('anno_accademico')

#     if not all([id_docente, id_insegnamento, anno_accademico]):
#         flash('Tutti i campi per assegnare la cattedra sono obbligatori.', 'warning')
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     try:
#         with conn.cursor() as cursor:
#             sql = "INSERT INTO Cattedra (docente, insegnamento, anno_accademico) VALUES (%s, %s, %s)"
#             cursor.execute(sql, (id_docente, id_insegnamento, anno_accademico))
#             conn.commit()
#             flash('Cattedra assegnata con successo!', 'success')
#     except pymysql.IntegrityError:
#         flash('Errore: Questa cattedra è già stata assegnata.', 'danger')
#     except pymysql.Error as e:
#         flash(f"Errore durante l'assegnazione della cattedra: {e}", 'danger')
#     finally:
#         if conn: conn.close()

#     return redirect(url_for('manager_bp.gestione_docenti'))


# @manager_bp.route('/docenti/rimuovi', methods=['POST'])
# @manager_required
# def rimuovi_docente():
#     id_docente = request.form.get('docente_da_rimuovere')
#     if not id_docente:
#         flash('Selezionare un docente da rimuovere.', 'warning')
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return redirect(url_for('manager_bp.gestione_docenti'))
    
#     try:
#         with conn.cursor() as cursor:
#             # Prima rimuovi le dipendenze per evitare IntegrityError
#             cursor.execute("DELETE FROM Cattedra WHERE docente = %s", (id_docente,))
#             cursor.execute("DELETE FROM Docenza WHERE docente = %s", (id_docente,))
            
#             # Ora rimuovi il docente
#             cursor.execute("DELETE FROM Docente WHERE idDocente = %s", (id_docente,))
#             conn.commit()
#             flash('Docente e tutte le sue associazioni rimossi con successo.', 'success')
#     except pymysql.Error as e:
#         conn.rollback()
#         flash(f"Errore durante la rimozione del docente: {e}", 'danger')
#     finally:
#         if conn: conn.close()

#     return redirect(url_for('manager_bp.gestione_docenti'))


# @manager_bp.route('/cattedre/rimuovi', methods=['POST'])
# @manager_required
# def solleva_da_cattedra():
#     # Il valore del form è una stringa combinata: "idDocente_idInsegnamento_annoAccademico"
#     cattedra_key = request.form.get('cattedra_da_rimuovere')
#     if not cattedra_key:
#         flash('Selezionare una cattedra da cui sollevare il docente.', 'warning')
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     try:
#         id_docente, id_insegnamento, anno_accademico = cattedra_key.split('_')
#     except ValueError:
#         flash('Valore della cattedra non valido.', 'danger')
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return redirect(url_for('manager_bp.gestione_docenti'))
        
#     try:
#         with conn.cursor() as cursor:
#             sql = "DELETE FROM Cattedra WHERE docente = %s AND insegnamento = %s AND anno_accademico = %s"
#             cursor.execute(sql, (id_docente, id_insegnamento, anno_accademico))
#             conn.commit()
#             flash('Docente sollevato dalla cattedra con successo.', 'success')
#     except pymysql.Error as e:
#         conn.rollback()
#         flash(f"Errore durante la rimozione della cattedra: {e}", 'danger')
#     finally:
#         if conn: conn.close()

#     return redirect(url_for('manager_bp.gestione_docenti'))



# @manager_bp.route('/docenti/andamento', methods=['POST'])
# @manager_required
# def ricerca_andamento_docente():
#     """
#     Gestisce la ricerca dell'andamento di un docente per un insegnamento specifico.
#     """
#     id_docente = request.form.get('docente_andamento')
#     id_insegnamento = request.form.get('insegnamento_andamento')
#     anno_di_corso = request.form.get('anno_di_corso')

#     if not id_docente or not id_insegnamento:
#         flash('Selezionare un docente e un insegnamento per visualizzare l\'andamento.', 'warning')
#         return redirect(url_for('manager_bp.gestione_docenti'))

#     return redirect(url_for('manager_bp.gestione_docenti', 
#                             docente_andamento=id_docente, 
#                             insegnamento_andamento=id_insegnamento,
#                             anno_di_corso=anno_di_corso))

# # ==============================================================================
# # === FINE SEZIONE GESTIONE DOCENTI ============================================
# # ==============================================================================

# # --- API PER LA GESTIONE DINAMICA DEGLI STUDENTI ---

# @manager_bp.route('/api/insegnamenti_per_corso', methods=['GET'])
# @manager_required
# def api_get_insegnamenti_per_corso():
#     id_corso = request.args.get('id_corso')
#     anno = request.args.get('anno')
#     if not id_corso or not anno:
#         return jsonify({'error': 'Parametri mancanti'}), 400
#     conn = get_db_connection()
#     insegnamenti = []
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             # ### CORREZIONE QUI ###
#             # Aggiunto DISTINCT alla query per assicurarsi che ogni insegnamento
#             # venga restituito una sola volta per il corso e l'anno selezionati.
#             sql = """
#                 SELECT DISTINCT i.idInsegnamento, i.Nome 
#                 FROM PianoDiStudi pds
#                 JOIN Insegnamento i ON pds.insegnamento = i.idInsegnamento
#                 WHERE pds.corso = %s AND pds.anno_di_corso = %s 
#                 ORDER BY i.Nome
#             """
            
#             cursor.execute(sql, (id_corso, anno))
#             insegnamenti = cursor.fetchall()
#     except pymysql.Error as e:
#         print(f"Errore DB: {e}")
#         return jsonify({'error': 'Errore durante la ricerca'}), 500
#     finally:
#         if conn: conn.close()
#     return jsonify(insegnamenti)


# @manager_bp.route('/api/studenti/<string:matricola>', methods=['GET'])
# @manager_required
# def api_get_studente(matricola):
#     conn = get_db_connection()
#     studente_data = None
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             cursor.execute("SELECT Nome, Cognome FROM Studente WHERE matricola = %s", (matricola,))
#             studente = cursor.fetchone()

#             if studente:
#                 # ### FIX: Rimossa la virgola finale dopo 'isc.anno_accademico' ###
#                 sql_iscrizioni = """
#                     SELECT 
#                         i.idInsegnamento, 
#                         i.Nome,
#                         isc.corso as idCorso,
#                         isc.anno_di_corso,
#                         isc.anno_accademico
#                     FROM Iscrizione isc
#                     JOIN Insegnamento i ON isc.insegnamento = i.idInsegnamento
#                     WHERE isc.studente = %s
#                     ORDER BY i.Nome
#                 """
#                 cursor.execute(sql_iscrizioni, (matricola,))
#                 iscrizioni = cursor.fetchall()
                
#                 studente_data = {
#                     'nome': studente['Nome'],
#                     'cognome': studente['Cognome'],
#                     'iscrizioni': iscrizioni
#                 }
#             else:
#                  return jsonify({'error': 'Studente non trovato'}), 404
#     except pymysql.Error as e:
#         print(f"Errore DB: {e}")
#         return jsonify({'error': 'Errore del server'}), 500
#     finally:
#         if conn: conn.close()
#     return jsonify(studente_data)


# # La tua route esistente per l'iscrizione singola (invariata)
# @manager_bp.route('/api/studenti/iscrivi', methods=['POST'])
# @manager_required
# def api_iscrivi_studente():
#     data = request.get_json()
#     matricola = data.get('matricola')
#     nome = data.get('nome')
#     cognome = data.get('cognome')
#     id_insegnamento = data.get('id_insegnamento')
#     id_corso = data.get('id_corso')
#     anno_di_corso = data.get('anno_di_corso')
#     anno_accademico = data.get('anno_accademico')

#     if not all([matricola, nome, cognome, id_insegnamento, id_corso, anno_di_corso, anno_accademico]):
#         return jsonify({'error': 'Tutti i campi sono obbligatori'}), 400

#     conn = get_db_connection()
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             cursor.execute("""
#                 INSERT INTO Studente (matricola, Nome, Cognome) VALUES (%s, %s, %s)
#                 ON DUPLICATE KEY UPDATE Nome = VALUES(Nome), Cognome = VALUES(Cognome)
#             """, (matricola, nome, cognome))

#             cursor.execute("""
#                 INSERT INTO Iscrizione (studente, insegnamento, corso, anno_di_corso, anno_accademico) 
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico))
        
#         conn.commit()
#     except pymysql.err.IntegrityError:
#         conn.rollback()
#         return jsonify({'error': 'Questa iscrizione specifica (studente-insegnamento-anno accademico) esiste già.'}), 409
#     except pymysql.Error as e:
#         conn.rollback()
#         print(f"Errore DB: {e}")
#         return jsonify({'error': 'Errore durante la registrazione'}), 500
#     finally:
#         if conn: conn.close()

#     return jsonify({'success': True, 'message': 'Studente registrato e iscritto con successo'}), 201


# # ### NUOVA ROUTE: Per l'iscrizione massiva a tutti gli insegnamenti di un anno ###
# @manager_bp.route('/api/studenti/iscrivi_tutti', methods=['POST'])
# @manager_required
# def api_iscrivi_studente_tutti():
#     data = request.get_json()
#     matricola = data.get('matricola')
#     nome = data.get('nome')
#     cognome = data.get('cognome')
#     id_corso = data.get('id_corso')
#     anno_di_corso = data.get('anno_di_corso')
#     anno_accademico = data.get('anno_accademico')

#     if not all([matricola, nome, cognome, id_corso, anno_di_corso, anno_accademico]):
#         return jsonify({'error': 'Tutti i campi sono obbligatori'}), 400

#     conn = get_db_connection()
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             # 1. Registra o aggiorna i dati anagrafici dello studente
#             cursor.execute("""
#                 INSERT INTO Studente (matricola, Nome, Cognome) VALUES (%s, %s, %s)
#                 ON DUPLICATE KEY UPDATE Nome = VALUES(Nome), Cognome = VALUES(Cognome)
#             """, (matricola, nome, cognome))

#             # 2. Ottieni tutti gli insegnamenti per il corso e l'anno specificati
#             cursor.execute("""
#                 SELECT idInsegnamento FROM PianoDiStudi
#                 JOIN Insegnamento ON PianoDiStudi.insegnamento = Insegnamento.idInsegnamento
#                 WHERE PianoDiStudi.corso = %s AND PianoDiStudi.anno_di_corso = %s
#             """, (id_corso, anno_di_corso))
#             insegnamenti = cursor.fetchall()

#             if not insegnamenti:
#                 conn.rollback()
#                 return jsonify({'error': 'Nessun insegnamento trovato per il corso e anno specificati.'}), 404

#             # 3. Iscrivi lo studente a ciascun insegnamento, ignorando le iscrizioni già esistenti
#             iscritti_nuovi = 0
#             for insegnamento in insegnamenti:
#                 id_insegnamento = insegnamento['idInsegnamento']
#                 # INSERT IGNORE non restituisce errore se la riga esiste già, ma la salta.
#                 # Restituisce 1 se la riga è stata inserita, 0 se è stata ignorata.
#                 cursor.execute("""
#                     INSERT IGNORE INTO Iscrizione (studente, insegnamento, corso, anno_di_corso, anno_accademico) 
#                     VALUES (%s, %s, %s, %s, %s)
#                 """, (matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico))
#                 iscritti_nuovi += cursor.rowcount 
        
#         conn.commit()
#     except pymysql.Error as e:
#         conn.rollback()
#         print(f"Errore DB durante iscrizione massiva: {e}")
#         return jsonify({'error': 'Un errore interno ha impedito l\'iscrizione massiva.'}), 500
#     finally:
#         if conn: conn.close()

#     messaggio = f"Studente registrato/aggiornato. Effettuate {iscritti_nuovi} nuove iscrizioni su {len(insegnamenti)} insegnamenti totali."
#     return jsonify({'success': True, 'message': messaggio}), 201


# @manager_bp.route('/api/studenti/disiscrivi', methods=['POST'])
# @manager_required
# def api_disiscrivi_studente():
#     # ... (codice invariato)
#     data = request.get_json()
#     matricola = data.get('matricola')
#     id_insegnamento = data.get('id_insegnamento')
#     id_corso = data.get('id_corso')
#     anno_di_corso = data.get('anno_di_corso')
#     anno_accademico = data.get('anno_accademico')

#     if not all([matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico]):
#         return jsonify({'error': 'Dati mancanti per la disiscrizione'}), 400

#     conn = get_db_connection()
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             sql = """
#                 DELETE FROM Iscrizione 
#                 WHERE studente = %s AND insegnamento = %s AND corso = %s 
#                 AND anno_di_corso = %s AND anno_accademico = %s
#             """
#             result = cursor.execute(sql, (matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico))
#             if result == 0: 
#                 return jsonify({'warning': 'Iscrizione non trovata'}), 404

#         conn.commit()
#     except pymysql.Error as e:
#         conn.rollback()
#         print(f"Errore DB: {e}")
#         return jsonify({'error': 'Errore durante la disiscrizione'}), 500
#     finally:
#         if conn: conn.close()

#     return jsonify({'success': True, 'message': 'Studente disiscritto con successo'}), 200


# @manager_bp.route('/api/studenti/elimina', methods=['POST'])
# @manager_required
# def api_elimina_studente():
#     # ... (codice invariato)
#     data = request.get_json()
#     matricola = data.get('matricola')

#     if not matricola: return jsonify({'error': 'Matricola mancante'}), 400

#     conn = get_db_connection()
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             cursor.execute("DELETE FROM Presenza WHERE studente = %s", (matricola,))
#             cursor.execute("DELETE FROM Iscrizione WHERE studente = %s", (matricola,))
#             result = cursor.execute("DELETE FROM Studente WHERE matricola = %s", (matricola,))
#             if result == 0: return jsonify({'error': 'Studente non trovato'}), 404

#         conn.commit()
#     except pymysql.Error as e:
#         conn.rollback()
#         print(f"Errore DB: {e}")
#         return jsonify({'error': "Errore durante l'eliminazione"}), 500
#     finally:
#         if conn: conn.close()

#     return jsonify({'success': True, 'message': 'Studente eliminato con successo'}), 200


# @manager_bp.route('/api/studenti/<string:matricola>/presenze', methods=['GET'])
# @manager_required
# def api_get_presenze_studente(matricola):
#     """
#     Recupera le presenze di uno studente per ogni insegnamento a cui è iscritto.
#     La query è stata riscritta utilizzando un LEFT JOIN per garantire che tutte le
#     iscrizioni vengano mostrate, anche se non esiste un piano di studi corrispondente.
#     """
#     conn = get_db_connection()
#     presenze = []
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             cursor.execute("SELECT matricola FROM Studente WHERE matricola = %s", (matricola,))
#             if not cursor.fetchone():
#                 return jsonify({'error': 'Studente non trovato'}), 404

#             # ### QUERY CORRETTA CON LEFT JOIN ###
#             # Questo approccio garantisce che tutte le iscrizioni vengano restituite.
#             sql = """
#                 WITH PianoConAnno AS (
#                     SELECT 
#                         pds.insegnamento, pds.corso, pds.anno_di_corso,
#                         pds.data_inizio, pds.data_fine, pds.durata,
#                         CASE 
#                             WHEN MONTH(pds.data_inizio) >= 9 THEN CONCAT(YEAR(pds.data_inizio), '/', YEAR(pds.data_inizio) + 1)
#                             ELSE CONCAT(YEAR(pds.data_inizio) - 1, '/', YEAR(pds.data_inizio))
#                         END AS anno_accademico_calcolato
#                     FROM PianoDiStudi pds
#                 )
#                 SELECT 
#                     i.Nome AS nome_insegnamento,
#                     isc.anno_accademico,
#                     -- Se non c'è un piano di studi, le ore previste sono 0
#                     COALESCE(pds.durata, 0) AS ore_totali_previste,
#                     -- La subquery calcola le ore svolte solo se esiste un piano di studi
#                     COALESCE((
#                         SELECT SUM(TIME_TO_SEC(TIMEDIFF(l.ora_fine, l.ora_inizio))) / 3600
#                         FROM Presenza p
#                         JOIN Lezione l ON p.lezione = l.idLezione
#                         WHERE p.studente = isc.studente 
#                           AND l.insegnamento = isc.insegnamento
#                           AND DATE(l.ora_inizio) BETWEEN pds.data_inizio AND pds.data_fine
#                     ), 0) AS ore_svolte
#                 FROM Iscrizione isc
#                 JOIN Insegnamento i ON isc.insegnamento = i.idInsegnamento
#                 -- Utilizziamo LEFT JOIN per includere tutte le iscrizioni
#                 LEFT JOIN PianoConAnno pds ON isc.insegnamento = pds.insegnamento 
#                                            AND isc.corso = pds.corso 
#                                            AND isc.anno_di_corso = pds.anno_di_corso
#                                            AND isc.anno_accademico = pds.anno_accademico_calcolato
#                 WHERE isc.studente = %s
#                 ORDER BY isc.anno_accademico DESC, i.Nome;
#             """
#             cursor.execute(sql, (matricola,))
#             presenze = cursor.fetchall()

#     except pymysql.Error as e:
#         print(f"Errore DB in api_get_presenze_studente: {e}")
#         return jsonify({'error': 'Errore del server durante il recupero delle presenze'}), 500
#     finally:
#         if conn:
#             conn.close()

#     return jsonify(presenze)





# @manager_bp.route('/lezioni', methods=['GET', 'POST'])
# @manager_required
# def gestione_lezioni():
#     # ... (codice iniziale invariato)
#     conn = get_db_connection()
#     if not conn:
#         flash("Errore di connessione al database.", "danger")
#         return render_template('manager/lesson_management.html', insegnamenti=[])

#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             if request.method == 'POST':
#                 action = request.form.get('action')
                
#                 if action == 'add':
#                     # Recupera tutti i dati dal form, incluso il nuovo campo
#                     insegnamento = request.form['insegnamento']
#                     # NUOVO: Recupera l'anno di corso
#                     anno_di_corso = request.form['anno_di_corso']
#                     aula = request.form['aula']
#                     ora_inizio = request.form['ora_inizio']
#                     ora_fine = request.form['ora_fine']
                    
#                     try:
#                         # MODIFICATO: Aggiorna la query SQL per includere la nuova colonna
#                         sql = "INSERT INTO Lezione (insegnamento, anno_di_corso, aula, ora_inizio, ora_fine) VALUES (%s, %s, %s, %s, %s)"
#                         # MODIFICATO: Aggiungi il nuovo valore al tuple dei parametri
#                         cursor.execute(sql, (insegnamento, anno_di_corso, aula, ora_inizio, ora_fine))
#                         conn.commit()
#                         flash('Lezione aggiunta al calendario con successo!', 'success')
#                     except pymysql.Error as err:
#                         flash(f"Errore durante l'aggiunta della lezione: {err}", 'danger')
#                         conn.rollback()

#                 elif action == 'delete':
#                     id_lezione_da_eliminare = request.form.get('idLezioneDaEliminare')
#                     try:
#                         cursor.execute("DELETE FROM Lezione WHERE idLezione = %s", (id_lezione_da_eliminare,))
#                         conn.commit()
#                         flash('Lezione eliminata con successo!', 'success')
#                     except pymysql.Error as err:
#                         flash(f"Errore durante l'eliminazione: {err}", 'danger')
#                         conn.rollback()
                
#                 return redirect(url_for('manager_bp.gestione_lezioni'))

#             cursor.execute("SELECT idInsegnamento, Nome FROM Insegnamento ORDER BY Nome")
#             insegnamenti = cursor.fetchall()
            
#             return render_template('manager/lesson_management.html', insegnamenti=insegnamenti)
#     finally:
#         if conn:
#             conn.close()



# @manager_bp.route('/lezioni/api')
# @manager_required
# def lezioni_api():
#     # ... (codice invariato)
#     conn = get_db_connection()
#     if not conn:
#         return jsonify([])
        
#     try:
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
#             start_date = request.args.get('start')
#             end_date = request.args.get('end')

#             if not start_date or not end_date:
#                 return jsonify([])

#             query = """
#                 SELECT 
#                     L.idLezione AS id, I.Nome AS title,
#                     L.ora_inizio AS start, L.ora_fine AS end,
#                     L.aula AS extended_aula ,
#                     L.anno_di_corso AS course_year
#                 FROM Lezione L
#                 JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
#                 WHERE L.ora_inizio < %s AND L.ora_fine > %s
#             """
#             cursor.execute(query, (end_date, start_date))
#             lezioni = cursor.fetchall()

#             for lezione in lezioni:
#                 if lezione.get('start'):
#                     lezione['start'] = lezione['start'].isoformat()
#                 if lezione.get('end'):
#                     lezione['end'] = lezione['end'].isoformat()
            
#             return jsonify(lezioni)

#     except pymysql.Error as err:
#         print(f"Errore API Lezioni: {err}")
#         return jsonify({"error": "Errore interno del server"}), 500
#     finally:
#         if conn:
#             conn.close()























from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from datetime import date, datetime
import pymysql.cursors
from functools import wraps
from werkzeug.security import generate_password_hash

# Importa la funzione per la connessione dal modulo centralizzato
from database import get_db_connection

# --- CREAZIONE DEL BLUEPRINT PER IL MANAGER ---
manager_bp = Blueprint('manager_bp', __name__,
                       url_prefix='/manager',
                       template_folder='templates',
                       static_folder='static')

# --- DECORATOR PER LA PROTEZIONE DELLE ROTTE ---
def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'manager':
            flash("Accesso non autorizzato.", "danger")
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTTA PRINCIPALE PER LA DASHBOARD ---
@manager_bp.route('/dashboard')
@manager_required
def dashboard():
    return render_template('manager/manager_home.html')




# ==============================================================================
# === INIZIO SEZIONE GESTIONE INSEGNAMENTI =====================================
# ==============================================================================

@manager_bp.route('/insegnamenti', methods=['GET', 'POST'])
@manager_required
def gestione_insegnamenti():
    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return render_template('manager/teaching_management.html', insegnamenti=[], corsi=[])
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            if request.method == 'POST':
                action = request.form.get('action')
                if action == 'add':
                    # ... (logica di aggiunta invariata)
                    id_insegnamento = request.form['idInsegnamento']
                    nome_insegnamento = request.form['nome']
                    id_corso = request.form['corso']
                    anno_corso = request.form['annoCorso']
                    durata_ore = request.form['durataOre']
                    data_inizio = request.form['dataInizio']
                    data_fine = request.form['dataFine']

                    if not data_inizio or not data_fine:
                        flash("Le date di inizio e fine sono obbligatorie.", 'danger')
                    else:
                        try:
                            cursor.execute("INSERT INTO Insegnamento (idInsegnamento, Nome) VALUES (%s, %s) ON DUPLICATE KEY UPDATE Nome=VALUES(Nome)", 
                                           (id_insegnamento, nome_insegnamento))
                            
                            query_piano_studi = """
                                INSERT INTO PianoDiStudi (insegnamento, corso, anno_di_corso, durata, data_inizio, data_fine) 
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(query_piano_studi, (id_insegnamento, id_corso, anno_corso, durata_ore, data_inizio, data_fine))
                            
                            conn.commit()
                            flash('Insegnamento aggiunto al piano di studi con successo!', 'success')

                        except pymysql.err.IntegrityError:
                            flash('Questo insegnamento è già presente in questo piano di studi.', 'warning')
                            conn.rollback()
                        except pymysql.Error as err:
                            flash(f"Errore durante l'aggiunta: {err}", 'danger')
                            conn.rollback()

                elif action == 'delete':
                    # ... (logica di eliminazione invariata)
                    id_insegnamento_da_eliminare = request.form['id_insegnamento_da_eliminare']
                    id_corso_da_cui_eliminare = request.form['id_corso_da_cui_eliminare']
                    data_inizio = request.form['data_inizio']
                    data_fine = request.form['data_fine']
                    
                    try:
                        data_inizio_sql = datetime.strptime(data_inizio, '%d/%m/%Y').strftime('%Y-%m-%d')
                        data_fine_sql = datetime.strptime(data_fine, '%d/%m/%Y').strftime('%Y-%m-%d')

                        cursor.execute("DELETE FROM PianoDiStudi WHERE insegnamento = %s AND corso = %s AND data_inizio = %s AND data_fine = %s", 
                                       (id_insegnamento_da_eliminare, id_corso_da_cui_eliminare, data_inizio_sql, data_fine_sql))

                        cursor.execute("SELECT COUNT(*) AS count FROM PianoDiStudi WHERE insegnamento = %s", (id_insegnamento_da_eliminare,))
                        count_result = cursor.fetchone()
                        
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
            query_insegnamenti = """
                SELECT 
                    I.idInsegnamento, I.Nome AS nome_insegnamento,
                    C.idCorso, C.Nome AS nome_corso, C.Tipologia AS tipologia_corso,
                    P.anno_di_corso, P.durata, P.data_inizio, P.data_fine
                FROM PianoDiStudi P
                JOIN Insegnamento I ON P.insegnamento = I.idInsegnamento
                JOIN Corso C ON P.corso = C.idCorso
                ORDER BY C.Nome, I.Nome
            """
            cursor.execute(query_insegnamenti)
            lista_insegnamenti = cursor.fetchall()

            for ins in lista_insegnamenti:
                if ins.get('data_inizio') and isinstance(ins['data_inizio'], date):
                    ins['data_inizio'] = ins['data_inizio'].strftime('%d/%m/%Y')
                if ins.get('data_fine') and isinstance(ins['data_fine'], date):
                    ins['data_fine'] = ins['data_fine'].strftime('%d/%m/%Y')

            cursor.execute("SELECT idCorso, CONCAT(Nome, ' - ', Tipologia) AS nome_completo FROM Corso ORDER BY Nome")
            lista_corsi = cursor.fetchall()

            return render_template('manager/teaching_management.html', 
                                   insegnamenti=lista_insegnamenti, 
                                   corsi=lista_corsi)
    finally:
        if conn:
            conn.close()


# ==============================================================================
# === INIZIO SEZIONE GESTIONE STUDENTI  =========================================
# ==============================================================================


@manager_bp.route('/studenti')
@manager_required
def gestione_studenti():
    conn = get_db_connection()
    corsi = []
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT idCorso, CONCAT(Nome, ' - ', Tipologia) AS nome_completo FROM Corso ORDER BY Nome")
            corsi = cursor.fetchall()
    except pymysql.Error as e:
        flash(f"Errore del database: {e}", "danger")
    finally:
        if conn: conn.close()
    return render_template('manager/student_management.html', corsi=corsi)

# --- API PER LA GESTIONE DINAMICA DEGLI STUDENTI ---

@manager_bp.route('/api/insegnamenti_per_corso', methods=['GET'])
@manager_required
def api_get_insegnamenti_per_corso():
    id_corso = request.args.get('id_corso')
    anno = request.args.get('anno')
    if not id_corso or not anno:
        return jsonify({'error': 'Parametri mancanti'}), 400
    conn = get_db_connection()
    insegnamenti = []
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # ### CORREZIONE QUI ###
            # Aggiunto DISTINCT alla query per assicurarsi che ogni insegnamento
            # venga restituito una sola volta per il corso e l'anno selezionati.
            sql = """
                SELECT DISTINCT i.idInsegnamento, i.Nome 
                FROM PianoDiStudi pds
                JOIN Insegnamento i ON pds.insegnamento = i.idInsegnamento
                WHERE pds.corso = %s AND pds.anno_di_corso = %s 
                ORDER BY i.Nome
            """
            
            cursor.execute(sql, (id_corso, anno))
            insegnamenti = cursor.fetchall()
    except pymysql.Error as e:
        print(f"Errore DB: {e}")
        return jsonify({'error': 'Errore durante la ricerca'}), 500
    finally:
        if conn: conn.close()
    return jsonify(insegnamenti)


@manager_bp.route('/api/studenti/<string:matricola>', methods=['GET'])
@manager_required
def api_get_studente(matricola):
    conn = get_db_connection()
    studente_data = None
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT Nome, Cognome FROM Studente WHERE matricola = %s", (matricola,))
            studente = cursor.fetchone()

            if studente:
                # ### FIX: Rimossa la virgola finale dopo 'isc.anno_accademico' ###
                sql_iscrizioni = """
                    SELECT 
                        i.idInsegnamento, 
                        i.Nome,
                        isc.corso as idCorso,
                        isc.anno_di_corso,
                        isc.anno_accademico
                    FROM Iscrizione isc
                    JOIN Insegnamento i ON isc.insegnamento = i.idInsegnamento
                    WHERE isc.studente = %s
                    ORDER BY i.Nome
                """
                cursor.execute(sql_iscrizioni, (matricola,))
                iscrizioni = cursor.fetchall()
                
                studente_data = {
                    'nome': studente['Nome'],
                    'cognome': studente['Cognome'],
                    'iscrizioni': iscrizioni
                }
            else:
                 return jsonify({'error': 'Studente non trovato'}), 404
    except pymysql.Error as e:
        print(f"Errore DB: {e}")
        return jsonify({'error': 'Errore del server'}), 500
    finally:
        if conn: conn.close()
    return jsonify(studente_data)


# La tua route esistente per l'iscrizione singola (invariata)
@manager_bp.route('/api/studenti/iscrivi', methods=['POST'])
@manager_required
def api_iscrivi_studente():
    data = request.get_json()
    matricola = data.get('matricola')
    nome = data.get('nome')
    cognome = data.get('cognome')
    id_insegnamento = data.get('id_insegnamento')
    id_corso = data.get('id_corso')
    anno_di_corso = data.get('anno_di_corso')
    anno_accademico = data.get('anno_accademico')

    if not all([matricola, nome, cognome, id_insegnamento, id_corso, anno_di_corso, anno_accademico]):
        return jsonify({'error': 'Tutti i campi sono obbligatori'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                INSERT INTO Studente (matricola, Nome, Cognome) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE Nome = VALUES(Nome), Cognome = VALUES(Cognome)
            """, (matricola, nome, cognome))

            cursor.execute("""
                INSERT INTO Iscrizione (studente, insegnamento, corso, anno_di_corso, anno_accademico) 
                VALUES (%s, %s, %s, %s, %s)
            """, (matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico))
        
        conn.commit()
    except pymysql.err.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Questa iscrizione specifica (studente-insegnamento-anno accademico) esiste già.'}), 409
    except pymysql.Error as e:
        conn.rollback()
        print(f"Errore DB: {e}")
        return jsonify({'error': 'Errore durante la registrazione'}), 500
    finally:
        if conn: conn.close()

    return jsonify({'success': True, 'message': 'Studente registrato e iscritto con successo'}), 201


# ### NUOVA ROUTE: Per l'iscrizione massiva a tutti gli insegnamenti di un anno ###
@manager_bp.route('/api/studenti/iscrivi_tutti', methods=['POST'])
@manager_required
def api_iscrivi_studente_tutti():
    data = request.get_json()
    matricola = data.get('matricola')
    nome = data.get('nome')
    cognome = data.get('cognome')
    id_corso = data.get('id_corso')
    anno_di_corso = data.get('anno_di_corso')
    anno_accademico = data.get('anno_accademico')

    if not all([matricola, nome, cognome, id_corso, anno_di_corso, anno_accademico]):
        return jsonify({'error': 'Tutti i campi sono obbligatori'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Registra o aggiorna i dati anagrafici dello studente
            cursor.execute("""
                INSERT INTO Studente (matricola, Nome, Cognome) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE Nome = VALUES(Nome), Cognome = VALUES(Cognome)
            """, (matricola, nome, cognome))

            # 2. Ottieni tutti gli insegnamenti per il corso e l'anno specificati
            cursor.execute("""
                SELECT idInsegnamento FROM PianoDiStudi
                JOIN Insegnamento ON PianoDiStudi.insegnamento = Insegnamento.idInsegnamento
                WHERE PianoDiStudi.corso = %s AND PianoDiStudi.anno_di_corso = %s
            """, (id_corso, anno_di_corso))
            insegnamenti = cursor.fetchall()

            if not insegnamenti:
                conn.rollback()
                return jsonify({'error': 'Nessun insegnamento trovato per il corso e anno specificati.'}), 404

            # 3. Iscrivi lo studente a ciascun insegnamento, ignorando le iscrizioni già esistenti
            iscritti_nuovi = 0
            for insegnamento in insegnamenti:
                id_insegnamento = insegnamento['idInsegnamento']
                # INSERT IGNORE non restituisce errore se la riga esiste già, ma la salta.
                # Restituisce 1 se la riga è stata inserita, 0 se è stata ignorata.
                cursor.execute("""
                    INSERT IGNORE INTO Iscrizione (studente, insegnamento, corso, anno_di_corso, anno_accademico) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico))
                iscritti_nuovi += cursor.rowcount 
        
        conn.commit()
    except pymysql.Error as e:
        conn.rollback()
        print(f"Errore DB durante iscrizione massiva: {e}")
        return jsonify({'error': 'Un errore interno ha impedito l\'iscrizione massiva.'}), 500
    finally:
        if conn: conn.close()

    messaggio = f"Studente registrato/aggiornato. Effettuate {iscritti_nuovi} nuove iscrizioni su {len(insegnamenti)} insegnamenti totali."
    return jsonify({'success': True, 'message': messaggio}), 201


@manager_bp.route('/api/studenti/disiscrivi', methods=['POST'])
@manager_required
def api_disiscrivi_studente():
    # ... (codice invariato)
    data = request.get_json()
    matricola = data.get('matricola')
    id_insegnamento = data.get('id_insegnamento')
    id_corso = data.get('id_corso')
    anno_di_corso = data.get('anno_di_corso')
    anno_accademico = data.get('anno_accademico')

    if not all([matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico]):
        return jsonify({'error': 'Dati mancanti per la disiscrizione'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                DELETE FROM Iscrizione 
                WHERE studente = %s AND insegnamento = %s AND corso = %s 
                AND anno_di_corso = %s AND anno_accademico = %s
            """
            result = cursor.execute(sql, (matricola, id_insegnamento, id_corso, anno_di_corso, anno_accademico))
            if result == 0: 
                return jsonify({'warning': 'Iscrizione non trovata'}), 404

        conn.commit()
    except pymysql.Error as e:
        conn.rollback()
        print(f"Errore DB: {e}")
        return jsonify({'error': 'Errore durante la disiscrizione'}), 500
    finally:
        if conn: conn.close()

    return jsonify({'success': True, 'message': 'Studente disiscritto con successo'}), 200


@manager_bp.route('/api/studenti/elimina', methods=['POST'])
@manager_required
def api_elimina_studente():
    # ... (codice invariato)
    data = request.get_json()
    matricola = data.get('matricola')

    if not matricola: return jsonify({'error': 'Matricola mancante'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("DELETE FROM Presenza WHERE studente = %s", (matricola,))
            cursor.execute("DELETE FROM Iscrizione WHERE studente = %s", (matricola,))
            result = cursor.execute("DELETE FROM Studente WHERE matricola = %s", (matricola,))
            if result == 0: return jsonify({'error': 'Studente non trovato'}), 404

        conn.commit()
    except pymysql.Error as e:
        conn.rollback()
        print(f"Errore DB: {e}")
        return jsonify({'error': "Errore durante l'eliminazione"}), 500
    finally:
        if conn: conn.close()

    return jsonify({'success': True, 'message': 'Studente eliminato con successo'}), 200


@manager_bp.route('/api/studenti/<string:matricola>/presenze', methods=['GET'])
@manager_required
def api_get_presenze_studente(matricola):
    """
    Recupera le presenze di uno studente per ogni insegnamento a cui è iscritto.
    La query è stata riscritta utilizzando un LEFT JOIN per garantire che tutte le
    iscrizioni vengano mostrate, anche se non esiste un piano di studi corrispondente.
    """
    conn = get_db_connection()
    presenze = []
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT matricola FROM Studente WHERE matricola = %s", (matricola,))
            if not cursor.fetchone():
                return jsonify({'error': 'Studente non trovato'}), 404

            # ### QUERY CORRETTA CON LEFT JOIN ###
            # Questo approccio garantisce che tutte le iscrizioni vengano restituite.
            sql = """
                WITH PianoConAnno AS (
                    SELECT 
                        pds.insegnamento, pds.corso, pds.anno_di_corso,
                        pds.data_inizio, pds.data_fine, pds.durata,
                        CASE 
                            WHEN MONTH(pds.data_inizio) >= 9 THEN CONCAT(YEAR(pds.data_inizio), '/', YEAR(pds.data_inizio) + 1)
                            ELSE CONCAT(YEAR(pds.data_inizio) - 1, '/', YEAR(pds.data_inizio))
                        END AS anno_accademico_calcolato
                    FROM PianoDiStudi pds
                )
                SELECT 
                    i.Nome AS nome_insegnamento,
                    isc.anno_accademico,
                    -- Se non c'è un piano di studi, le ore previste sono 0
                    COALESCE(pds.durata, 0) AS ore_totali_previste,
                    -- La subquery calcola le ore svolte solo se esiste un piano di studi
                    COALESCE((
                        SELECT SUM(TIME_TO_SEC(TIMEDIFF(l.ora_fine, l.ora_inizio))) / 3600
                        FROM Presenza p
                        JOIN Lezione l ON p.lezione = l.idLezione
                        WHERE p.studente = isc.studente 
                          AND l.insegnamento = isc.insegnamento
                          AND DATE(l.ora_inizio) BETWEEN pds.data_inizio AND pds.data_fine
                    ), 0) AS ore_svolte
                FROM Iscrizione isc
                JOIN Insegnamento i ON isc.insegnamento = i.idInsegnamento
                -- Utilizziamo LEFT JOIN per includere tutte le iscrizioni
                LEFT JOIN PianoConAnno pds ON isc.insegnamento = pds.insegnamento 
                                           AND isc.corso = pds.corso 
                                           AND isc.anno_di_corso = pds.anno_di_corso
                                           AND isc.anno_accademico = pds.anno_accademico_calcolato
                WHERE isc.studente = %s
                ORDER BY isc.anno_accademico DESC, i.Nome;
            """
            cursor.execute(sql, (matricola,))
            presenze = cursor.fetchall()

    except pymysql.Error as e:
        print(f"Errore DB in api_get_presenze_studente: {e}")
        return jsonify({'error': 'Errore del server durante il recupero delle presenze'}), 500
    finally:
        if conn:
            conn.close()

    return jsonify(presenze)



# ==============================================================================
# === INIZIO SEZIONE GESTIONE DOCENTI  =========================================
# ==============================================================================

@manager_bp.route('/docenti', methods=['GET'])
@manager_required
def gestione_docenti():
    """
    Pagina Unica: Carica i dati per i form e gestisce la visualizzazione dell'andamento.
    """
    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return render_template('manager/teacher_management.html', docenti=[], insegnamenti=[], cattedre=[], risultati=None)

    docenti, insegnamenti, cattedre, risultati = [], [], [], None
    docente_selezionato, insegnamento_selezionato = None, None
    id_docente_corrente = request.args.get('docente_andamento', type=int)
    id_insegnamento_corrente = request.args.get('insegnamento_andamento', type=int)

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Recupera sempre tutti i docenti per i menu
            cursor.execute("SELECT idDocente, Nome, Cognome FROM Docente WHERE ruolo = 'docente' ORDER BY Cognome, Nome")
            docenti = cursor.fetchall()
            
            # 2. Recupera sempre tutti gli insegnamenti per i menu
            cursor.execute("SELECT idInsegnamento, Nome FROM Insegnamento ORDER BY Nome")
            insegnamenti = cursor.fetchall()

            # 3. Recupera le cattedre per il menu di rimozione (senza idCattedra)
            sql_cattedre = """
                SELECT D.idDocente, I.idInsegnamento, C.anno_accademico,
                       D.Nome AS NomeDocente, D.Cognome, I.Nome AS NomeInsegnamento
                FROM Cattedra C
                JOIN Docente D ON C.docente = D.idDocente
                JOIN Insegnamento I ON C.insegnamento = I.idInsegnamento
                ORDER BY D.Cognome, I.Nome
            """
            cursor.execute(sql_cattedre)
            cattedre = cursor.fetchall()

            # 4. Se è stata fatta una ricerca per l'andamento, esegui la query
            if id_docente_corrente and id_insegnamento_corrente:
                sql_andamento = """
                    SELECT DATE_FORMAT(L.ora_inizio, '%%d/%%m/%%Y') AS giorno_lezione, D.presenza, D.note
                    FROM Docenza D
                    JOIN Lezione L ON D.lezione = L.idLezione
                    WHERE D.docente = %s AND L.insegnamento = %s
                    ORDER BY L.ora_inizio DESC
                """
                cursor.execute(sql_andamento, (id_docente_corrente, id_insegnamento_corrente))
                risultati = cursor.fetchall()
                
                docente_selezionato = next((d for d in docenti if d['idDocente'] == id_docente_corrente), None)
                insegnamento_selezionato = next((i for i in insegnamenti if i['idInsegnamento'] == id_insegnamento_corrente), None)

    except pymysql.Error as e:
        flash(f"Errore nel recupero dei dati: {e}", 'danger')
    finally:
        if conn:
            conn.close()
            
    return render_template('manager/teacher_management.html', 
                           docenti=docenti, 
                           insegnamenti=insegnamenti, 
                           cattedre=cattedre,
                           risultati=risultati,
                           docente_selezionato=docente_selezionato,
                           insegnamento_selezionato=insegnamento_selezionato,
                           id_docente_corrente=id_docente_corrente,
                           id_insegnamento_corrente=id_insegnamento_corrente)

@manager_bp.route('/docenti/aggiungi', methods=['POST'])
@manager_required
def aggiungi_docente():
    # CORREZIONE: Legge 'idDocente' dal form invece di 'codice_docente'
    id_docente = request.form.get('idDocente')
    nome = request.form.get('nome')
    cognome = request.form.get('cognome')
    email = request.form.get('email')
    password = request.form.get('password')

    if not all([id_docente, nome, cognome, email, password]):
        flash('Tutti i campi sono obbligatori.', 'warning')
        return redirect(url_for('manager_bp.gestione_docenti'))

    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return redirect(url_for('manager_bp.gestione_docenti'))

    try:
        with conn.cursor() as cursor:
            # CORREZIONE: Inserisce il valore di idDocente fornito nel form
            sql = "INSERT INTO Docente (idDocente, Nome, Cognome, Email, Password, ruolo) VALUES (%s, %s, %s, %s, %s, 'docente')"
            cursor.execute(sql, (id_docente, nome, cognome, email, password_hash))
            conn.commit()
            flash('Nuovo docente aggiunto con successo!', 'success')
    except pymysql.IntegrityError:
        flash('Errore: ID Docente o email già esistente.', 'danger')
    except pymysql.Error as e:
        flash(f"Errore durante l'inserimento del docente: {e}", 'danger')
    finally:
        if conn: conn.close()
            
    return redirect(url_for('manager_bp.gestione_docenti'))


@manager_bp.route('/cattedre/assegna', methods=['POST'])
@manager_required
def assegna_cattedra():
    id_docente = request.form.get('docente_cattedra')
    id_insegnamento = request.form.get('insegnamento_cattedra')
    anno_accademico = request.form.get('anno_accademico')

    if not all([id_docente, id_insegnamento, anno_accademico]):
        flash('Tutti i campi per assegnare la cattedra sono obbligatori.', 'warning')
        return redirect(url_for('manager_bp.gestione_docenti'))

    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return redirect(url_for('manager_bp.gestione_docenti'))

    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO Cattedra (docente, insegnamento, anno_accademico) VALUES (%s, %s, %s)"
            cursor.execute(sql, (id_docente, id_insegnamento, anno_accademico))
            conn.commit()
            flash('Cattedra assegnata con successo!', 'success')
    except pymysql.IntegrityError:
        flash('Errore: Questa cattedra è già stata assegnata.', 'danger')
    except pymysql.Error as e:
        flash(f"Errore durante l'assegnazione della cattedra: {e}", 'danger')
    finally:
        if conn: conn.close()

    return redirect(url_for('manager_bp.gestione_docenti'))


@manager_bp.route('/docenti/rimuovi', methods=['POST'])
@manager_required
def rimuovi_docente():
    id_docente = request.form.get('docente_da_rimuovere')
    if not id_docente:
        flash('Selezionare un docente da rimuovere.', 'warning')
        return redirect(url_for('manager_bp.gestione_docenti'))

    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return redirect(url_for('manager_bp.gestione_docenti'))
    
    try:
        with conn.cursor() as cursor:
            # Prima rimuovi le dipendenze per evitare IntegrityError
            cursor.execute("DELETE FROM Cattedra WHERE docente = %s", (id_docente,))
            cursor.execute("DELETE FROM Docenza WHERE docente = %s", (id_docente,))
            
            # Ora rimuovi il docente
            cursor.execute("DELETE FROM Docente WHERE idDocente = %s", (id_docente,))
            conn.commit()
            flash('Docente e tutte le sue associazioni rimossi con successo.', 'success')
    except pymysql.Error as e:
        conn.rollback()
        flash(f"Errore durante la rimozione del docente: {e}", 'danger')
    finally:
        if conn: conn.close()

    return redirect(url_for('manager_bp.gestione_docenti'))


@manager_bp.route('/cattedre/rimuovi', methods=['POST'])
@manager_required
def solleva_da_cattedra():
    # Il valore del form è una stringa combinata: "idDocente_idInsegnamento_annoAccademico"
    cattedra_key = request.form.get('cattedra_da_rimuovere')
    if not cattedra_key:
        flash('Selezionare una cattedra da cui sollevare il docente.', 'warning')
        return redirect(url_for('manager_bp.gestione_docenti'))

    try:
        id_docente, id_insegnamento, anno_accademico = cattedra_key.split('_')
    except ValueError:
        flash('Valore della cattedra non valido.', 'danger')
        return redirect(url_for('manager_bp.gestione_docenti'))

    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return redirect(url_for('manager_bp.gestione_docenti'))
        
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM Cattedra WHERE docente = %s AND insegnamento = %s AND anno_accademico = %s"
            cursor.execute(sql, (id_docente, id_insegnamento, anno_accademico))
            conn.commit()
            flash('Docente sollevato dalla cattedra con successo.', 'success')
    except pymysql.Error as e:
        conn.rollback()
        flash(f"Errore durante la rimozione della cattedra: {e}", 'danger')
    finally:
        if conn: conn.close()

    return redirect(url_for('manager_bp.gestione_docenti'))



@manager_bp.route('/docenti/andamento', methods=['POST'])
@manager_required
def ricerca_andamento_docente():
    """
    Gestisce la ricerca dell'andamento di un docente per un insegnamento specifico.
    """
    id_docente = request.form.get('docente_andamento')
    id_insegnamento = request.form.get('insegnamento_andamento')
    anno_di_corso = request.form.get('anno_di_corso')

    if not id_docente or not id_insegnamento:
        flash('Selezionare un docente e un insegnamento per visualizzare l\'andamento.', 'warning')
        return redirect(url_for('manager_bp.gestione_docenti'))

    return redirect(url_for('manager_bp.gestione_docenti', 
                            docente_andamento=id_docente, 
                            insegnamento_andamento=id_insegnamento,
                            anno_di_corso=anno_di_corso))

# ==============================================================================
# === FINE SEZIONE GESTIONE DOCENTI ============================================
# ==============================================================================


# ==============================================================================
# === INIZIO SEZIONE GESTIONE LEZIONI  =========================================
# ==============================================================================


@manager_bp.route('/lezioni', methods=['GET', 'POST'])
@manager_required
def gestione_lezioni():
    # ... (codice iniziale invariato)
    conn = get_db_connection()
    if not conn:
        flash("Errore di connessione al database.", "danger")
        return render_template('manager/lesson_management.html', insegnamenti=[])

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            if request.method == 'POST':
                action = request.form.get('action')
                
                if action == 'add':
                    # Recupera tutti i dati dal form, incluso il nuovo campo
                    insegnamento = request.form['insegnamento']
                    # NUOVO: Recupera l'anno di corso
                    anno_di_corso = request.form['anno_di_corso']
                    aula = request.form['aula']
                    ora_inizio = request.form['ora_inizio']
                    ora_fine = request.form['ora_fine']
                    
                    try:
                        # MODIFICATO: Aggiorna la query SQL per includere la nuova colonna
                        sql = "INSERT INTO Lezione (insegnamento, anno_di_corso, aula, ora_inizio, ora_fine) VALUES (%s, %s, %s, %s, %s)"
                        # MODIFICATO: Aggiungi il nuovo valore al tuple dei parametri
                        cursor.execute(sql, (insegnamento, anno_di_corso, aula, ora_inizio, ora_fine))
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
                
                return redirect(url_for('manager_bp.gestione_lezioni'))

            cursor.execute("SELECT idInsegnamento, Nome FROM Insegnamento ORDER BY Nome")
            insegnamenti = cursor.fetchall()
            
            return render_template('manager/lesson_management.html', insegnamenti=insegnamenti)
    finally:
        if conn:
            conn.close()



@manager_bp.route('/lezioni/api')
@manager_required
def lezioni_api():
    # ... (codice invariato)
    conn = get_db_connection()
    if not conn:
        return jsonify([])
        
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            start_date = request.args.get('start')
            end_date = request.args.get('end')

            if not start_date or not end_date:
                return jsonify([])

            query = """
                SELECT 
                    L.idLezione AS id, I.Nome AS title,
                    L.ora_inizio AS start, L.ora_fine AS end,
                    L.aula AS extended_aula ,
                    L.anno_di_corso AS course_year
                FROM Lezione L
                JOIN Insegnamento I ON L.insegnamento = I.idInsegnamento
                WHERE L.ora_inizio < %s AND L.ora_fine > %s
            """
            cursor.execute(query, (end_date, start_date))
            lezioni = cursor.fetchall()

            for lezione in lezioni:
                if lezione.get('start'):
                    lezione['start'] = lezione['start'].isoformat()
                if lezione.get('end'):
                    lezione['end'] = lezione['end'].isoformat()
            
            return jsonify(lezioni)

    except pymysql.Error as err:
        print(f"Errore API Lezioni: {err}")
        return jsonify({"error": "Errore interno del server"}), 500
    finally:
        if conn:
            conn.close()
