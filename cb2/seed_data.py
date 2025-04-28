import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from api.models import db, User, CBInstance
from config import config

def create_app():
    """Create a Flask app instance for seeding data."""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    return app

def add_test_users(app):
    """Add test users to the database."""
    with app.app_context():
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@example.com',
                password='password123',
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            db.session.add(admin)
        
        # Add a regular user
        user = User.query.filter_by(username='user').first()
        if not user:
            print("Creating regular user...")
            regular_user = User(
                username='user',
                email='user@example.com',
                password='password123',
                first_name='Regular',
                last_name='User',
                is_admin=False
            )
            db.session.add(regular_user)
        
        db.session.commit()
        print("Users created successfully.")

def add_test_instances(app):
    """Add test CB instances to the database."""
    with app.app_context():
        # Check if we already have instances
        existing_count = CBInstance.query.count()
        if existing_count > 0:
            print(f"Already have {existing_count} instances. Skipping instance creation.")
            return
        
        # Add a test CB Response instance
        print("Creating test CB Response instance...")
        response_instance = CBInstance(
            id='resp1',
            name='CB Response Test',
            api_base_url='https://cb-response.example.com',
            api_token='abcdef123456',
            connection_status='Connected',
            sensors=125,
            version='7.5.0',
            connection_message='Test instance connection successful',
            is_active=True
        )
        
        # Add a test CB Protection instance
        print("Creating test CB Protection instance...")
        protection_instance = CBInstance(
            id='prot1',
            name='CB Protection Test',
            api_base_url='https://cb-protection.example.com',
            api_token='xyz789012',
            connection_status='Connected',
            sensors=85,
            version='8.1.4',
            connection_message='Test instance connection successful',
            is_active=True
        )
        
        db.session.add(response_instance)
        db.session.add(protection_instance)
        db.session.commit()
        print("Test instances created successfully.")

if __name__ == '__main__':
    app = create_app()
    
    # Add test data
    with app.app_context():
        db.create_all()
    
    add_test_users(app)
    add_test_instances(app)
    
    print("Seed data added successfully!") 