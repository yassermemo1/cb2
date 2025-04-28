# Carbon Black Multi-Tenant Console

A web-based management console for monitoring and managing multiple Carbon Black instances from a single interface.

## Features

- Manage multiple Carbon Black instances (both Response and Protection)
- Monitor agent status across all instances
- Execute Carbon Black API commands through a unified interface
- View and export audit logs
- Import and export Carbon Black instance configurations

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yassermemo1/cb2.git
   cd cb2
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r cb2/requirements.txt
   ```

3. Set up the database:
   ```
   cd cb2
   python create_db.py
   ```

4. Run the application:
   ```
   chmod +x run.sh
   ./run.sh
   ```

   Or manually:
   ```
   export FLASK_ENV=development
   export FLASK_DEBUG=1
   python app.py
   ```

## Configuration

The application uses PostgreSQL by default. Update the database configuration in `config.py` if needed.

## Usage

1. Access the web interface at `http://localhost:5000`
2. Add Carbon Black instances through the UI
3. Monitor and manage agents across all instances

## License

MIT 