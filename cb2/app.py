import os
import argparse
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import config
from api.models import db, ma

# Import blueprints conditionally to avoid crashing on missing modules
try:
    from api.routes import cb_instance_bp, agent_bp, sync_bp, dashboard_bp, cbapi_bp
    from api.routes.license_routes import license_bp
    from api.routes.audit_routes import audit_bp
    from api.routes.cb_users_routes import cb_users_bp
    from api.routes.import_routes import import_bp
    from api.routes.auth_routes import auth_bp
    from frontend.routes import frontend_bp
    from api.routes import api_bp
    
    # Store available blueprints
    available_blueprints = {
        'cb_instance_bp': cb_instance_bp,
        'agent_bp': agent_bp,
        'sync_bp': sync_bp,
        'dashboard_bp': dashboard_bp,
        'cbapi_bp': cbapi_bp,
        'license_bp': license_bp,
        'audit_bp': audit_bp,
        'cb_users_bp': cb_users_bp,
        'import_bp': import_bp,
        'auth_bp': auth_bp,
        'frontend_bp': frontend_bp,
        'api_bp': api_bp
    }
except ImportError as e:
    logging.warning(f"Some blueprints could not be imported: {str(e)}")
    available_blueprints = {}

def configure_logging(app):
    """Configure application logging."""
    log_level_name = os.environ.get('FLASK_LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure Flask logger
    app.logger.setLevel(log_level)
    
    if log_level == logging.DEBUG:
        app.logger.debug("Debug logging enabled")

def create_app(config_name='default'):
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production', 'default')
        
    Returns:
        Flask application instance
    """
    # Create Flask app
    app = Flask(__name__, 
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set additional configuration from environment
    app.config['SKIP_CONNECTION_TESTS'] = os.environ.get('SKIP_CONNECTION_TESTS', 'false').lower() == 'true'
    
    # Configure logging
    configure_logging(app)
    app.logger.info(f"Initializing {app.config['APP_NAME']} in {config_name} mode")
    
    if app.config['SKIP_CONNECTION_TESTS']:
        app.logger.warning("Carbon Black connection tests are disabled")
    
    # Enable CORS
    CORS(app)
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    
    # Register blueprints
    for blueprint_name, blueprint in available_blueprints.items():
        if blueprint_name == 'api_bp':
            app.register_blueprint(blueprint, url_prefix='/api')
        else:
            app.register_blueprint(blueprint)
    
    # Request logger for debugging
    @app.before_request
    def log_request_info():
        if app.debug:
            app.logger.debug('Headers: %s', request.headers)
            app.logger.debug('Body: %s', request.get_data())
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'name': app.config['APP_NAME'],
            'version': '1.0.0',
            'description': 'Multi-tenant Carbon Black Management Console',
            'endpoints': {
                'instances': '/api/instances',
                'agents': '/api/agents',
                'sync': '/api/sync',
                'dashboard': '/api/dashboard',
                'cbapi': '/api/cbapi',
                'cb-users': '/api/cb-users',
                'audit': '/api/audit',
                'import': '/api/import'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f"Resource not found: {request.path}")
        return jsonify({
            'status': 'error',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Server error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
    # Create all database tables
    with app.app_context():
        app.logger.info("Creating database tables if they don't exist")
        db.create_all()
    
    return app

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Carbon Black Multi-Tenant Console')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the application on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Set debug mode from command line or environment
    debug_mode = args.debug or os.environ.get('FLASK_DEBUG', '0') == '1'
    
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    
    print(f"🔌 Starting server on {args.host}:{args.port} (debug: {debug_mode})")
    app.run(host=args.host, port=args.port, debug=debug_mode) 