from flask import Blueprint, jsonify, request, current_app

# Create a blueprint for authentication endpoints without user requirements
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Return the authentication status - will always return authenticated for now."""
    return jsonify({
        'status': 'success',
        'authenticated': True,
        'message': 'No authentication required in this version'
    })

@auth_bp.route('/info', methods=['GET'])
def auth_info():
    """Return information about the authentication system."""
    return jsonify({
        'status': 'success',
        'message': 'Authentication system is disabled in this version',
        'auth_type': 'none'
    }) 