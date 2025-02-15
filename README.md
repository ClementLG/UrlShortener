# UrlShortener

## Description du Projet

Ce projet est une application web simple et efficace pour raccourcir les URLs longues en URLs courtes, plus faciles à partager et à mémoriser.  L'application est construite avec Python et le framework Flask. Elle offre à la fois une interface web conviviale pour raccourcir les URLs et une API pour une intégration dans d'autres services ou applications.  

## Fonctionnalités Principales

*   **Raccourcissement d'URL :** Permet de transformer une URL longue en une URL courte et unique.
*   **Redirection :**  Les URLs courtes redirigent de manière transparente vers l'URL longue d'origine.
*   **Interface Web :** Interface utilisateur simple et intuitive pour raccourcir les URLs via un navigateur web. [Image of Exemple d'interface utilisateur simple pour un raccourcisseur d'URL]
*   **API (Application Programming Interface) :**  API RESTful permettant de raccourcir les URLs de manière programmatique.
*   **Sécurité DDOS :**  Protection contre les attaques DDOS basées sur la limitation du nombre de requêtes par adresse IP (avec `Flask-Limiter`).
*   **Base de données Open Source :** Utilisation de MongoDB, une base de données NoSQL orientée documents, pour stocker les correspondances URL courte -> URL longue.

## Technologies Utilisées

*   **Backend :**
    *   **Python 3.x**
    *   **Flask :**  Micro-framework web Python pour le backend et l'API.
    *   **Flask-Limiter :**  Pour la protection contre les DDOS et la limitation de débit.
    *   **Pymongo :**  Pilote Python officiel pour interagir avec MongoDB 
    *   **Base de données :**  **MongoDB** - Base de données NoSQL orientée documents. Choisi pour sa flexibilité, sa scalabilité horizontale et sa bonne performance avec des données non relationnelles, ce qui est adapté pour un raccourcisseur d'URL.

*   **Frontend (Interface Web) :**
    *   **HTML, CSS, JavaScript** (Simple - pas de framework frontend majeur prévu pour cette version de base, peut-être à ajouter plus tard).
*   **Autres outils :**
    *   **pip :**  Gestionnaire de paquets Python.
    *   **Git :**  Pour la gestion de version.

## Installation

Suivez ces étapes pour installer et exécuter l'application localement :

1.  **Cloner le dépôt GitHub :**
    ```bash
    git clone [URL_DE_VOTRE_REPO_GITHUB]
    cd [NOM_DU_DOSSIER_DU_PROJET]
    ```

2.  **Coming soon**
    ```bash
    XXXXX
    ```

## Utilisation

### Interface Web

1.  Ouvrez la page d'accueil de l'application dans votre navigateur web.
2.  Entrez l'URL longue que vous souhaitez raccourcir dans le champ prévu à cet effet.
3.  Cliquez sur le bouton "Raccourcir".
4.  L'application générera une URL courte et l'affichera. Vous pourrez copier cette URL courte et la partager.

### API

L'API fournit un endpoint pour raccourcir les URLs de manière programmatique.

**Endpoint :**  `/api/v1/urls`

**Méthode :** `POST`

**Format de la requête (JSON) :**

    ```json
    {
        "long_url": "URL_LONGUE_A_RACCOURCIR"
    }
    ```
**Exemple de requête avec curl :**

    ```bash
    curl XX

    ```
**Réponse (JSON) en cas de succès (code 201 Created) :**
XX

**Réponse (JSON) en cas d'erreur (par exemple, URL long_url manquante dans la requête - code 400 Bad Request) :**
XX
