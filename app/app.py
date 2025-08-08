
from flask import Flask, render_template, request, redirect, abort, g
import string
import random
import sqlite3  # Utilisation de SQLite (plus de dictionnaire !)
from urllib.parse import urlparse
import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging  # Importez le module logging
from logging.handlers import TimedRotatingFileHandler  # et TimedRotatingFileHandler
import os
import errno
from werkzeug.middleware.proxy_fix import ProxyFix

# Basic config
app = Flask(__name__)
# Le nombre de proxys devant l'application.
# 1 pour un seul proxy (ex: Traefik seul).
# 2 pour une configuration courante (ex: Load Balancer -> Traefik).
# Ajustez cette valeur via la variable d'environnement PROXIES_COUNT si votre infrastructure change.
proxies_count = int(os.environ.get('PROXIES_COUNT', 2))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies_count, x_proto=1, x_host=1, x_prefix=1)
app.config['DATABASE'] = 'urls.db'  # Nom du fichier de la base de donnees
# Configuration de Flask-Limiter
app.config['RATELIMIT_DEFAULT'] = "200/day;50/hour;10/minute"  # Limites globales par defaut
app.config['RATELIMIT_STRATEGY'] = 'moving-window'  # Algorithme
app.config[
    'RATELIMIT_STORAGE_URL'] = "memory://"  # Stockage en memoire (simple, mais redemarre a zero si l'app redemarre)

# Configuration du logging
LOG_FILE = 'logs/app.log'  # Chemin RELATIF vers le fichier de log (dans un dossier 'logs')
LOG_LEVEL = logging.INFO

# Creer un logger
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# Creer un handler pour la rotation des logs (hebdomadaire)
handler = TimedRotatingFileHandler(LOG_FILE, when="W0", backupCount=4)
handler.setLevel(LOG_LEVEL)

# Creer un formateur
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Ajouter le handler au logger
logger.addHandler(handler)

# Creer le repertoire de logs s'il n'existe pas
log_dir = os.path.dirname(LOG_FILE)  # Extrait le repertoire du chemin du fichier
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)  # Cree le repertoire (et les repertoires parents si necessaire)
    except OSError as e:
        if e.errno != errno.EEXIST:  # Leve l'exception si ce n'est pas une erreur "le dossier existe deja"
            logger.exception("Impossible de creer le repertoire de logs :")  # Log l'erreur complete
            raise  # et relance l'exception


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db


@app.cli.command('init-db')
def init_db():
    """Clear existing data and create new tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    print('Initialized the database.')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def calculate_expiration_date(duration):
    """Calcule la date d'expiration en fonction de la duree."""
    now = datetime.datetime.now()
    if duration == '24h':
        return now + datetime.timedelta(seconds=15)
    elif duration == '48h':
        return now + datetime.timedelta(hours=48)
    elif duration == '1w':
        return now + datetime.timedelta(weeks=1)
    else:  # Valeur par defaut (24h) - important pour la securite
        return now + datetime.timedelta(seconds=15)


def cleanup_expired_urls():
    """Supprime les URL expirees de la base de donnees."""
    db = get_db()
    db.execute('DELETE FROM urls WHERE expiration_date < ?', [datetime.datetime.now()])
    db.commit()


limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=app.config['RATELIMIT_STORAGE_URL'],
    strategy=app.config['RATELIMIT_STRATEGY']
)


@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5/minute")  # Limite specifique pour cette route
def index():
    if request.method == 'POST':
        long_url = request.form['long_url']
        duration = request.form.get('duration', '24h')  # Reupere la duree, 24h par defaut

        if not is_valid_url(long_url):
            logger.warning(f"Tentative de creation d'URL invalide - IP: {request.remote_addr} - URL: {long_url}")
            return render_template('index.html', error="URL invalide.")

        expiration_date = calculate_expiration_date(duration)

        while True:
            short_code = generate_short_code()
            db = get_db()
            cur = db.execute('SELECT 1 FROM urls WHERE short_code = ?', [short_code])
            if cur.fetchone() is None:
                break

        db.execute('INSERT INTO urls (short_code, long_url, expiration_date) VALUES (?, ?, ?)',
                   [short_code, long_url, expiration_date])
        db.commit()
        short_url = request.host_url + short_code
        logger.info(
            f"URL creee - IP: {request.remote_addr} - URL longue: {long_url} - URL courte: {short_url} - Expiration: {expiration_date}")
        return render_template('index.html', short_url=short_url)

    # logger.info(f"Accès a la page d'accueil - IP: {get_remote_IP()}")
    return render_template('index.html')


@app.route('/<short_code>')
@limiter.limit("10/minute")  # Limite specifique
def redirect_to_long_url(short_code):
    db = get_db()
    cur = db.execute('SELECT long_url, expiration_date FROM urls WHERE short_code = ?', [short_code])
    result = cur.fetchone()

    if result:
        long_url, expiration_date_str = result
        expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d %H:%M:%S.%f')

        if datetime.datetime.now() < expiration_date:
            logger.info(
                f"Acces a l'URL courte - IP: {request.remote_addr} - URL courte: {request.host_url}{short_code} - Redirection vers: {long_url}")
            return redirect(long_url)
        else:
            cleanup_expired_urls()
            logger.warning(
                f"Acces a l'URL courte expiree - IP: {request.remote_addr} - URL courte: {request.host_url}{short_code}")
            abort(404, description="Ce lien a expire.")  # Message d'erreur plus explicite
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"Page non trouvee - IP: {request.remote_addr} - URL demandee: {request.url}")
    return render_template('404.html', error_message=e.description), 404


@app.errorhandler(429)  # Gerer le code d'erreur 429 (Too Many Requests)
def ratelimit_handler(e):
    logger.warning(f"Limite de requetes atteinte - IP: {request.remote_addr}")
    return render_template('429.html', limit=e.description), 429


