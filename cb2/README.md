# Carbon Black Multi-Tenant Console

A management console for multiple Carbon Black instances, allowing centralized management of agents, policies, and more.

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure database settings in `config.py`
5. Create the database:
   ```
   python create_db.py
   ```
6. Run the application:
   ```
   ./run.sh
   ```

## Database Migrations

The application now uses Flask-Migrate to manage database schema changes:

### Setting Up Migrations (First Time)

To set up Flask-Migrate in an existing project:

```
python setup_migrations.py
```

This script will:
1. Add Flask-Migrate to your requirements.txt
2. Install Flask-Migrate in your virtual environment
3. Configure app.py to use Flask-Migrate
4. Create a management script for database operations
5. Initialize the migrations directory
6. Create and apply the initial migration

### Managing Database Migrations

After setup, you can use the following commands to manage migrations:

```
# Generate a new migration after model changes
flask db migrate -m "Description of changes"

# Apply pending migrations
flask db upgrade

# Rollback the most recent migration
flask db downgrade

# Show migration status
flask db current
flask db history
```

### Managing Database Tables

You can also use the management script for common database operations:

```
# Initialize database with tables and seed data
python manage.py init

# Drop all tables (dangerous!)
python manage.py drop-tables

# Recreate all tables (dangerous!)
python manage.py recreate-tables
```

## Features

- Multi-tenant management of Carbon Black instances
- Agent inventory across all instances
- User management with role-based access control
- Audit logging of all actions
- License usage monitoring and reporting
- API console for direct Carbon Black API access

## Project Structure

- `/api`: Backend API routes and utilities
  - `/routes`: API endpoint definitions
  - `/models`: Database models
  - `/utils`: Helper functions
- `/frontend`: Frontend templates and static files
- `/migrations`: Database migration scripts
- `app.py`: Main application entry point
- `config.py`: Application configuration
- `create_db.py`: Database creation script
- `manage.py`: Database management commands
- `run.sh`: Application startup script
- `setup_migrations.py`: Migration setup script 