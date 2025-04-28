from flask import Blueprint, request, jsonify, current_app, Response
from ..models import db, Agent, CBInstance, agent_schema, agents_schema
from ..utils import CBAPIHelper
import logging
from sqlalchemy import or_, and_
import csv
import io

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint
agent_bp = Blueprint('agent', __name__, url_prefix='/api/agents')

@agent_bp.route('/', methods=['GET'])
def get_agents():
    """Get all agents, with optional filtering."""
    try:
        # Get query parameters
        instance_id = request.args.get('instance_id')
        status = request.args.get('status')
        os_type = request.args.get('os_type')
        hostname = request.args.get('hostname')
        computer_name = request.args.get('computer_name')
        
        # Build query
        query = Agent.query
        
        # Apply filters
        if instance_id:
            query = query.filter(Agent.instance_id == instance_id)
        
        if status:
            query = query.filter(Agent.status == status)
        
        if os_type:
            query = query.filter(Agent.os_type == os_type)
        
        if hostname:
            query = query.filter(Agent.hostname.ilike(f"%{hostname}%"))
            
        if computer_name:
            query = query.filter(Agent.computer_name.ilike(f"%{computer_name}%"))
        
        # Execute query
        agents = query.all()
        result = []
        
        for agent in agents:
            result.append({
                'id': agent.id,
                'instance_id': agent.instance_id,
                'hostname': agent.hostname,
                'computer_name': agent.computer_name,
                'status': agent.status,
                'os_type': agent.os_type,
                'os_version': agent.os_version,
                'sensor_version': agent.sensor_version,
                'last_checkin': agent.last_checkin.isoformat() if agent.last_checkin else None,
                'network_status': agent.network_status,
                'group_name': agent.group_name
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving agents: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving agents: {str(e)}"
        }), 500

@agent_bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a specific agent."""
    try:
        agent = Agent.query.get(agent_id)
        
        if not agent:
            return jsonify({
                'success': False,
                'message': f"Agent {agent_id} not found"
            }), 404
        
        result = {
            'id': agent.id,
            'instance_id': agent.instance_id,
            'hostname': agent.hostname,
            'computer_name': agent.computer_name,
            'status': agent.status,
            'os_type': agent.os_type,
            'os_version': agent.os_version,
            'sensor_version': agent.sensor_version,
            'last_checkin': agent.last_checkin.isoformat() if agent.last_checkin else None,
            'network_status': agent.network_status,
            'group_name': agent.group_name
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving agent {agent_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving agent: {str(e)}"
        }), 500

@agent_bp.route('/search', methods=['GET'])
def search_agents():
    """Search for agents based on various criteria."""
    try:
        # Get query parameters
        query = request.args.get('q', '')
        instance_id = request.args.get('instance_id')
        
        if not query:
            return jsonify({
                'success': False,
                'message': "Search query is required"
            }), 400
        
        # Build search query
        search = Agent.query
        
        # Filter by instance if specified
        if instance_id:
            search = search.filter(Agent.instance_id == instance_id)
        
        # Search in multiple fields
        search = search.filter(
            or_(
                Agent.hostname.ilike(f"%{query}%"),
                Agent.computer_name.ilike(f"%{query}%"),
                Agent.os_type.ilike(f"%{query}%"),
                Agent.os_version.ilike(f"%{query}%"),
                Agent.sensor_version.ilike(f"%{query}%"),
                Agent.group_name.ilike(f"%{query}%")
            )
        )
        
        # Execute query
        agents = search.all()
        result = []
        
        for agent in agents:
            result.append({
                'id': agent.id,
                'instance_id': agent.instance_id,
                'hostname': agent.hostname,
                'computer_name': agent.computer_name,
                'status': agent.status,
                'os_type': agent.os_type,
                'os_version': agent.os_version,
                'sensor_version': agent.sensor_version,
                'last_checkin': agent.last_checkin.isoformat() if agent.last_checkin else None,
                'network_status': agent.network_status,
                'group_name': agent.group_name
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        current_app.logger.error(f"Error searching agents: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error searching agents: {str(e)}"
        }), 500

@agent_bp.route('/stats', methods=['GET'])
def get_agent_stats():
    """Get agent statistics."""
    try:
        instance_id = request.args.get('instance_id')
        
        # Build query
        query = Agent.query
        
        # Filter by instance if specified
        if instance_id:
            query = query.filter(Agent.instance_id == instance_id)
        
        # Total agents
        total_count = query.count()
        
        # Status counts
        online_count = query.filter(Agent.status == 'Online').count()
        offline_count = query.filter(Agent.status == 'Offline').count()
        
        # OS type counts
        windows_count = query.filter(Agent.os_type.ilike('%windows%')).count()
        mac_count = query.filter(Agent.os_type.ilike('%mac%')).count()
        linux_count = query.filter(Agent.os_type.ilike('%linux%')).count()
        
        # Network status counts
        normal_count = query.filter(Agent.network_status == 'Normal').count()
        isolated_count = query.filter(Agent.network_status == 'Isolated').count()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total_count,
                'status': {
                    'online': online_count,
                    'offline': offline_count
                },
                'os_type': {
                    'windows': windows_count,
                    'mac': mac_count,
                    'linux': linux_count
                },
                'network_status': {
                    'normal': normal_count,
                    'isolated': isolated_count
                }
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving agent statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving agent statistics: {str(e)}"
        }), 500

@agent_bp.route('/export-csv', methods=['GET'])
def export_agents_to_csv():
    """Export agents to a CSV file."""
    try:
        # Get query parameters for filtering
        instance_id = request.args.get('instance_id')
        status = request.args.get('status')
        os_type = request.args.get('os_type')
        hostname = request.args.get('hostname')
        computer_name = request.args.get('computer_name')
        
        # Build query
        query = Agent.query
        
        # Apply filters
        if instance_id:
            query = query.filter(Agent.instance_id == instance_id)
        
        if status:
            query = query.filter(Agent.status == status)
        
        if os_type:
            query = query.filter(Agent.os_type == os_type)
        
        if hostname:
            query = query.filter(Agent.hostname.ilike(f"%{hostname}%"))
            
        if computer_name:
            query = query.filter(Agent.computer_name.ilike(f"%{computer_name}%"))
        
        # Execute query
        agents = query.all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'instance_id', 'hostname', 'computer_name', 'status', 
            'os_type', 'os_version', 'sensor_version', 'last_checkin',
            'network_status', 'group_name'
        ])
        writer.writeheader()
        
        for agent in agents:
            writer.writerow({
                'id': agent.id,
                'instance_id': agent.instance_id,
                'hostname': agent.hostname,
                'computer_name': agent.computer_name,
                'status': agent.status,
                'os_type': agent.os_type,
                'os_version': agent.os_version,
                'sensor_version': agent.sensor_version,
                'last_checkin': agent.last_checkin.isoformat() if agent.last_checkin else None,
                'network_status': agent.network_status,
                'group_name': agent.group_name
            })
        
        # Create filename with filters if applicable
        filename = 'cb_agents'
        if instance_id:
            filename += f'_{instance_id}'
        filename += '.csv'
        
        # Create response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
        return response
    except Exception as e:
        current_app.logger.error(f"Error exporting agents: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error exporting agents: {str(e)}"
        }), 500

@agent_bp.route('/sync-all', methods=['POST'])
def sync_all_agents():
    """Sync agents from all active Carbon Black instances."""
    instances = CBInstance.query.filter_by(is_active=True).all()
    
    results = []
    total_count = 0
    
    for instance in instances:
        logger.info(f"Syncing agents for instance: {instance.name}")
        success, count, message = CBAPIHelper.sync_agents(instance)
        results.append({
            'instance_id': instance.id,
            'instance_name': instance.name,
            'success': success,
            'count': count,
            'message': message
        })
        
        if success:
            total_count += count
    
    return jsonify({
        'status': 'success',
        'total_count': total_count,
        'results': results
    }), 200

@agent_bp.route('/search', methods=['POST'])
def search_agents_post():
    """Search for agents based on criteria."""
    data = request.get_json() or {}
    
    # Start with base query
    query = Agent.query
    
    # Apply filters
    if 'hostname' in data:
        query = query.filter(Agent.hostname.ilike(f"%{data['hostname']}%"))
    
    if 'status' in data:
        query = query.filter(Agent.status == data['status'])
    
    if 'os' in data:
        query = query.filter(Agent.os.ilike(f"%{data['os']}%"))
    
    if 'instance_id' in data:
        query = query.filter(Agent.instance_id == data['instance_id'])
    
    if 'version' in data:
        query = query.filter(Agent.version.ilike(f"%{data['version']}%"))
    
    # Advanced search with multiple fields
    if 'search' in data:
        search_term = f"%{data['search']}%"
        query = query.filter(
            or_(
                Agent.hostname.ilike(search_term),
                Agent.os.ilike(search_term),
                Agent.version.ilike(search_term),
                Agent.status.ilike(search_term)
            )
        )
    
    # Execute query
    agents = query.all()
    
    # Get available filter options
    filter_options = get_filter_options()
    
    return jsonify({
        'status': 'success',
        'count': len(agents),
        'filter_options': filter_options,
        'data': agents_schema.dump(agents)
    }), 200

def get_filter_options(instance_id=None):
    """Get available filter options for dropdowns."""
    query = Agent.query
    
    # Filter by instance if provided
    if instance_id:
        query = query.filter_by(instance_id=instance_id)
    
    # Get distinct values for filters
    statuses = db.session.query(Agent.status).distinct().all()
    os_types = db.session.query(Agent.os).distinct().all()
    versions = db.session.query(Agent.version).distinct().all()
    
    # Get instances for dropdown
    instances = db.session.query(
        CBInstance.id, CBInstance.name
    ).filter(CBInstance.is_active == True).all()
    
    return {
        'statuses': [status[0] for status in statuses if status[0]],
        'os_types': [os_type[0] for os_type in os_types if os_type[0]],
        'versions': [version[0] for version in versions if version[0]],
        'instances': [{'id': inst[0], 'name': inst[1]} for inst in instances]
    } 