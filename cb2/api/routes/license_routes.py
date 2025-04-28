from flask import Blueprint, jsonify, request, current_app
from ..models import db, CBInstance, Agent
from ..utils.cb_api_helper import CBAPIHelper

license_bp = Blueprint('license', __name__, url_prefix='/api/licenses')

@license_bp.route('/', methods=['GET'])
def get_licenses():
    """Get license information for all instances."""
    try:
        from datetime import datetime
        
        # Get all instances
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

@license_bp.route('/instance/<int:instance_id>', methods=['GET'])
def get_license_by_instance(instance_id):
    """Get detailed license information for a specific instance."""
    try:
        # Get the instance
        instance = CBInstance.query.get(instance_id)
        if not instance:
            return jsonify({
                'status': 'error',
                'message': f'Instance with ID {instance_id} not found'
            }), 404
        
        # Initialize the CB API client
        cb_api = CBAPIHelper.get_cb_api(instance)
        if not cb_api:
            return jsonify({
                'status': 'error',
                'message': f'Failed to initialize CB API for instance {instance.name}'
            }), 500
        
        license_data = {}
        agents_data = []
        
        # Get license information based on server type
        if instance.server_type.lower() == 'response':
            # Get license data
            license_data = cb_api._request('GET', '/api/v1/license')
            
            # Get agents
            sensors = cb_api.select('Sensor')
            for sensor in sensors:
                agent_data = {
                    'id': sensor.id,
                    'hostname': getattr(sensor, 'hostname', 'Unknown'),
                    'status': getattr(sensor, 'status', 'Unknown'),
                    'last_checkin': getattr(sensor, 'last_checkin_time', None),
                    'registration_time': getattr(sensor, 'registration_time', None),
                    'os_type': getattr(sensor, 'os_type', 'Unknown'),
                    'computer_name': getattr(sensor, 'computer_name', 'Unknown')
                }
                agents_data.append(agent_data)
                
        else:  # 'protection'
            # Get license data
            license_data = cb_api._request('GET', '/api/bit9platform/v1/license')
            
            # Get agents
            computers = cb_api.select('Computer')
            for computer in computers:
                agent_data = {
                    'id': computer.id,
                    'hostname': getattr(computer, 'name', 'Unknown'),
                    'status': 'Connected' if getattr(computer, 'connected', False) else 'Disconnected',
                    'last_checkin': getattr(computer, 'lastPollDate', None),
                    'registration_time': getattr(computer, 'dateCreated', None),
                    'os_type': getattr(computer, 'osShortName', 'Unknown'),
                    'computer_name': getattr(computer, 'name', 'Unknown')
                }
                agents_data.append(agent_data)
        
        # Get dropped connections for this instance
        dropped_connections = []
        try:
            if instance.server_type.lower() == 'response':
                events = cb_api._request('GET', '/api/v1/sensor/events?q=license')
                if events and 'results' in events:
                    for event in events['results']:
                        if 'license' in event.get('description', '').lower():
                            dropped_connections.append({
                                'agent_id': event.get('sensor_id'),
                                'agent_hostname': event.get('hostname', 'Unknown'),
                                'timestamp': event.get('timestamp'),
                                'reason': event.get('description', 'License limit reached')
                            })
            else:
                events = cb_api._request('GET', '/api/bit9platform/v1/events?q=licenseLimit')
                if events:
                    for event in events:
                        dropped_connections.append({
                            'agent_id': event.get('agentId'),
                            'agent_hostname': event.get('computerName', 'Unknown'),
                            'timestamp': event.get('timestamp'),
                            'reason': event.get('description', 'License limit reached')
                        })
        except Exception as e:
            current_app.logger.error(f"Error getting dropped connections for {instance.name}: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'instance': {
                'id': instance.id,
                'name': instance.name,
                'server_type': instance.server_type,
                'url': instance.url
            },
            'license': license_data,
            'agents': agents_data,
            'dropped_connections': dropped_connections
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting license information for instance {instance_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve license information: {str(e)}'
        }), 500

@license_bp.route('/dropped', methods=['GET'])
def get_dropped_connections():
    """Get detailed information about all dropped agent connections."""
    try:
        # Get all instances
        instances = CBInstance.query.all()
        all_dropped_connections = []
        
        # Query each instance for dropped connection information
        for instance in instances:
            try:
                # Initialize the CB API client
                cb_api = CBAPIHelper.get_cb_api(instance)
                
                if not cb_api:
                    continue
                
                # Get dropped connections based on server type
                if instance.server_type.lower() == 'response':
                    events = cb_api._request('GET', '/api/v1/sensor/events?q=license')
                    if events and 'results' in events:
                        for event in events['results']:
                            if 'license' in event.get('description', '').lower():
                                # Get additional agent information if available
                                agent_info = {}
                                try:
                                    sensor_id = event.get('sensor_id')
                                    if sensor_id:
                                        sensor = cb_api.select('Sensor', sensor_id)
                                        agent_info = {
                                            'os_type': getattr(sensor, 'os_type', 'Unknown'),
                                            'computer_name': getattr(sensor, 'computer_name', 'Unknown'),
                                            'sensor_version': getattr(sensor, 'build_version_string', 'Unknown')
                                        }
                                except Exception:
                                    pass
                                
                                all_dropped_connections.append({
                                    'instance_id': instance.id,
                                    'instance_name': instance.name,
                                    'instance_type': 'response',
                                    'agent_id': event.get('sensor_id'),
                                    'agent_hostname': event.get('hostname', 'Unknown'),
                                    'timestamp': event.get('timestamp'),
                                    'reason': event.get('description', 'License limit reached'),
                                    'agent_info': agent_info
                                })
                
                else:  # 'protection'
                    events = cb_api._request('GET', '/api/bit9platform/v1/events?q=licenseLimit')
                    if events:
                        for event in events:
                            # Get additional agent information if available
                            agent_info = {}
                            try:
                                agent_id = event.get('agentId')
                                if agent_id:
                                    computer = cb_api.select('Computer', agent_id)
                                    agent_info = {
                                        'os_type': getattr(computer, 'osShortName', 'Unknown'),
                                        'computer_name': getattr(computer, 'name', 'Unknown'),
                                        'sensor_version': getattr(computer, 'agentVersion', 'Unknown')
                                    }
                            except Exception:
                                pass
                            
                            all_dropped_connections.append({
                                'instance_id': instance.id,
                                'instance_name': instance.name,
                                'instance_type': 'protection',
                                'agent_id': event.get('agentId'),
                                'agent_hostname': event.get('computerName', 'Unknown'),
                                'timestamp': event.get('timestamp'),
                                'reason': event.get('description', 'License limit reached'),
                                'agent_info': agent_info
                            })
            
            except Exception as e:
                current_app.logger.error(f"Error getting dropped connections for {instance.name}: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'count': len(all_dropped_connections),
            'dropped_connections': all_dropped_connections
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting dropped connections: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve dropped connections: {str(e)}'
        }), 500 