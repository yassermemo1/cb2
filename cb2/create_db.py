#!/usr/bin/env python
import os
import sys
import logging
from flask import Flask
from sqlalchemy_utils import database_exists, create_database, drop_database

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app():
    """Create a minimal Flask app for database operations"""
    app = Flask(__name__)
    
    # Load the config
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)
    
    # Initialize database
    from api.models import db
    db.init_app(app)
    
    return app

def recreate_database(app):
    """Drop and recreate the database"""
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        logger.info(f"Database URI: {db_uri}")
        
        if database_exists(db_uri):
            logger.info("Dropping existing database...")
            drop_database(db_uri)
            logger.info("Database dropped successfully.")
        
        logger.info("Creating new database...")
        create_database(db_uri)
        logger.info("Database created successfully.")
        
        logger.info("Creating database tables...")
        from api.models import db
        db.create_all()
        logger.info("Database tables created successfully.")
        
        # Create initial admin user if needed
        create_admin_user(app)
        
        logger.info("Database setup complete!")

def create_admin_user(app):
    """Create an initial admin user if no users exist"""
    try:
        from api.models import User
        
        # Check if users exist
        user_count = User.query.count()
        if user_count == 0:
            logger.info("Creating initial admin user...")
            from api.models import User
            from werkzeug.security import generate_password_hash
            
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin"),
                is_admin=True
            )
            
            from api.models import db
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created successfully.")
        else:
            logger.info(f"Users already exist ({user_count} found). Skipping admin creation.")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting database creation script...")
    app = create_app()
    recreate_database(app) 