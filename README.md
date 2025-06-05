 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/README.md
index 0000000000000000000000000000000000000000..32f0103b4be15f9fb9f84e8b5b06a9fbf9b45a45 100644
--- a//dev/null
+++ b/README.md
@@ -0,0 +1,40 @@
+# Shipping Quote System
+
+This project provides a simple web interface for managing shipping rates and schedules.
+
+## Prerequisites
+
+- **Python 3.9+** (if running without Docker)
+- **Docker** and **docker-compose** (optional, for containerised setup)
+
+## Setup
+
+1. Clone this repository.
+2. Install dependencies with `pip install -r requirements.txt` or run the provided container.
+3. Ensure a `src/templates` directory exists and contains the HTML templates required by the Flask application.
+
+## Running with Docker
+
+To start the application using Docker Compose:
+
+```bash
+docker-compose up
+```
+
+The container will create an initial admin account using the credentials **admin** / **admin123** as defined in `docker-entrypoint.sh`.
+
+## Development without Docker
+
+Create a virtual environment, install requirements and start Flask manually:
+
+```bash
+python -m venv venv
+source venv/bin/activate
+pip install -r requirements.txt
+python -m src.app
+```
+
+## Notes
+
+- Templates must be placed in `src/templates` for the web pages to render correctly.
+- By default the app listens on port `5000`.
 
EOF
)
