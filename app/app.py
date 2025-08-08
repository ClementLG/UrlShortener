
from flask import Flask, render_template, request, redirect, abort, g
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

# --- Basic App Configuration ---
app = Flask(__name__)
# Configure ProxyFix to trust headers from a proxy (e.g., Traefik).
# x_for=1 means we trust the first proxy in the chain.
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
)
app.config['DATABASE'] = 'urls.db'  # Database file name

# --- Rate Limiting Configuration ---
app.config['RATELIMIT_DEFAULT'] = "200/day;50/hour;10/minute"  # Default global limits
app.config['RATELIMIT_STRATEGY'] = 'moving-window'  # Algorithm
app.config['RATELIMIT_STORAGE_URL'] = "memory://"  # In-memory storage (resets on app restart)

# --- Logging Configuration ---
LOG_FILE = 'logs/app.log'  # Relative path to the log file
LOG_LEVEL = logging.INFO

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
        db = g._database = sqlite3.connect(app.config['DATABASE'])
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
        result = urlparse(url)
        return all([result.scheme, result.netloc])
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
    storage_uri=app.config['RATELIMIT_STORAGE_URL'],
    strategy=app.config['RATELIMIT_STRATEGY']
)


# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5/minute")  # Specific limit for this route
def index():
    """Main page to create short URLs."""
    if request.method == 'POST':
        long_url = request.form['long_url']
        duration = request.form.get('duration', '24h')  # Default to 24h

        if not is_valid_url(long_url):
            logger.warning(f"Invalid URL creation attempt - IP: {request.remote_addr} - URL: {long_url}")
            return render_template('index.html', error="Invalid URL.")

        expiration_date = calculate_expiration_date(duration)

        # Ensure the generated short code is unique
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
            f"URL created - IP: {request.remote_addr} - Long URL: {long_url} - Short URL: {short_url} - Expires: {expiration_date}")
        return render_template('index.html', short_url=short_url)

    return render_template('index.html')


@app.route('/<short_code>')
@limiter.limit("10/minute")  # Specific limit for this route
def redirect_to_long_url(short_code):
    """Redirects a short code to its corresponding long URL."""
    db = get_db()
    cur = db.execute('SELECT long_url, expiration_date FROM urls WHERE short_code = ?', [short_code])
    result = cur.fetchone()

    if result:
        long_url, expiration_date_str = result
        expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d %H:%M:%S.%f')

        if datetime.datetime.now() < expiration_date:
            logger.info(
                f"Redirecting short URL - IP: {request.remote_addr} - Short URL: {request.host_url}{short_code} - To: {long_url}")
            return redirect(long_url)
        else:
            # Clean up the specific expired URL
            db.execute('DELETE FROM urls WHERE short_code = ?', [short_code])
            db.commit()
            logger.warning(
                f"Attempted access to expired short URL - IP: {request.remote_addr} - Short URL: {request.host_url}{short_code}")
            abort(404, description="This link has expired.")
    else:
        abort(404)


# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    """Handles 404 Not Found errors."""
    logger.warning(f"Page not found (404) - IP: {request.remote_addr} - URL: {request.url}")
    description = e.description if e.description else "Page not found."
    return render_template('404.html', error_message=description), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handles 429 Too Many Requests errors."""
    logger.warning(f"Rate limit exceeded - IP: {request.remote_addr}")
    return render_template('429.html', limit=e.description), 429


