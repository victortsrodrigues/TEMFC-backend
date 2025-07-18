"""
WSGI entry point for Gunicorn.
This file is used by Gunicorn to start the application.
"""
import os
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

# Create config for the app
config = {
    'ENV': 'production',
}

from app import create_app

# Create the Flask application instance with production config
app = create_app(config)

if __name__ == "__main__":
    app.run()
