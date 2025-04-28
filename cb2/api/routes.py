from flask import Blueprint, request, jsonify

api_bp = Blueprint('api', __name__)

# Mock data - replace with actual DB/Carbon Black integration
instances = []
agents = []

@api_bp.route('/instances', methods=['GET'])
def get_instances():
    """Return all instances."""
    return jsonify(instances)

@api_bp.route('/instances', methods=['POST'])
def add_instance():
    """Add a new instance."""
    data = request.json
    if not data or not all(key in data for key in ['name', 'url', 'api_key']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    instance_id = len(instances) + 1
    new_instance = {
        'id': instance_id,
        'name': data['name'],
        'url': data['url'],
        'api_key': data['api_key'],
        'status': 'Active'
    }
    instances.append(new_instance)
    return jsonify(new_instance), 201

@api_bp.route('/instances/<int:instance_id>', methods=['DELETE'])
def delete_instance(instance_id):
    """Delete an instance by ID."""
    for i, instance in enumerate(instances):
        if instance['id'] == instance_id:
            del instances[i]
            return jsonify({'message': 'Instance deleted'}), 200
    return jsonify({'error': 'Instance not found'}), 404

@api_bp.route('/agents', methods=['GET'])
def get_agents():
    """Return all agents."""
    return jsonify(agents)

@api_bp.route('/agents/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Return a specific agent by ID."""
    for agent in agents:
        if agent['id'] == agent_id:
            return jsonify(agent)
    return jsonify({'error': 'Agent not found'}), 404

@api_bp.route('/agents/<int:agent_id>/restart', methods=['POST'])
def restart_agent(agent_id):
    """Restart an agent by ID."""
    for agent in agents:
        if agent['id'] == agent_id:
            # In a real application, this would trigger the restart logic
            return jsonify({'message': f'Agent {agent_id} restart initiated'})
    return jsonify({'error': 'Agent not found'}), 404 