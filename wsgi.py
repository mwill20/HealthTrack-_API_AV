"""
wsgi.py
Production WSGI entrypoint.

Gunicorn imports the module-level `app` object (see the Dockerfile CMD:
`gunicorn -b 0.0.0.0:5000 wsgi:app`). Keeping the factory call here — rather
than inside app/__init__.py — means importing the `app` package for tests does
not implicitly build and bind an application instance.
"""

from app import create_app

app = create_app()


if __name__ == "__main__":
    # Convenience for local, non-gunicorn runs. Production uses gunicorn.
    app.run(host="0.0.0.0", port=5000)
