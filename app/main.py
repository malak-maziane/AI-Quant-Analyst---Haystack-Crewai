"""
Entry point for the Flask web application.
Initializes the Flask app using the factory pattern
defined in app/__init__.py and starts the dev server.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )