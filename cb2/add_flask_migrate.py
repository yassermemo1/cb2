import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def update_requirements():
    """Add Flask-Migrate to requirements.txt if not already present."""
    requirements_path = Path("requirements.txt")
    
    if not requirements_path.exists():
        logger.error("requirements.txt not found")
        return False
    
    with open(requirements_path, 'r') as f:
        requirements = f.read()
    
    if "flask-migrate" in requirements.lower():
        logger.info("Flask-Migrate already in requirements.txt")
    else:
        logger.info("Adding Flask-Migrate to requirements.txt")
        with open(requirements_path, 'a') as f:
            f.write("\n# Database migrations\nflask-migrate>=4.0.0\n")
    
    return True

def install_flask_migrate():
    """Install Flask-Migrate package."""
    logger.info("Installing Flask-Migrate...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "flask-migrate"], check=True)
        logger.info("Flask-Migrate installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Flask-Migrate: {e}")
        return False

def create_migrations_script():
    """Create a migrations script."""
    migrations_script = Path("migrations_init.py")
    
    if migrations_script.exists():
        logger.info(f"{migrations_script} already exists")
        return True
    
    logger.info(f"Creating {migrations_script}")
    
    script_content = '''
import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_app():
    """Create a Flask app instance."""
    from config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    from models.base import db
    db.init_app(app)
    
    return app

def init_migrations():
    """Initialize Flask-Migrate."""
    app = create_app()
    
    # Import all models to ensure they're registered with SQLAlchemy
    # Add your model imports here
    from models.instance import CBInstance
    from models.agent import Agent
    from models.license import License
    from models.user import User
    from models.audit_log import AuditLog
    
    # Initialize Flask-Migrate
    from models.base import db
    migrate = Migrate(app, db)
    
    with app.app_context():
        from flask_migrate import init, migrate as migrate_command
        
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            logger.info("Initializing migrations directory...")
            init()
            logger.info("Migrations directory initialized")
        
        # Create initial migration
        logger.info("Creating initial migration...")
        migrate_command(message="Initial migration")
        logger.info("Initial migration created")
        
    logger.info("Flask-Migrate setup complete")

if __name__ == "__main__":
    init_migrations()
'''
    
    with open(migrations_script, 'w') as f:
        f.write(script_content)
    
    return True

def main():
    """Main function to add Flask-Migrate to the project."""
    logger.info("Adding Flask-Migrate to the project...")
    
    # Change to the project root directory if needed
    if os.path.basename(os.getcwd()) != "cb2":
        os.chdir("cb2")
    
    # Update requirements.txt
    if not update_requirements():
        logger.error("Failed to update requirements.txt")
        return False
    
    # Install Flask-Migrate
    if not install_flask_migrate():
        logger.error("Failed to install Flask-Migrate")
        return False
    
    # Create migrations script
    if not create_migrations_script():
        logger.error("Failed to create migrations script")
        return False
    
    logger.info("Flask-Migrate successfully added to the project")
    logger.info("To initialize migrations, run: python migrations_init.py")
    
    return True

if __name__ == "__main__":
    main() 