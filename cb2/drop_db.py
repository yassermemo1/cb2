#!/usr/bin/env python
import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_app():
    """Create a Flask app for database initialization."""
    from api.extensions import db
    
    app = Flask(__name__)
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/cb2')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    return app, db

def drop_and_create_tables():
    """Drop and recreate all database tables."""
    try:
        app, db = create_app()
        
        with app.app_context():
            logger.info("Dropping all tables...")
            db.drop_all()
            
            logger.info("Creating all tables...")
            db.create_all()
            
            logger.info("Database reset completed successfully.")
    
    except Exception as e:
        logger.error(f"Database reset failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    confirmation = input("This will DELETE ALL DATA in the database. Are you sure? (y/N): ")
    
    if confirmation.lower() == 'y':
        logger.info("Starting database reset...")
        drop_and_create_tables()
        logger.info("Database reset completed.")
    else:
        logger.info("Database reset cancelled.")
        sys.exit(0) 