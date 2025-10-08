import pymysql.cursors
from dbutils.pooled_db import PooledDB
import os
from dotenv import load_dotenv

load_dotenv()  # Carica le variabili d'ambiente dal file .env

# Legge le credenziali dalle variabili d'ambiente per maggiore sicurezza.
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

try:
    pool = PooledDB(
        creator=pymysql,      # La libreria da usare
        maxconnections=10,    # Numero massimo di connessioni nel pool
        mincached=2,          # Numero minimo di connessioni da tenere pronte
        blocking=True,        # Attende se non ci sono connessioni disponibili
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
except pymysql.Error as e:
    print(f"Errore critico: Impossibile creare il pool di connessioni al database. {e}")
    # In un'app reale, questo errore dovrebbe essere gestito in modo più robusto.
    pool = None

def get_db_connection():
    """
    Recupera una connessione dal pool.
    Questa funzione sostituisce la vecchia implementazione.
    """
    if pool is None:
        raise ConnectionError("Il pool di connessioni al database non è stato inizializzato.")
    return pool.connection()
