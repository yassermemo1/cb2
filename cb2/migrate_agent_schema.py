#!/usr/bin/env python3

import os
import sys
import logging
from flask import current_app
from app import create_app
from sqlalchemy import text, inspect

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def add_device_id_column(app):
    """Add device_id column to agents table if it doesn't exist"""
    with app.app_context():
        from api.models.base import db
        
        # Get database connection
        conn = db.engine.connect()
        
        # Check if the device_id column exists
        inspector = inspect(db.engine)
        has_device_id = False
        columns = inspector.get_columns('agents')
        for column in columns:
            if column['name'] == 'device_id':
                has_device_id = True
                break
        
        if not has_device_id:
            logger.info("Adding device_id column to agents table...")
            try:
                # Add the column
                conn.execute(text("ALTER TABLE agents ADD COLUMN device_id VARCHAR(50)"))
                
                # Update device_id values from id column
                conn.execute(text("UPDATE agents SET device_id = id"))
                
                # Commit the transaction
                conn.commit()
                logger.info("Successfully added device_id column to agents table")
            except Exception as e:
                logger.error(f"Error adding device_id column: {str(e)}")
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            logger.info("device_id column already exists in agents table. No migration needed.")

if __name__ == "__main__":
    logger.info("Starting database migration process...")
    
    try:
        # Create the Flask app
        app = create_app()
        
        # Add device_id column if it doesn't exist
        add_device_id_column(app)
        
        logger.info("Database migration completed successfully!")
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        sys.exit(1) 