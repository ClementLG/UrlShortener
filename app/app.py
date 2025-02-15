from flask import Flask, render_template, request, redirect, abort
import string
import random
from urllib.parse import urlparse

app = Flask(__name__)

# Dictionnaire pour stocker les mappages d'URL (pourrait être remplacé par une base de données)
url_mapping = {}

def generate_short_code(length=6):
    """Génère un code court aléatoire de la longueur donnée."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def is_valid_url(url):
    """Vérification de base de la validité d'une URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False



@app.route('/', methods=['GET', 'POST'])
def index():
    """Page d'accueil: affiche le formulaire et l'URL raccourcie (si disponible)."""
    if request.method == 'POST':
        long_url = request.form['long_url']

        if not is_valid_url(long_url):
            return render_template('index.html', error="URL invalide. Veuillez vous assurer d'inclure le schéma (par exemple, http:// ou https://).")

        # Générer un code court unique
        while True:
            short_code = generate_short_code()
            if short_code not in url_mapping:
                break

        url_mapping[short_code] = long_url
        short_url = request.host_url + short_code  # Créer l'URL raccourcie complète

        return render_template('index.html', short_url=short_url)

    return render_template('index.html')



@app.route('/<short_code>')
def redirect_to_long_url(short_code):
    """Redirige du code court vers l'URL longue d'origine."""
    if short_code in url_mapping:
        long_url = url_mapping[short_code]
        return redirect(long_url)  # Redirection cruciale !
    else:
        abort(404) # Page non trouvée si le code n'existe pas


@app.errorhandler(404)
def page_not_found(e):
    """Gérer les erreurs 404 (page non trouvée)."""
    return render_template('404.html'), 404



if __name__ == '__main__':
    app.run(debug=True)  # debug=True pour le développement