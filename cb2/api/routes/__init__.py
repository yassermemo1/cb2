from flask import Blueprint
from .cb_instance_routes import cb_instance_bp
from .agent_routes import agent_bp
from .sync_routes import sync_bp
from .dashboard_routes import dashboard_bp
from .cbapi_routes import cbapi_bp

# Create a master API blueprint
api_bp = Blueprint('api', __name__)

# Register all route blueprints with api_bp
# Note: These are registered directly with the app in app.py, 
# but api_bp can be used for grouping API routes/functionality

__all__ = ['cb_instance_bp', 'agent_bp', 'sync_bp', 'dashboard_bp', 'cbapi_bp', 'api_bp'] 