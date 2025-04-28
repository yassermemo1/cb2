from flask import Blueprint, request, jsonify, current_app, Response
from ..models import db, CBInstance, cb_instance_schema, cb_instances_schema
from ..utils import CBAPIHelper
import logging
import uuid
import csv
import io
from werkzeug.utils import secure_filename

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint
cb_instance_bp = Blueprint('cb_instance', __name__, url_prefix='/api/instances')

@cb_instance_bp.route('/', methods=['GET'])
def get_instances():
    """Get all CB instances."""
    try:
        instances = CBInstance.query.all()
        result = []
        
        for instance in instances:
            result.append({
                'id': instance.id,
                'name': instance.name,
                'api_base_url': instance.api_base_url,
                'connection_status': instance.connection_status,
                'sensors': instance.sensors,
                'version': instance.version,
                'connection_message': instance.connection_message,
                'is_active': instance.is_active,
                'server_type': instance.server_type,
                'last_checked': instance.last_checked.isoformat() if instance.last_checked else None
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving instances: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving instances: {str(e)}"
        }), 500

@cb_instance_bp.route('/<instance_id>', methods=['GET'])
def get_instance(instance_id):
    """Get a specific CB instance."""
    try:
        instance = CBInstance.query.get(instance_id)
        
        if not instance:
            return jsonify({
                'success': False,
                'message': f"Instance {instance_id} not found"
            }), 404
        
        result = {
            'id': instance.id,
            'name': instance.name,
            'api_base_url': instance.api_base_url,
            'connection_status': instance.connection_status,
            'sensors': instance.sensors,
            'version': instance.version,
            'connection_message': instance.connection_message,
            'is_active': instance.is_active,
            'server_type': instance.server_type,
            'last_checked': instance.last_checked.isoformat() if instance.last_checked else None
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving instance {instance_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving instance: {str(e)}"
        }), 500

@cb_instance_bp.route('/', methods=['POST'])
def create_instance():
    """Create a new CB instance."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': "No data provided"
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'api_base_url', 'api_token', 'server_type']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Check if URL already exists
        existing_instance = CBInstance.query.filter_by(api_base_url=data['api_base_url']).first()
        if existing_instance:
            return jsonify({
                'success': False,
                'message': f"An instance with URL {data['api_base_url']} already exists"
            }), 400
        
        # Generate an ID if not provided
        instance_id = data.get('id', str(uuid.uuid4())[:8])
        
        # Create new instance
        instance = CBInstance(
            id=instance_id,
            name=data['name'],
            api_base_url=data['api_base_url'],
            api_token=data['api_token'],
            server_type=data['server_type'],
            is_active=data.get('is_active', True)
        )
        
        # Test connection
        if not current_app.config.get('SKIP_CONNECTION_TESTS', False):
            connection_result = CBAPIHelper.test_connection(instance)
            
            instance.connection_status = connection_result.get('status', 'Unknown')
            instance.connection_message = connection_result.get('message', '')
            instance.version = connection_result.get('version', '')
            
            if connection_result.get('status') != 'Connected':
                current_app.logger.warning(f"Created instance {instance.name} with connection issue: {connection_result.get('message')}")
        
        db.session.add(instance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Instance {instance.name} created successfully",
            'data': {
                'id': instance.id,
                'name': instance.name,
                'api_base_url': instance.api_base_url,
                'connection_status': instance.connection_status,
                'sensors': instance.sensors,
                'version': instance.version,
                'connection_message': instance.connection_message,
                'is_active': instance.is_active,
                'server_type': instance.server_type
            }
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating instance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error creating instance: {str(e)}"
        }), 500

@cb_instance_bp.route('/<instance_id>', methods=['PUT'])
def update_instance(instance_id):
    """Update a CB instance."""
    try:
        instance = CBInstance.query.get(instance_id)
        
        if not instance:
            return jsonify({
                'success': False,
                'message': f"Instance {instance_id} not found"
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': "No data provided"
            }), 400
        
        # Update fields
        if 'name' in data:
            instance.name = data['name']
        
        if 'api_base_url' in data:
            # Check if URL already exists on a different instance
            existing_instance = CBInstance.query.filter_by(api_base_url=data['api_base_url']).first()
            if existing_instance and existing_instance.id != instance_id:
                return jsonify({
                    'success': False,
                    'message': f"An instance with URL {data['api_base_url']} already exists"
                }), 400
            
            instance.api_base_url = data['api_base_url']
        
        if 'api_token' in data:
            instance.api_token = data['api_token']
        
        if 'server_type' in data:
            instance.server_type = data['server_type']
        
        if 'is_active' in data:
            instance.is_active = data['is_active']
        
        # Test connection if API URL or token has changed
        if ('api_base_url' in data or 'api_token' in data or 'server_type' in data) and not current_app.config.get('SKIP_CONNECTION_TESTS', False):
            connection_result = CBAPIHelper.test_connection(instance)
            
            instance.connection_status = connection_result.get('status', 'Unknown')
            instance.connection_message = connection_result.get('message', '')
            instance.version = connection_result.get('version', '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Instance {instance.name} updated successfully",
            'data': {
                'id': instance.id,
                'name': instance.name,
                'api_base_url': instance.api_base_url,
                'connection_status': instance.connection_status,
                'sensors': instance.sensors,
                'version': instance.version,
                'connection_message': instance.connection_message,
                'is_active': instance.is_active,
                'server_type': instance.server_type,
                'last_checked': instance.last_checked.isoformat() if instance.last_checked else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error updating instance {instance_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error updating instance: {str(e)}"
        }), 500

@cb_instance_bp.route('/<instance_id>', methods=['DELETE'])
def delete_instance(instance_id):
    """Delete a CB instance."""
    try:
        instance = CBInstance.query.get(instance_id)
        
        if not instance:
            return jsonify({
                'success': False,
                'message': f"Instance {instance_id} not found"
            }), 404
        
        db.session.delete(instance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Instance {instance_id} deleted successfully"
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting instance {instance_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error deleting instance: {str(e)}"
        }), 500

@cb_instance_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a CB instance."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': "No data provided"
            }), 400
        
        # Validate required fields
        required_fields = ['api_base_url', 'api_token', 'server_type']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Create temporary instance for testing
        test_instance = CBInstance(
            id='temp_test',
            name='Connection Test',
            api_base_url=data['api_base_url'],
            api_token=data['api_token'],
            server_type=data['server_type']
        )
        
        # Test connection
        connection_result = CBAPIHelper.test_connection(test_instance)
        
        return jsonify({
            'success': True,
            'result': connection_result
        })
    except Exception as e:
        current_app.logger.error(f"Error testing connection: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error testing connection: {str(e)}"
        }), 500

@cb_instance_bp.route('/import-csv', methods=['POST'])
def import_instances_from_csv():
    """Import CB instances from a CSV file."""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': "No file provided"
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': "No file selected"
        }), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({
            'success': False,
            'message': "File must be a CSV"
        }), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        created_instances = []
        skipped_instances = []
        errors = []
        
        for i, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header row
            # Validate required fields
            required_fields = ['name', 'api_base_url', 'api_token', 'server_type']
            missing_fields = [field for field in required_fields if field not in row or not row[field]]
            
            if missing_fields:
                errors.append({
                    'row': i,
                    'message': f"Missing required fields: {', '.join(missing_fields)}"
                })
                continue
            
            # Check if instance already exists
            existing_instance = CBInstance.query.filter_by(api_base_url=row['api_base_url']).first()
            if existing_instance:
                skipped_instances.append({
                    'row': i,
                    'name': row['name'],
                    'api_base_url': row['api_base_url'],
                    'message': f"Instance with URL {row['api_base_url']} already exists"
                })
                continue
            
            # Generate an ID if not provided
            instance_id = row.get('id', str(uuid.uuid4())[:8])
            
            # Create new instance
            instance = CBInstance(
                id=instance_id,
                name=row['name'],
                api_base_url=row['api_base_url'],
                api_token=row['api_token'],
                server_type=row['server_type'],
                is_active=row.get('is_active', 'True').lower() in ['true', 'yes', '1']
            )
            
            # Test connection
            if not current_app.config.get('SKIP_CONNECTION_TESTS', False):
                connection_result = CBAPIHelper.test_connection(instance)
                
                instance.connection_status = connection_result.get('status', 'Unknown')
                instance.connection_message = connection_result.get('message', '')
                instance.version = connection_result.get('version', '')
            
            db.session.add(instance)
            
            created_instances.append({
                'id': instance.id,
                'name': instance.name,
                'api_base_url': instance.api_base_url,
                'connection_status': instance.connection_status,
                'version': instance.version
            })
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Successfully imported {len(created_instances)} instances, skipped {len(skipped_instances)}, with {len(errors)} errors",
            'created': created_instances,
            'skipped': skipped_instances,
            'errors': errors
        })
    except Exception as e:
        current_app.logger.error(f"Error importing instances: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error importing instances: {str(e)}"
        }), 500

@cb_instance_bp.route('/export-csv', methods=['GET'])
def export_instances_to_csv():
    """Export CB instances to a CSV file."""
    try:
        instances = CBInstance.query.all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'name', 'api_base_url', 'api_token', 'server_type', 
            'connection_status', 'sensors', 'version', 'is_active'
        ])
        writer.writeheader()
        
        for instance in instances:
            writer.writerow({
                'id': instance.id,
                'name': instance.name,
                'api_base_url': instance.api_base_url,
                'api_token': instance.api_token,
                'server_type': instance.server_type,
                'connection_status': instance.connection_status,
                'sensors': instance.sensors,
                'version': instance.version,
                'is_active': instance.is_active
            })
        
        # Create response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=cb_instances.csv'
            }
        )
        
        return response
    except Exception as e:
        current_app.logger.error(f"Error exporting instances: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error exporting instances: {str(e)}"
        }), 500 