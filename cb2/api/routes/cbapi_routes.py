from flask import Blueprint, request, jsonify
from ..models import db, CBInstance, Agent
from ..utils.cb_api_helper import CBAPIHelper

cbapi_bp = Blueprint('cbapi', __name__, url_prefix='/api/cbapi')

@cbapi_bp.route('/execute', methods=['POST'])
def execute_api_action():
    """Execute a Carbon Black API action."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    # Required parameters
    required_fields = ['instance_id', 'action', 'method', 'endpoint']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Get the instance
    instance_id = data['instance_id']
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Execute the API action
    try:
        result = execute_cb_api_action(
            cb_api, 
            instance,
            data['action'],
            data['method'],
            data['endpoint'],
            data.get('params', {}),
            data.get('body', {})
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error executing API action: {str(e)}'
        }), 500

@cbapi_bp.route('/agents', methods=['GET'])
def get_agents():
    """Get agents from a Carbon Black instance."""
    instance_id = request.args.get('instance_id')
    
    if not instance_id:
        return jsonify({
            'success': False,
            'message': 'Missing instance_id parameter'
        }), 400
    
    # Get the instance
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Get agents based on server type
    try:
        if instance.server_type.lower() == 'response':
            sensors = cb_api.select('Sensor')
            agents = []
            
            for sensor in sensors:
                agent = {
                    'id': sensor.id,
                    'hostname': getattr(sensor, 'hostname', ''),
                    'status': getattr(sensor, 'status', ''),
                    'os_type': getattr(sensor, 'os_type', ''),
                    'sensor_version': getattr(sensor, 'build_version_string', '')
                }
                agents.append(agent)
            
            return jsonify({
                'success': True,
                'data': agents
            }), 200
            
        else:  # 'protection'
            computers = cb_api.select('Computer')
            agents = []
            
            for computer in computers:
                agent = {
                    'id': computer.id,
                    'hostname': getattr(computer, 'name', ''),
                    'status': 'Connected' if getattr(computer, 'connected', False) else 'Disconnected',
                    'os_type': getattr(computer, 'osShortName', ''),
                    'sensor_version': getattr(computer, 'agentVersion', '')
                }
                agents.append(agent)
            
            return jsonify({
                'success': True,
                'data': agents
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching agents: {str(e)}'
        }), 500

@cbapi_bp.route('/live-response/sessions', methods=['GET'])
def get_live_response_sessions():
    """Get active Live Response sessions."""
    instance_id = request.args.get('instance_id')
    
    if not instance_id:
        return jsonify({
            'success': False,
            'message': 'Missing instance_id parameter'
        }), 400
    
    # Get the instance
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Only applicable to CB Response
    if instance.server_type.lower() != 'response':
        return jsonify({
            'success': False,
            'message': 'Live Response is only available for CB Response instances'
        }), 400
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Get live response sessions
    try:
        sessions = cb_api.select('Session')
        session_list = []
        
        for session in sessions:
            session_data = {
                'id': session.id,
                'sensor_id': getattr(session, 'sensor_id', ''),
                'status': getattr(session, 'status', ''),
                'created_at': getattr(session, 'created_at', '')
            }
            session_list.append(session_data)
        
        return jsonify({
            'success': True,
            'data': session_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching live response sessions: {str(e)}'
        }), 500

@cbapi_bp.route('/live-response/session', methods=['POST'])
def start_live_response_session():
    """Start a new Live Response session."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    required_fields = ['instance_id', 'sensor_id']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Get the instance
    instance_id = data['instance_id']
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Only applicable to CB Response
    if instance.server_type.lower() != 'response':
        return jsonify({
            'success': False,
            'message': 'Live Response is only available for CB Response instances'
        }), 400
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Start live response session
    try:
        sensor_id = data['sensor_id']
        session = cb_api.create('Session', sensor_id=sensor_id)
        
        session_data = {
            'id': session.id,
            'sensor_id': getattr(session, 'sensor_id', ''),
            'status': getattr(session, 'status', ''),
            'created_at': getattr(session, 'created_at', '')
        }
        
        return jsonify({
            'success': True,
            'data': session_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting live response session: {str(e)}'
        }), 500

@cbapi_bp.route('/live-response/command', methods=['POST'])
def execute_live_response_command():
    """Execute a command in a Live Response session."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    required_fields = ['instance_id', 'session_id', 'command', 'command_type']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
    
    # Get the instance
    instance_id = data['instance_id']
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Only applicable to CB Response
    if instance.server_type.lower() != 'response':
        return jsonify({
            'success': False,
            'message': 'Live Response is only available for CB Response instances'
        }), 400
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Execute live response command
    try:
        session_id = data['session_id']
        command_type = data['command_type']
        command = data['command']
        arguments = data.get('arguments', {})
        
        session = cb_api.select('Session', session_id)
        
        # Execute command based on type
        if command_type == 'process':
            result = session.create_process(command)
        elif command_type == 'file':
            result = session.list_directory(command)
        elif command_type == 'registry':
            result = session.list_registry_keys(command)
        else:
            result = session.create_command(command_type, command, arguments)
        
        command_result = {
            'id': result.id,
            'status': result.status,
            'result': result.result,
            'session_id': session_id
        }
        
        return jsonify({
            'success': True,
            'data': command_result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error executing live response command: {str(e)}'
        }), 500

@cbapi_bp.route('/threats', methods=['GET'])
def get_threats():
    """Get threats from a Carbon Black instance."""
    instance_id = request.args.get('instance_id')
    
    if not instance_id:
        return jsonify({
            'success': False,
            'message': 'Missing instance_id parameter'
        }), 400
    
    # Get the instance
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Only applicable to CB Response
    if instance.server_type.lower() != 'response':
        return jsonify({
            'success': False,
            'message': 'Threats API is only available for CB Response instances'
        }), 400
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Get threats
    try:
        threats = cb_api.select('Feed')
        threat_list = []
        
        for threat in threats:
            threat_data = {
                'id': threat.id,
                'name': getattr(threat, 'name', ''),
                'provider_url': getattr(threat, 'provider_url', ''),
                'summary': getattr(threat, 'summary', ''),
                'category': getattr(threat, 'category', ''),
                'reports': getattr(threat, 'reports', [])
            }
            threat_list.append(threat_data)
        
        return jsonify({
            'success': True,
            'data': threat_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching threats: {str(e)}'
        }), 500

@cbapi_bp.route('/licenses', methods=['GET'])
def get_licenses():
    """Get license information for all instances."""
    try:
        from datetime import datetime
        from flask import current_app
        
        # Get all instances
        from cb2.api.models.instance import CBInstance
        instances = CBInstance.query.all()
        license_info = []
        total_seats = 0
        used_seats = 0
        dropped_connections = []
        
        # Query each instance for license information
        for instance in instances:
            try:
                # Initialize the CB API client
                cb_api = CBAPIHelper.get_cb_api(instance)
                
                if not cb_api:
                    current_app.logger.error(f"Failed to initialize CB API for instance {instance.name}")
                    continue
                
                # Get license information based on server type
                if instance.server_type.lower() == 'response':
                    # For Carbon Black Response (EDR)
                    license_data = cb_api._request('GET', '/api/v1/license')
                    
                    # Extract relevant license information
                    instance_license = {
                        'id': instance.id,
                        'name': instance.name,
                        'license_type': license_data.get('edr_license_type', 'Standard'),
                        'seats_used': license_data.get('sensors_active', 0),
                        'total_seats': license_data.get('sensors_maximum', 0),
                        'start_date': license_data.get('license_valid_from'),
                        'expiration_date': license_data.get('license_valid_to')
                    }
                    
                    # Get dropped connections due to license issues (if available)
                    try:
                        # This endpoint might vary depending on CB Response version
                        events = cb_api._request('GET', '/api/v1/sensor/events?q=license')
                        if events and 'results' in events:
                            for event in events['results']:
                                if 'license' in event.get('description', '').lower():
                                    dropped_connections.append({
                                        'instance_id': instance.id,
                                        'instance_name': instance.name,
                                        'agent_id': event.get('sensor_id'),
                                        'agent_hostname': event.get('hostname', 'Unknown'),
                                        'timestamp': event.get('timestamp'),
                                        'reason': event.get('description', 'License limit reached')
                                    })
                    except Exception as e:
                        current_app.logger.error(f"Error getting dropped connections for {instance.name}: {str(e)}")
                
                else:  # 'protection'
                    # For Carbon Black Protection (App Control)
                    license_data = cb_api._request('GET', '/api/bit9platform/v1/license')
                    
                    # Extract relevant license information
                    instance_license = {
                        'id': instance.id,
                        'name': instance.name,
                        'license_type': license_data.get('type', 'Standard'),
                        'seats_used': license_data.get('agentsUsed', 0),
                        'total_seats': license_data.get('maxAgents', 0),
                        'start_date': license_data.get('startDate'),
                        'expiration_date': license_data.get('expirationDate')
                    }
                    
                    # Get dropped connections due to license issues (if available)
                    try:
                        # This endpoint might vary depending on CB Protection version
                        events = cb_api._request('GET', '/api/bit9platform/v1/events?q=licenseLimit')
                        if events:
                            for event in events:
                                dropped_connections.append({
                                    'instance_id': instance.id,
                                    'instance_name': instance.name,
                                    'agent_id': event.get('agentId'),
                                    'agent_hostname': event.get('computerName', 'Unknown'),
                                    'timestamp': event.get('timestamp'),
                                    'reason': event.get('description', 'License limit reached')
                                })
                    except Exception as e:
                        current_app.logger.error(f"Error getting dropped connections for {instance.name}: {str(e)}")
                
                # Add instance license info to the list
                license_info.append(instance_license)
                
                # Add to totals
                total_seats += instance_license['total_seats']
                used_seats += instance_license['seats_used']
                
            except Exception as e:
                current_app.logger.error(f"Error getting license information for instance {instance.name}: {str(e)}")
                # Add a placeholder entry with error information
                license_info.append({
                    'id': instance.id,
                    'name': instance.name,
                    'license_type': 'Unknown',
                    'seats_used': 0,
                    'total_seats': 0,
                    'start_date': None,
                    'expiration_date': None,
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'total_seats': total_seats,
            'used_seats': used_seats,
            'available_seats': total_seats - used_seats,
            'dropped_connections_count': len(dropped_connections),
            'instances': license_info,
            'dropped_connections': dropped_connections
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting license information: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve license information: {str(e)}'
        }), 500

@cbapi_bp.route('/audit-logs', methods=['GET'])
def get_cb_audit_logs():
    """Get audit logs from a Carbon Black instance."""
    instance_id = request.args.get('instance_id')
    
    if not instance_id:
        return jsonify({
            'success': False,
            'message': 'Missing instance_id parameter'
        }), 400
    
    # Get the instance
    instance = CBInstance.query.get(instance_id)
    
    if not instance:
        return jsonify({
            'success': False,
            'message': 'Instance not found'
        }), 404
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    # Optional query parameters
    days = request.args.get('days', default=7, type=int)
    limit = request.args.get('limit', default=100, type=int)
    event_type = request.args.get('event_type')
    username = request.args.get('username')
    
    try:
        # Different implementation based on server type
        if instance.server_type.lower() == 'response':
            # For CB Response, we need to use a direct query since there's no specific audit log type
            # The audit logs in CB Response are typically stored in the 'events' table
            query = f"select * from events where type='audit'"
            
            # Add filters if provided
            if username:
                query += f" and username:'{username}'"
            
            if event_type:
                query += f" and description:'{event_type}'"
                
            # Add time restriction
            if days > 0:
                query += f" and timestamp:-{days}d"
                
            # Execute the query
            results = cb_api.select(query, rows=limit)
            audit_logs = []
            
            for result in results:
                audit_log = {
                    'timestamp': getattr(result, 'timestamp', ''),
                    'type': getattr(result, 'type', ''),
                    'username': getattr(result, 'username', ''),
                    'description': getattr(result, 'description', ''),
                    'details': getattr(result, 'details', '')
                }
                audit_logs.append(audit_log)
            
            return jsonify({
                'success': True,
                'data': audit_logs
            }), 200
            
        else:  # 'protection'
            # For CB Protection, use the direct API endpoint for audit logs
            endpoint = "/api/v1/auditLog"
            
            # Build query parameters
            params = {}
            
            if days > 0:
                from datetime import datetime, timedelta
                start_date = datetime.now() - timedelta(days=days)
                params['startDate'] = start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            if username:
                params['userName'] = username
                
            if event_type:
                params['eventType'] = event_type
                
            if limit > 0:
                params['limit'] = limit
            
            # Execute the API action using our helper function
            result = execute_cb_api_action(
                cb_api,
                instance,
                'get_audit_logs',
                'GET',
                endpoint,
                params,
                {}
            )
            
            return jsonify({
                'success': True,
                'data': result
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching audit logs: {str(e)}'
        }), 500

def execute_cb_api_action(cb_api, instance, action, method, endpoint, params, body):
    """Execute a Carbon Black API action."""
    # This is a simplified implementation
    # In a real implementation, this would handle various API endpoints
    # and return the appropriate data
    
    # Prepare the full endpoint
    full_endpoint = endpoint
    if not full_endpoint.startswith('/'):
        full_endpoint = '/' + full_endpoint
    
    # Execute the API request based on the method
    try:
        if method == 'GET':
            response = cb_api._request('GET', full_endpoint, params=params)
        elif method == 'POST':
            response = cb_api._request('POST', full_endpoint, data=body)
        elif method == 'PUT':
            response = cb_api._request('PUT', full_endpoint, data=body)
        elif method == 'DELETE':
            response = cb_api._request('DELETE', full_endpoint)
        else:
            raise ValueError(f'Unsupported method: {method}')
        
        return response
        
    except Exception as e:
        raise Exception(f'Error executing API request: {str(e)}') 