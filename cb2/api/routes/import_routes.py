import os
import logging
import csv
import io
from flask import Blueprint, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
from ..models import db, CBInstance
from ..utils.cb_api_helper import CBAPIHelper

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
import_bp = Blueprint('import', __name__, url_prefix='/api/import')

@import_bp.route('/instances', methods=['POST'])
def import_instances():
    """Import Carbon Black instances from a CSV file."""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file part in the request'
            }), 400
            
        file = request.files['file']
        
        # If user does not select file, browser may send empty file
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
            
        # Check file extension
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'message': 'Only CSV files are allowed'
            }), 400
            
        # Read CSV data from the file
        csv_data = file.read().decode('utf-8')
        
        # Import instances from CSV
        success, count, message, failed_rows = CBAPIHelper.import_instances_from_csv(csv_data)
        
        # Return response
        return jsonify({
            'success': success,
            'message': message,
            'count': count,
            'failed_rows': failed_rows
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error in import_instances: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error importing instances: {str(e)}"
        }), 500

@import_bp.route('/instances/export', methods=['GET'])
def export_instances():
    """Export Carbon Black instances to a CSV file."""
    try:
        # Get all instances
        instances = CBInstance.query.all()
        
        if not instances:
            return jsonify({
                'success': False,
                'message': 'No instances found to export'
            }), 404
        
        # Create CSV file in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['id', 'name', 'api_base_url', 'api_token', 'is_active', 'connection_status', 'sensors'])
        
        # Write data rows
        for instance in instances:
            writer.writerow([
                instance.id,
                instance.name,
                instance.api_base_url,
                instance.api_token,  # Note: This exports sensitive API tokens
                'true' if instance.is_active else 'false',
                instance.connection_status,
                instance.sensors
            ])
        
        # Create response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=carbon_black_instances.csv'}
        )
        
    except Exception as e:
        logger.error(f"Error in export_instances: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error exporting instances: {str(e)}"
        }), 500 