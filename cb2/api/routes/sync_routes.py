from flask import Blueprint, request, jsonify
from ..models import db, CBInstance, Agent
from ..utils.cb_api_helper import CBAPIHelper

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

@sync_bp.route('/agent/<agent_id>', methods=['POST'])
def sync_single_agent(agent_id):
    """Sync a single agent from a Carbon Black instance."""
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
            'message': 'Carbon Black instance not found'
        }), 404
    
    # Check if agent exists
    agent = Agent.query.filter_by(device_id=agent_id, cb_instance_id=instance_id).first()
    
    if not agent:
        return jsonify({
            'success': False,
            'message': f'Agent with ID {agent_id} not found in instance {instance.name}'
        }), 404
    
    # Initialize the CB API client
    cb_api = CBAPIHelper.get_cb_api(instance)
    
    if not cb_api:
        return jsonify({
            'success': False,
            'message': 'Failed to initialize CB API'
        }), 500
    
    try:
        # Get the latest agent data based on server type
        if instance.server_type.lower() == 'response':
            # For Carbon Black Response (EDR)
            device = cb_api.select('Sensor', agent_id)
            
            # Update agent data
            agent.hostname = getattr(device, 'hostname', '')
            agent.computer_name = getattr(device, 'computer_name', '')
            agent.status = getattr(device, 'status', '')
            agent.last_checkin = getattr(device, 'last_checkin_time', None)
            agent.os_type = getattr(device, 'os_type', '')
            agent.os_version = getattr(device, 'os_environment_display_string', '')
            agent.sensor_version = getattr(device, 'build_version_string', '')
            agent.network_status = 'Isolated' if getattr(device, 'network_isolation_enabled', False) else 'Normal'
            agent.group_name = getattr(device, 'group_name', '')
            
        else:  # 'protection'
            # For Carbon Black Protection (App Control)
            device = cb_api.select('Computer', agent_id)
            
            # Update agent data
            agent.hostname = getattr(device, 'name', '')
            agent.computer_name = getattr(device, 'computerName', '')
            agent.status = 'Connected' if getattr(device, 'connected', False) else 'Disconnected'
            agent.last_checkin = getattr(device, 'dateLastRegistered', None)
            agent.os_type = getattr(device, 'osShortName', '')
            agent.os_version = getattr(device, 'osName', '')
            agent.sensor_version = getattr(device, 'agentVersion', '')
            agent.network_status = 'Normal'  # Not applicable in Protection
            agent.group_name = getattr(device, 'policyName', '')
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Agent {agent.hostname} successfully synced',
            'data': {
                'id': agent.id,
                'device_id': agent.device_id,
                'hostname': agent.hostname,
                'status': agent.status,
                'os_type': agent.os_type,
                'sensor_version': agent.sensor_version,
                'last_checkin': agent.last_checkin
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error syncing agent: {str(e)}'
        }), 500 