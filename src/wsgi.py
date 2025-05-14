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
    'START_KEEP_ALIVE': os.environ.get('START_KEEP_ALIVE', 'true').lower() == 'true'
}

from app import create_app

# Create the Flask application instance with production config
application = create_app(config)

# For compatibility with some WSGI servers
app = application

if __name__ == "__main__":
    app.run()
