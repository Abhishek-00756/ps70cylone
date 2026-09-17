"""Entrypoint: `python -m app.main` (or `flask --app app.main run`)."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
