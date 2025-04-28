#!/usr/bin/env python3

import os
import sys
import logging
from flask_migrate import Migrate, init, migrate, upgrade

# Add the current directory to path if needed
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_migrations():
    """Set up Flask-Migrate for database migrations."""
    logger.info("Setting up Flask-Migrate...")
    
    try:
        # Import here to avoid circular imports
        from app import create_app, db
        
        # Create Flask app with correct configuration
        env = os.getenv('FLASK_ENV', 'development')
        app = create_app(env)
        
        # Initialize Flask-Migrate
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Check if migrations directory exists
            if not os.path.exists('migrations'):
                logger.info("Initializing migrations directory...")
                init()
            
            # Generate initial migration if it doesn't exist
            migrations_folder = os.path.join('migrations', 'versions')
            if not os.path.exists(migrations_folder) or not os.listdir(migrations_folder):
                logger.info("Creating initial migration...")
                migrate(message="Initial migration")
            
            # Apply any pending migrations
            logger.info("Applying migrations...")
            upgrade()
        
        logger.info("Database migration setup complete!")
        return True
    
    except Exception as e:
        logger.error(f"Error setting up migrations: {str(e)}")
        return False

if __name__ == '__main__':
    success = setup_migrations()
    if not success:
        logger.error("Failed to set up database migrations")
        sys.exit(1)
    sys.exit(0) 