import os
import sys
import logging
from flask import Flask
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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/cb_multi_tenant')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def migrate_database(app):
    """Add the server_type column to the instances table."""
    with app.app_context():
        try:
            # Check if user agrees to proceed
            if not os.environ.get('AUTO_MIGRATE', ''):
                confirm = input("This will alter your database schema. Continue? (y/n): ")
                if confirm.lower() != 'y':
                    logger.info("Migration cancelled by user")
                    return
            
            # Begin a transaction
            conn = db.engine.connect()
            trans = conn.begin()
            
            # Check if the column already exists
            result = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='instances' AND column_name='server_type'")
            if result.rowcount == 0:
                # Column doesn't exist, add it
                logger.info("Adding server_type column to instances table")
                conn.execute("ALTER TABLE instances ADD COLUMN server_type VARCHAR(50) DEFAULT 'response'")
                trans.commit()
                logger.info("Migration completed successfully")
            else:
                logger.info("server_type column already exists, no changes needed")
                trans.rollback()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    # Create app
    app = create_app()
    
    # Run migrations
    migrate_database(app) 