# Raccourcisseur d'URL

Une application simple de raccourcissement d'URL construite avec Python, Flask, et SQLite.

## Fonctionnalités

*   Raccourcissement d'URL.
*   Expiration automatique des URL (configurable : 24h, 48h, 1 semaine).
*   Redirection vers l'URL longue.
*   Protection basique contre le DDoS (limitation du débit).
*   Logging des actions (création, accès, expiration, erreurs).

## Prérequis

*   Python 3.7+
*   Flask
*   Flask-Limiter
*   (Optionnel) Docker et Docker Compose

## Installation (sans Docker)

1.  **Cloner le dépôt :**
    ```bash
    git clone <URL_DU_DEPOS>
    cd <NOM_DU_DOSSIER>
    ```

2.  **Créer un environnement virtuel (recommandé) :**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate  # Windows
    ```

3.  **Installer les dépendances :**
    ```bash
    pip install Flask Flask-Limiter
    ```

4.  **Créer le dossier des logs**
    ```bash
    mkdir logs
    ```
5.  **Lancer l'application :**
    ```bash
    python app.py
    ```

    L'application sera accessible à l'adresse `http://IP_DE_VOTRE_HOST:5000`.

## Installation avec Docker

1.  **Installer Docker et Docker Compose.**
2.  **Cloner le dépôt.**
3.  **Construire et lancer l'application :**
    ```bash
    docker compose -d up
    ```
4.  **Accéder à l'application :**  `http://IP_DE_VOTRE_HOST:5000`

## Fichiers de configuration

*   `app.py` :  Code principal de l'application Flask.
*   `schema.sql` :  Schéma de la base de données SQLite.
*   `templates/` :  Templates HTML (index.html, 404.html, partials/logo.html, 429.html).
*   `static/` :  Fichiers statiques (style.css, images).
*   `Dockerfile` :  Instructions pour construire l'image Docker.
*   `docker-compose.yml` :  Configuration pour Docker Compose.
*   `logs/app.log`: Fichier de logs (créé automatiquement).
*   `url.db`: Base de donnée SQLite (créée automatiquement).

## Logs

Les logs sont enregistrés dans le fichier `logs/app.log`.  Ils incluent l'horodatage, l'adresse IP de l'utilisateur, l'URL (longue et courte, si applicable), et l'action effectuée. Les logs effectuent une rotation hebdomadaire, conservant les logs des 4 dernières semaines.

## Améliorations possibles

*   Authentification des utilisateurs.
*   Interface utilisateur pour gérer les URL raccourcies (modification, suppression, statistiques, traking).
*   API RESTful.
*   Utilisation d'une base de données plus robuste (PostgreSQL, MySQL) pour la production.
*   Tests unitaires.

## Architecture

```
url_shortener/        <-- Répertoire racine du projet
├── app.py            <-- Fichier principal de l'application Flask
├── schema.sql        <-- Schéma de la base de données SQLite
├── templates/        <-- Templates HTML
│   ├── index.html    <-- Page d'accueil (formulaire)
│   ├── 404.html      <-- Page d'erreur 404
│   └── partials/
│       └── logo.html  <-- Partial pour le logo (réutilisable)
├── static/           <-- Fichiers statiques (CSS, JS, images)
│   ├── style.css     <-- Fichier CSS personnalisé
│   └── images/
│       ├── favicon.ico <-- Favicon de l'application
│       └── logo.png    <-- (Optionnel) Image du logo
├── Dockerfile        <-- Instructions pour construire l'image Docker
├── docker-compose.yml <-- Fichier de configuration Docker Compose
├── logs/              <-- créez ce repertoire manuellement
│   └── app.log    <-- Fichier de log (créé dynamiquement)
├── venv/             <-- (Optionnel) Environnement virtuel
└── README.md         <-- Ce fichier

```