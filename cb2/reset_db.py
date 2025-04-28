#!/usr/bin/env python3

import os
import sys
import logging
from flask import current_app
from sqlalchemy_utils import database_exists, drop_database, create_database
from app import create_app
from api.models.admin import User

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def recreate_database(app):
    """Drop and recreate the database"""
    with app.app_context():
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        logger.info(f"Using database URL: {db_url}")
        
        from api.models.db import db
        
        if database_exists(db_url):
            logger.info("Dropping existing database...")
            drop_database(db_url)
            logger.info("Database dropped successfully")
        
        logger.info("Creating new database...")
        create_database(db_url)
        logger.info("Database created successfully")
        
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")

def create_admin_user(app):
    """Create admin user if none exists"""
    with app.app_context():
        from api.models.db import db
        
        # Check if any users exist
        users = User.query.all()
        if not users:
            logger.info("No users found. Creating initial admin user...")
            admin_user = User(
                username="admin",
                name="Administrator",
                email="admin@example.com",
                is_admin=True
            )
            admin_user.set_password("admin123")  # Default password, should be changed
            
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Admin user created successfully. Username: admin, Password: admin123")
            logger.warning("Please change the default admin password immediately after first login!")
        else:
            logger.info(f"Found {len(users)} existing users. Skipping admin user creation.")

if __name__ == "__main__":
    logger.info("Starting database reset process...")
    
    # Check if user wants to proceed
    if len(sys.argv) < 2 or sys.argv[1] != "--confirm":
        logger.warning("WARNING: This will delete all data in the database!")
        logger.warning("Run with --confirm to proceed with database reset")
        sys.exit(1)
    
    try:
        # Create the Flask app
        app = create_app()
        
        # Drop and recreate the database
        recreate_database(app)
        
        # Create admin user if none exists
        create_admin_user(app)
        
        logger.info("Database reset completed successfully!")
    except Exception as e:
        logger.error(f"Error during database reset: {str(e)}")
        sys.exit(1) 