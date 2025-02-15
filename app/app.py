from flask import Flask, render_template, request, redirect, abort, g
import string
import random
import sqlite3  # Utilisation de SQLite (plus de dictionnaire !)
from urllib.parse import urlparse

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        long_url = request.form['long_url']

        if not is_valid_url(long_url):
            return render_template('index.html', error="URL invalide. Veuillez inclure le schéma (http:// ou https://).")

        while True:
            short_code = generate_short_code()
            db = get_db()
            cur = db.execute('SELECT 1 FROM urls WHERE short_code = ?', [short_code])
            if cur.fetchone() is None:  # Vérification d'unicité *correcte*
                break

        db.execute('INSERT INTO urls (short_code, long_url) VALUES (?, ?)', [short_code, long_url])
        db.commit()
        short_url = request.host_url + short_code
        return render_template('index.html', short_url=short_url)

    return render_template('index.html')

@app.route('/<short_code>')
def redirect_to_long_url(short_code):
    db = get_db()
    cur = db.execute('SELECT long_url FROM urls WHERE short_code = ?', [short_code])
    result = cur.fetchone()
    if result:
        long_url = result[0]
        return redirect(long_url)
    else:
        abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)