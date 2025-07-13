# add_teacher.py
import pymysql.cursors
from werkzeug.security import generate_password_hash
import getpass # Per nascondere l'input della password

# --- CONFIGURAZIONE DATABASE MYSQL ---
# Usa la stessa configurazione dell'app Flask.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '23042005', # <--- CAMBIA CON LA TUA VERA PASSWORD MYSQL
    'db': 'registro_accademico'
}

def add_new_teacher(id, name, surname, email, password):
    """
    Aggiunge un nuovo docente al database con una password hashata.
    """
    # Genera l'hash della password
    password_hash = generate_password_hash(password)
    
    connection = None
    try:
        # Connettiti al database
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:

            # Esegui la query per inserire il nuovo docente
            sql = "INSERT INTO registro_accademico.Docente (idDocente, Nome, Cognome, Email, Password, Ruolo) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (id, name, surname, email, password_hash, 'manager'))

        # Conferma le modifiche
        connection.commit()
        
        print(f"✅ Docente '{name} {surname}' aggiunto con successo al database.")

    except pymysql.Error as e:
        print(f"❌ Errore durante l'operazione sul database: {e}")
        if connection:
            connection.rollback() # Annulla le modifiche in caso di errore
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    print("--- Inserimento nuovo docente ---")
    id = 2
    nome = "Mattia"
    cognome = "Pinna"
    email_addr = "mattia@pinna.it"
    # Usa getpass per non mostrare la password mentre viene digitata
    plain_password = "root"

    if nome and cognome and email_addr and plain_password:
        add_new_teacher(id, nome, cognome, email_addr, plain_password)
    else:
        print("Tutti i campi sono obbligatori. Operazione annullata.")