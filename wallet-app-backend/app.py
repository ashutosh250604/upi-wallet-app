"""Entrypoint: `flask run`, `flask db upgrade` and gunicorn all use this module."""

from wallet import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
