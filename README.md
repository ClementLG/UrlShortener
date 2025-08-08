# URL Shortener

A simple URL shortener application built with Python, Flask, and SQLite.

## Features

*   URL shortening.
*   Automatic URL expiration (configurable: 24h, 48h, 1 week).
*   Redirection to the long URL.
*   Basic DDoS protection (rate limiting).
*   Action logging (creation, access, expiration, errors).

## Prerequisites

*   Python 3.7+
*   Flask
*   Flask-Limiter
*   (Optional) Docker and Docker Compose

## Installation (without Docker)

1.  **Clone the repository:**
    ```bash
    git clone <REPO_URL>
    cd <FOLDER_NAME>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate  # Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r app/requirements.txt
    ```

4.  **Create the logs directory:**
    ```bash
    mkdir logs
    ```
5.  **Initialize the database:**
    ```bash
    flask init-db
    ```
6.  **Run the application:**
    ```bash
    flask run
    ```

    The application will be accessible at `http://127.0.0.1:5000`.

## Installation with Docker

1.  **Install Docker and Docker Compose.**
2.  **Clone the repository.**
3.  **Build and run the application:**
    ```bash
    docker-compose up -d --build
    ```
4.  **Access the application:** `http://<YOUR_HOST_IP>:5000` (You might need to uncomment the port mapping in `docker-compose.yml`)

## Configuration Files

*   `app/app.py`: Main Flask application code.
*   `app/schema.sql`: SQLite database schema.
*   `app/templates/`: HTML templates (index.html, 404.html, 429.html, partials/logo.html).
*   `app/static/`: Static files (style.css, images).
*   `Dockerfile`: Instructions for building the Docker image.
*   `docker-compose.yml`: Configuration for Docker Compose.
*   `logs/app.log`: Log file (created automatically).
*   `urls.db`: SQLite database (created automatically).

## Logs

Logs are saved in the `logs/app.log` file. They include the timestamp, user's IP address, the URL (long and short, if applicable), and the action performed. Logs rotate weekly, keeping the logs of the last 4 weeks.

## Possible Improvements

*   User authentication.
*   User interface to manage shortened URLs (edit, delete, statistics, tracking).
*   RESTful API.
*   Use of a more robust database (PostgreSQL, MySQL) for production.
*   Unit tests.

## Architecture

```
url_shortener/        <-- Project root directory
├── app/
│   ├── app.py            <-- Main Flask application file
│   ├── schema.sql        <-- SQLite database schema
│   ├── requirements.txt  <-- Python dependencies
│   ├── templates/        <-- HTML templates
│   │   ├── index.html    <-- Home page (form)
│   │   ├── 404.html      <-- 404 error page
│   │   ├── 429.html      <-- 429 error page
│   │   └── partials/
│   │       └── logo.html  <-- Reusable logo partial
│   └── static/           <-- Static files (CSS, JS, images)
│       ├── style.css     <-- Custom CSS file
│       └── images/
│           ├── favicon.ico <-- Application favicon
│           └── logo.png    <-- (Optional) Logo image
├── Dockerfile        <-- Instructions to build the Docker image
├── docker-compose.yml <-- Docker Compose configuration file
├── logs/              <-- (Created automatically) Log directory
│   └── app.log        <-- (Created automatically) Log file
├── urls.db            <-- (Created automatically) SQLite database
└── README.md         <-- This file
