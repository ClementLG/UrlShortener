# Utiliser une image Python officielle comme image de base
FROM python:3.9-slim-buster

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de l'application dans le conteneur
COPY ./app /app

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port sur lequel l'application s'exécutera
EXPOSE 5000

# Commande pour exécuter l'application
CMD ["flask", "run", "--host=0.0.0.0"]