import os
import sys
import logging
from flask import Flask
from sqlalchemy import text
from api.models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the app from environment variables or set defaults
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'postgresql://postgres:postgres@localhost/carbon_black_edr')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def drop_users_table(app):
    """Drop the users table from the database."""
    with app.app_context():
        try:
            # Check if user agrees to proceed
            if not os.environ.get('AUTO_MIGRATE', ''):
                confirm = input("This will drop the users table and all user data. Continue? (y/n): ")
                if confirm.lower() != 'y':
                    logger.info("Migration cancelled by user")
                    return
            
            # Begin a transaction
            conn = db.engine.connect()
            trans = conn.begin()
            
            logger.info("Checking if the users table exists")
            
            # Check if the users table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'users')"
            ))
            exists = result.scalar()
            
            if exists:
                logger.info("Dropping the users table")
                
                # Drop foreign key constraints first
                logger.info("Removing foreign key constraints")
                conn.execute(text(
                    "ALTER TABLE IF EXISTS audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey"
                ))
                
                # Drop the users table
                conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
                
                # Update the audit_logs table to make user_id nullable
                logger.info("Updating audit_logs table to make user_id nullable")
                conn.execute(text(
                    "ALTER TABLE IF EXISTS audit_logs ALTER COLUMN user_id DROP NOT NULL"
                ))
                
                trans.commit()
                logger.info("Users table and related constraints dropped successfully")
            else:
                logger.info("Users table does not exist, no changes needed")
                trans.rollback()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    # Create app
    app = create_app()
    
    # Run migration
    drop_users_table(app) 