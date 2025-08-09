# URL Shortener

A simple, yet powerful URL shortener application built with Python, Flask, and SQLite. It provides a clean user interface, a RESTful API, and detailed statistics for your shortened links. It is fully containerized using Docker for easy deployment.

## Features

*   **URL Shortening**: Quickly shorten long URLs.
*   **Customizable Expiration**: Set expiration dates for your links (24h, 48h, or 1 week).
*   **Usage Limits**: Limit the number of times a link can be used.
*   **Statistics Page**: Track the number of clicks and other details for each shortened URL.
*   **RESTful API**: Programmatically create short URLs with Swagger documentation.
*   **Rate Limiting**: Basic DDoS protection on the API and redirection endpoints.
*   **Comprehensive Logging**: Logs creations, accesses, expirations, and errors for monitoring and debugging.
*   **Dockerized**: Comes with `Dockerfile` and `docker-compose.yml` for easy and consistent deployment.

## Prerequisites

*   Docker
*   Docker Compose

## Installation and Running with Docker

This is the recommended way to run the application.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ClementLG/UrlShortener.git
    cd url-shortener
    ```

2.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```
    This command will build the Docker image and start the application in the background. The database and logs will be initialized automatically.

3.  **Access the application:**
    *   **Application**: `http://localhost:5000`
    *   **API Documentation (Swagger)**: `http://localhost:5000/apidocs/`

## Installation (Manual, without Docker)

If you prefer not to use Docker:

1.  **Prerequisites**:
    *   Python 3.7+
    *   Flask, Flask-Limiter, Flasgger

2.  **Clone the repository and navigate into it.**

3.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate    # On Windows
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r app/requirements.txt
    ```

5.  **Initialize the database:**
    ```bash
    flask init-db
    ```

6.  **Run the application:**
    ```bash
    flask run
    ```

## API Usage

The application includes a RESTful API for creating short URLs.

### Create a Short URL

*   **Endpoint**: `POST /api/urls`
*   **Content-Type**: `application/json`

**Request Body:**

```json
{
  "long_url": "https://your-long-url.com/with/a/very/long/path",
  "duration": "24h",
  "uses_limit": 100
}
```

*   `long_url` (string, required): The original URL to shorten.
*   `duration` (string, optional, default: `'24h'`): The validity period. Can be `'24h'`, `'48h'`, or `'1w'`.
*   `uses_limit` (integer, optional): The maximum number of uses.

**Success Response (201 Created):**

```json
{
  "short_url": "http://localhost:5000/aBcDeFg"
}
```

## Project Structure

```
url_shortener/
├── app/
│   ├── __init__.py
│   ├── app.py            # Main Flask application
│   ├── config.py         # Configuration file
│   ├── errors.py         # Custom error handlers
│   ├── requirements.txt  # Python dependencies
│   ├── schema.sql        # Database schema
│   ├── static/           # Static files (CSS, images)
│   └── templates/        # HTML templates
├── logs/                 # (Created automatically) Log directory
├── urls.db               # (Created automatically) SQLite database
├── Dockerfile            # Instructions to build the Docker image
├── docker-compose.yml    # Docker Compose configuration
└── README.md
```

## Logs

When running with Docker, logs are managed by the Docker daemon. You can view them with:
```bash
docker-compose logs -f
```
When running manually, logs are stored in `logs/app.log`. They rotate weekly, and the last 4 weeks of logs are kept. (Can be binded in docker container)
