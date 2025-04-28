#!/usr/bin/env python3

import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('db_migration')

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Set the environment to development by default
    os.environ['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'development')
    
    # Load app configuration from the config module
    if os.environ['FLASK_ENV'] == 'development':
        app.config.from_object('config.DevelopmentConfig')
    elif os.environ['FLASK_ENV'] == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.ProductionConfig')
    
    return app

def migrate_database(app):
    """Add missing device_id column to the agents table."""
    try:
        db = SQLAlchemy(app)
        
        logger.info("Starting database migration...")
        
        # Check if device_id column exists in agents table
        with db.engine.connect() as conn:
            # Check if column exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='agents' AND column_name='device_id'
                );
            """)
            result = conn.execute(check_query)
            column_exists = result.scalar()
            
            if column_exists:
                logger.info("The device_id column already exists in the agents table. No migration needed.")
                return
            
            logger.info("Adding device_id column to agents table...")
            
            # Add the device_id column to the agents table
            add_column_query = text("""
                ALTER TABLE agents ADD COLUMN device_id VARCHAR(255);
            """)
            conn.execute(add_column_query)
            conn.commit()
            
            logger.info("Successfully added device_id column to agents table.")
    
    except SQLAlchemyError as e:
        logger.error(f"Error during database migration: {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    logger.info("Database migration script started")
    
    # Create the Flask app
    app = create_app()
    
    # Ask for user confirmation
    logger.info("This script will add the missing device_id column to the agents table.")
    confirmation = input("Do you want to proceed? (y/n): ")
    
    if confirmation.lower() != 'y':
        logger.info("Migration cancelled by user")
        sys.exit(0)
    
    # Run the migration
    success = migrate_database(app)
    
    if success:
        logger.info("Database migration completed successfully")
    else:
        logger.error("Database migration failed")
        sys.exit(1) 