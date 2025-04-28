#!/bin/bash
set -e

# Change to the script's directory
cd "$(dirname "$0")"
echo "🔄 Setting up Carbon Black Multi-Tenant Console..."

# Default settings
DEBUG_MODE=${DEBUG_MODE:-false}
SKIP_CONNECTION_TESTS=${SKIP_CONNECTION_TESTS:-false}
RESET_DB=${RESET_DB:-false}

if [ "$DEBUG_MODE" = "true" ]; then
    echo "🐛 DEBUG MODE ENABLED"
    export FLASK_DEBUG=1
    LOG_LEVEL="DEBUG"
else
    export FLASK_DEBUG=0
    LOG_LEVEL=${LOG_LEVEL:-"INFO"}
fi

# Check for Python installation
check_python() {
    if command -v python3 &> /dev/null; then
        echo "✅ Python 3 found: $(python3 --version)"
        PYTHON_CMD="python3"
        return 0
    elif command -v python &> /dev/null && [[ $(python --version 2>&1) == *"Python 3"* ]]; then
        echo "✅ Python 3 found: $(python --version)"
        PYTHON_CMD="python"
        return 0
    else
        return 1
    fi
}

# Install Python if not found
install_python() {
    echo "❌ Python 3 not found. Attempting to install..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "📦 Installing Python using Homebrew..."
            brew install python
        else
            echo "📦 Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            echo "📦 Installing Python using Homebrew..."
            brew install python
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            echo "📦 Installing Python using apt..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            echo "📦 Installing Python using yum..."
            sudo yum install -y python3 python3-pip
        else
            echo "❌ Unsupported Linux distribution. Please install Python 3 manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        echo "❌ On Windows, please install Python 3 manually from https://www.python.org/downloads/"
        exit 1
    else
        echo "❌ Unsupported operating system. Please install Python 3 manually."
        exit 1
    fi
    
    # Verify installation
    if ! check_python; then
        echo "❌ Failed to install Python 3. Please install it manually."
        exit 1
    fi
}

# Find an available port
find_available_port() {
    local port=$1
    local max_port=$(($port + 100))
    
    while [[ $port -le $max_port ]]; do
        if ! nc -z localhost $port &>/dev/null; then
            echo $port
            return 0
        fi
        ((port++))
    done
    
    echo "❌ No available ports found between $1 and $max_port."
    exit 1
}

# Check for Python or install it
if ! check_python; then
    install_python
fi

# Default database settings
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_NAME=${DB_NAME:-cb2}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

# Find an available port for the app
DEFAULT_PORT=5005
APP_PORT=${APP_PORT:-$(find_available_port $DEFAULT_PORT)}

# Display and confirm settings
echo "📊 Configuration:"
echo "   - Database: $DB_NAME"
echo "   - DB User: $DB_USER"
echo "   - DB Host: $DB_HOST:$DB_PORT"
echo "   - App Port: $APP_PORT"
echo "   - Debug Mode: $DEBUG_MODE"
echo "   - Skip Connection Tests: $SKIP_CONNECTION_TESTS"
echo "   - Reset Database: $RESET_DB"
echo "   - Log Level: $LOG_LEVEL"
echo ""
echo "To customize these settings, you can set the following environment variables:"
echo "   DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT, APP_PORT, DEBUG_MODE, SKIP_CONNECTION_TESTS, RESET_DB, LOG_LEVEL"
echo ""
read -p "Continue with these settings? [Y/n] " -n 1 -r REPLY
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "❌ Setup cancelled. Please set the environment variables and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set development environment
export FLASK_ENV=development
export FLASK_APP=app.py
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
export FLASK_LOG_LEVEL=$LOG_LEVEL
export SKIP_CONNECTION_TESTS=$SKIP_CONNECTION_TESTS
export RESET_DB=$RESET_DB
echo "💾 Using database connection: $DATABASE_URL"

# Check if PostgreSQL is running
echo "🔍 Checking database connection..."
if command -v pg_isready &> /dev/null; then
    pg_isready -h $DB_HOST -p $DB_PORT || {
        echo "❌ PostgreSQL is not running. Please start your PostgreSQL server."
        exit 1
    }
    echo "✅ Database is running."
else
    echo "⚠️ pg_isready command not found. Skipping database check."
fi

# Initialize or reset the database using Flask-Migrate
if [ "$RESET_DB" = "true" ]; then
    echo "🧨 RESETTING DATABASE: All existing data will be lost!"
    read -p "Are you sure you want to reset the database? [y/N] " -n 1 -r CONFIRM_RESET
    echo
    if [[ $CONFIRM_RESET =~ ^[Yy]$ ]]; then
        echo "🗄️ Dropping and recreating database tables with migrations..."
        # Drop all tables first
        $PYTHON_CMD -c "
from app import create_app
from api.models import db

app = create_app('development')
with app.app_context():
    db.drop_all()
    print('✅ Database tables dropped successfully!')
"
        # Then set up migrations and apply them
        $PYTHON_CMD setup_migrations.py
    else
        echo "❌ Database reset cancelled."
    fi
else
    # Initialize database with migrations
    echo "🗄️ Setting up database with migrations..."
    $PYTHON_CMD setup_migrations.py
fi

# Configure logging
echo "📝 Configuring logging level: $LOG_LEVEL"

# Run the application
echo "🚀 Starting the application on port $APP_PORT (debug mode: $DEBUG_MODE)..."
if [ "$DEBUG_MODE" = "true" ]; then
    echo "🔍 Debug mode is enabled - connection tests can be skipped via the API"
    if [ "$SKIP_CONNECTION_TESTS" = "true" ]; then
        echo "⏩ Connection tests will be skipped by default"
    fi
fi

$PYTHON_CMD app.py --port $APP_PORT

# Deactivate virtual environment on exit
trap "echo '👋 Deactivating virtual environment...'; deactivate" EXIT 