from flask import Flask, render_template, request, redirect, abort, g
import string
import random
import sqlite3  # Utilisation de SQLite (plus de dictionnaire !)
from urllib.parse import urlparse
import datetime

app = Flask(__name__)
app.config['DATABASE'] = 'urls.db'  # Nom du fichier de la base de données


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db


def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:  # Utilisation du chemin relatif correct
            db.cursor().executescript(f.read())
        db.commit()


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
    """Calcule la date d'expiration en fonction de la durée."""
    now = datetime.datetime.now()
    if duration == '24h':
        return now + datetime.timedelta(seconds=15)
    elif duration == '48h':
        return now + datetime.timedelta(hours=48)
    elif duration == '1w':
        return now + datetime.timedelta(weeks=1)
    else:  # Valeur par défaut (24h) - important pour la sécurité
        return now + datetime.timedelta(seconds=15)


def cleanup_expired_urls():
    """Supprime les URL expirées de la base de données."""
    db = get_db()
    db.execute('DELETE FROM urls WHERE expiration_date < ?', [datetime.datetime.now()])
    db.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        long_url = request.form['long_url']
        duration = request.form.get('duration', '24h')  # Récupère la durée, 24h par défaut

        if not is_valid_url(long_url):
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
        return render_template('index.html', short_url=short_url)

    return render_template('index.html')


@app.route('/<short_code>')
def redirect_to_long_url(short_code):
    db = get_db()
    cur = db.execute('SELECT long_url, expiration_date FROM urls WHERE short_code = ?', [short_code])
    result = cur.fetchone()

    if result:
        long_url, expiration_date_str = result
        expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d %H:%M:%S.%f')

        if datetime.datetime.now() < expiration_date:
            return redirect(long_url)
        else:
            # Optionnel: Supprimer l'URL expirée ici (pour éviter le "nettoyage" séparé)
            #db.execute('DELETE FROM urls WHERE short_code = ?', [short_code])
            #db.commit()
            cleanup_expired_urls()
            abort(404, description="Ce lien a expiré.")  # Message d'erreur plus explicite
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error_message=e.description), 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
