from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inizializziamo l'estensione qui, ma la colleghiamo all'app nel file app.py.
# Questo previene problemi di importazione circolare.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"], # Limiti generici per tutta l'app
    storage_uri="memory://" # Per produzioni più grandi, si può usare Redis
)
