from flask import Blueprint, request, jsonify, current_app, Response
import logging
import csv
import io
from sqlalchemy.exc import SQLAlchemyError
from api.utils.cb_api_helper import CBAPIHelper
from api.models import CBInstance

cb_users_bp = Blueprint('cb_users', __name__, url_prefix='/api/cb-users')
logger = logging.getLogger(__name__)

@cb_users_bp.route('/', methods=['GET'])
def get_users():
    """Get users from a Carbon Black instance."""
    instance_id = request.args.get('instance_id')
    
    if not instance_id:
        return jsonify({
            "status": "error", 
            "message": "Instance ID is required"
        }), 400
    
    try:
        cb_instance = CBInstance.query.get(instance_id)
        if not cb_instance:
            return jsonify({
                "status": "error",
                "message": f"Carbon Black instance with ID {instance_id} not found"
            }), 404
        
        users = CBAPIHelper.get_users(cb_instance)
        return jsonify({
            "status": "success",
            "data": users
        })
    
    except Exception as e:
        error_msg = f"Error retrieving users: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500

@cb_users_bp.route('/export-csv', methods=['GET'])
def export_users_csv():
    """Export users from a Carbon Black instance to CSV."""
    instance_id = request.args.get('instance_id')
    
    if not instance_id:
        return jsonify({"error": "Instance ID is required"}), 400
    
    try:
        cb_instance = CBInstance.query.get(instance_id)
        if not cb_instance:
            return jsonify({"error": f"Carbon Black instance with ID {instance_id} not found"}), 404
        
        users = CBAPIHelper.get_users(cb_instance)
        
        if not users:
            return jsonify({"error": "No users found"}), 404
        
        # Create CSV in memory
        output = io.StringIO()
        fieldnames = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'status', 'last_login']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for user in users:
            writer.writerow(user)
        
        # Create response with CSV data
        response = Response(
            output.getvalue(), 
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=cb_users_{cb_instance.name}.csv'}
        )
        
        return response
    
    except Exception as e:
        error_msg = f"Error exporting users to CSV: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500 