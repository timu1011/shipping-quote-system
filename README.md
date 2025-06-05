# Shipping Quote System

This repository contains a simple Flask application used for generating shipping quotes.

## Environment Variables

The application requires the following environment variables:

- `SECRET_KEY` – key used by Flask to secure sessions.
- `JWT_SECRET_KEY` – secret used for signing JWT tokens.

`docker-compose.yml` defines example values for local development.# Shipping Quote System

This project provides a simple web interface for managing shipping rates and schedules.

## Prerequisites

- **Python 3.9+** (if running without Docker)
- **Docker** and **docker-compose** (optional, for containerised setup)

## Setup

1. Clone this repository.
2. Install dependencies with `pip install -r requirements.txt` or run the provided container.
3. Ensure a `src/templates` directory exists and contains the HTML templates required by the Flask application.

## Running with Docker

To start the application using Docker Compose:

```bash
docker-compose up
```

The container will create an initial admin account using the credentials **admin** / **admin123** as defined in `docker-entrypoint.sh`.

## Development without Docker

Create a virtual environment, install requirements and start Flask manually:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.app
```

## Notes

- Templates must be placed in `src/templates` for the web pages to render correctly.
- By default the app listens on port `5000`.
