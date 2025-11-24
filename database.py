import pymysql.cursors
from dbutils.pooled_db import PooledDB
import os
from dotenv import load_dotenv

load_dotenv()  # Caricare le variabili d'ambiente dal file .env

# Leggere le credenziali dalle variabili d'ambiente per maggiore sicurezza.
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

try:
    pool = PooledDB(
        creator=pymysql,      # Specificare la libreria database da utilizzare
        maxconnections=10,    # Impostare il numero massimo di connessioni consentite nel pool
        mincached=2,          # Mantenere un numero minimo di connessioni sempre pronte all'uso
        blocking=True,        # Attendere il rilascio di una connessione se il pool è momentaneamente pieno
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
except pymysql.Error as e:
    print(f"Errore critico: Impossibile creare il pool di connessioni al database. {e}")
    # In un'app reale, gestire questo errore in modo più robusto (es. log su file o retry).
    pool = None

def get_db_connection():
    if pool is None:
        # Sollevare un'eccezione esplicita se il pool non è stato inizializzato correttamente
        raise ConnectionError("Il pool di connessioni al database non è stato inizializzato.")
    
    # Restituire una connessione attiva prelevata dal pool
    return pool.connection()