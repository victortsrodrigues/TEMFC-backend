"""
WSGI entry point for Gunicorn.
This file is used by Gunicorn to start the application.
"""
from app import create_app

# Create the Flask application instance
application = create_app()

# For compatibility with some WSGI servers
app = application

if __name__ == "__main__":
    app.run()