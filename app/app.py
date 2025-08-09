from flask import Flask, render_template, request, redirect, abort, g, jsonify
from flasgger import Swagger
import string
import random
import sqlite3
from urllib.parse import urlparse
import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import errno
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import config_by_name
from app.errors import errors_bp

# --- Basic App Configuration ---
app = Flask(__name__)
app.config.from_object(config_by_name[os.getenv('FLASK_ENV') or 'development'])
app.register_blueprint(errors_bp)

# --- Swagger Configuration ---
app.config['SWAGGER'] = {
    'title': 'URL Shortener API',
    'uiversion': 3,
    "specs_route": "/apidocs/"
}
swagger = Swagger(app)

# Configure ProxyFix to trust headers from a proxy (e.g., Traefik).
# x_for=1 means we trust the first proxy in the chain.
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
)

# --- Logging Configuration ---
LOG_FILE = app.config['LOG_FILE']
LOG_LEVEL = app.config['LOG_LEVEL']

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

# Create a handler for weekly log rotation
handler = TimedRotatingFileHandler(LOG_FILE, when="W0", backupCount=4)
handler.setLevel(LOG_LEVEL)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Create log directory if it doesn't exist
log_dir = os.path.dirname(LOG_FILE)
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.exception("Could not create log directory:")
            raise


# --- Database Management ---
def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE_URI'].replace('sqlite:///', ''))
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    print('Initialized the database.')


# --- URL Utilities ---
def generate_short_code(length=6):
    """Generate a random short code."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def is_valid_url(url):
    """Check if a URL is valid."""
    try:
        # After potentially adding a scheme, a simple check for a netloc is sufficient.
        result = urlparse(url)
        if not result.netloc:
            return False
        # This regex provides a much stronger validation for the domain structure.
        import re
        # This regex checks for a valid domain name, allowing for subdomains.
        # It ensures that parts of the domain are separated by dots,
        # and the TLD is at least two characters long. It disallows invalid characters.
        pattern = re.compile(
            r'^(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$',
            re.IGNORECASE)
        return re.match(pattern, result.netloc) is not None
    except ValueError:
        return False


def calculate_expiration_date(duration):
    """Calculate the expiration date based on the selected duration."""
    now = datetime.datetime.now()
    if duration == '24h':
        return now + datetime.timedelta(hours=24)
    elif duration == '48h':
        return now + datetime.timedelta(hours=48)
    elif duration == '1w':
        return now + datetime.timedelta(weeks=1)
    else:  # Default to 24h for security
        return now + datetime.timedelta(hours=24)


def cleanup_expired_urls():
    """Remove expired URLs from the database."""
    db = get_db()
    db.execute('DELETE FROM urls WHERE expiration_date < ?', [datetime.datetime.now()])
    db.commit()


# --- Rate Limiter Initialization ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[app.config['RATELIMIT_DEFAULT']],
    storage_uri=app.config['RATELIMIT_STORAGE_URL'],
    strategy=app.config['RATELIMIT_STRATEGY']
)


# --- Routes ---
@app.route('/', methods=['GET'])
def index():
    """
    Main page to create short URLs.
    ---
    get:
      summary: Display the URL shortening form
      responses:
        200:
          description: The HTML form for creating short URLs.
    """
    return render_template('index.html')


@app.route('/<short_code>')
@limiter.limit(app.config['RATELIMIT_REDIRECT'])
def redirect_to_long_url(short_code):
    """
    Redirects a short code to its corresponding long URL.
    ---
    get:
      summary: Redirect to the original URL
      parameters:
        - in: path
          name: short_code
          type: string
          required: true
          description: The short code to redirect.
      responses:
        302:
          description: Redirects to the long URL.
        404:
          description: The short code is not found or has expired.
    """
    db = get_db()
    cur = db.execute('SELECT long_url, expiration_date, clicks, uses_limit FROM urls WHERE short_code = ?', [short_code])
    result = cur.fetchone()

    if result:
        long_url, expiration_date_str, clicks, uses_limit = result
        expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d %H:%M:%S.%f')

        if datetime.datetime.now() >= expiration_date:
            db.execute('DELETE FROM urls WHERE short_code = ?', [short_code])
            db.commit()
            logger.warning(
                f"Attempted access to expired short URL - IP: {request.remote_addr} - Short URL: {request.host_url}{short_code}")
            abort(404, description="This link has expired.")
            return

        if uses_limit is not None and clicks >= uses_limit:
            logger.warning(
                f"Attempted access to depleted short URL - IP: {request.remote_addr} - Short URL: {request.host_url}{short_code}")
            abort(404, description="This link has reached its usage limit.")
            return

        db.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', [short_code])
        db.commit()
        logger.info(
            f"Redirecting short URL - IP: {request.remote_addr} - Short URL: {request.host_url}{short_code} - To: {long_url}")
        return redirect(long_url)
    else:
        abort(404)


@app.route('/stats/<short_code>')
def url_stats(short_code):
    """
    Display statistics for a short URL.
    """
    db = get_db()
    cur = db.execute('SELECT long_url, expiration_date, clicks, uses_limit FROM urls WHERE short_code = ?', [short_code])
    result = cur.fetchone()

    if result:
        long_url, expiration_date_str, clicks, uses_limit = result
        url_data = {
            'short_code': short_code,
            'long_url': long_url,
            'expiration_date': expiration_date_str,
            'clicks': clicks,
            'uses_limit': uses_limit,
            'remaining_uses': uses_limit - clicks if uses_limit is not None else 'Unlimited'
        }
        return render_template('stats.html', url_data=url_data)
    else:
        abort(404)


@app.route('/api/urls', methods=['POST'])
@limiter.limit(app.config['RATELIMIT_API'])
def create_short_url():
    """
    Create a new short URL
    ---
    post:
      summary: Create a new short URL
      consumes:
        - application/json
      produces:
        - application/json
      parameters:
        - in: body
          name: body
          required: true
          schema:
            type: object
            required:
              - long_url
            properties:
              long_url:
                type: string
                description: The original long URL to shorten.
              duration:
                type: string
                enum: ['24h', '48h', '1w']
                default: '24h'
                description: The duration for which the short URL will be valid.
              uses_limit:
                type: integer
                description: The maximum number of times the short URL can be used.
      responses:
        201:
          description: Short URL created successfully.
          schema:
            type: object
            properties:
              short_url:
                type: string
                description: The generated short URL.
        400:
          description: Invalid URL provided.
    """
    # Trigger cleanup with a 10% probability
    if random.random() < 0.1:
        cleanup_expired_urls()

    data = request.get_json()
    if not data or 'long_url' not in data:
        abort(400, description="The 'long_url' parameter is required.")

    long_url = data['long_url']
    duration = data.get('duration', '24h')
    uses_limit = data.get('uses_limit')

    if uses_limit is not None:
        try:
            uses_limit = int(uses_limit)
            if uses_limit <= 0:
                abort(400, description="The 'uses_limit' must be a positive integer.")
        except (ValueError, TypeError):
            abort(400, description="The 'uses_limit' must be a valid integer.")

    # Automatically add https:// if no scheme is present
    if not urlparse(long_url).scheme:
        long_url = 'https://' + long_url

    if not is_valid_url(long_url):
        logger.warning(f"Invalid URL creation attempt - IP: {request.remote_addr} - URL: {long_url}")
        abort(400, description="The provided URL is not valid.")

    expiration_date = calculate_expiration_date(duration)

    while True:
        short_code = generate_short_code()
        db = get_db()
        cur = db.execute('SELECT 1 FROM urls WHERE short_code = ?', [short_code])
        if cur.fetchone() is None:
            break

    db.execute('INSERT INTO urls (short_code, long_url, expiration_date, uses_limit) VALUES (?, ?, ?, ?)',
               [short_code, long_url, expiration_date, uses_limit])
    db.commit()
    short_url = request.host_url + short_code
    logger.info(
        f"URL created - IP: {request.remote_addr} - Long URL: {long_url} - Short URL: {short_url} - Expires: {expiration_date} - Uses Limit: {uses_limit or 'None'}")
    return jsonify({'short_url': short_url}), 201


# --- Routes de test pour les erreurs ---
@app.route('/test/error/<int:error_code>')
def test_error(error_code):
    """
    Route de test pour déclencher des erreurs HTTP.
    Utilisez /test/error/400, /test/error/404, /test/error/429, /test/error/500
    """
    if error_code == 400:
        abort(400, description="Ceci est un test de page 400 (Bad Request).")
    elif error_code == 404:
        abort(404, description="Ceci est un test de page 404 (Not Found).")
    elif error_code == 429:
        abort(429, description="100 per minute")  # La description simule la limite de taux
    elif error_code == 500:
        # Simule une erreur interne en divisant par zéro
        result = 1 / 0
    else:
        return "Code d'erreur non valide pour le test.", 400

# The error handlers are now in app/errors.py
