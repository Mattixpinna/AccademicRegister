# from flask import Flask, render_template
# from flask_cors import CORS
# import os

# # Blueprints from different modules
# from auth_routes import auth_bp
# from teacher_routes import teacher_bp
# from manager_routes import manager_bp

# def create_app():
#     app = Flask(__name__, template_folder='templates', static_folder='static')
    
#     CORS(app)
#     app.config['SECRET_KEY'] = os.urandom(24)

#     # Register blueprints
#     app.register_blueprint(auth_bp)
#     app.register_blueprint(teacher_bp)
#     app.register_blueprint(manager_bp)

#     # Define a simple route for the home page
#     @app.route('/')
#     def home():
#         return render_template('home.html')

#     return app

# # This block is executed only when you run the script directly
# if __name__ == '__main__':
#     app = create_app()
#     app.run(debug=True, port=5000)






from flask import Flask, render_template
from flask_cors import CORS
import os

# 1. Importa le estensioni e i blueprint
from extensions import limiter
from auth_routes import auth_bp
from teacher_routes import teacher_bp
from manager_routes import manager_bp
from database import pool # Importa il pool per chiuderlo correttamente

def create_app():
    """
    Application Factory: crea e configura l'istanza dell'applicazione Flask.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # --- CONFIGURAZIONE DI SICUREZZA ---

    # SECRET_KEY persistente
    secret = os.environ.get('SECRET_KEY')
    if not secret:
        # Per lo sviluppo, possiamo usare una chiave fissa se non impostata,
        # ma stampiamo un avviso. In produzione, la variabile DEVE essere impostata.
        print("ATTENZIONE: La variabile d'ambiente SECRET_KEY non è impostata. Si sta usando una chiave di sviluppo non sicura.")
        app.config['SECRET_KEY'] = 'chiave-di-sviluppo-non-sicura-cambiami'
    else:
        app.config['SECRET_KEY'] = secret

    # Configurazione CORS
    # In sviluppo, '*' è accettabile. In produzione, specifica i domini.
    CORS(app, origins="*", supports_credentials=True)

    # 2. Inizializza le estensioni con l'app
    limiter.init_app(app)

    # --- REGISTRAZIONE DEI BLUEPRINT ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(manager_bp)

    # --- ROTTE PRINCIPALI ---
    @app.route('/')
    def home():
        return render_template('home.html')
        
    # --- GESTIONE DELLA CHIUSURA ---
    # Aggiunge un hook per chiudere il pool di connessioni quando l'app si ferma
    @app.teardown_appcontext
    def close_db_pool(exception=None):
        if pool:
            pool.close()

    return app

# Questo blocco è solo per lo sviluppo locale
if __name__ == '__main__':
    app = create_app()
    # Esegui con debug=False anche in sviluppo per testare il comportamento di produzione
    # Il reload automatico è comunque attivo con `flask run` o `gunicorn --reload`
    app.run(host='0.0.0.0', port=5001, debug=False)