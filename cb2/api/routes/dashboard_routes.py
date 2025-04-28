from flask import Blueprint, request, jsonify
from ..models import db, CBInstance, Agent
from ..utils.cb_api_helper import CBAPIHelper
from datetime import datetime, timedelta
import random  # Temporary for mock data

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/data', methods=['GET'])
def get_dashboard_data():
    """Get dashboard data based on the provided filters."""
    # Get filter parameters
    instance_id = request.args.get('instance', 'all')
    os_type = request.args.get('os_type', 'all')
    status = request.args.get('status', 'all')
    time_period = request.args.get('time_period', '24h')
    
    # In a real implementation, fetch actual data from the database
    # and calculate statistics based on the filters
    # For demonstration, generate mock data
    
    # Convert time period to days for filtering
    days = {
        '24h': 1,
        '7d': 7,
        '30d': 30,
        '90d': 90
    }.get(time_period, 1)
    
    # Calculate statistics based on filters
    stats = calculate_dashboard_stats(instance_id, os_type, status, days)
    
    # Generate chart data
    charts = generate_chart_data(instance_id, os_type, status, days)
    
    # Generate alert and event data
    alerts = generate_alert_data(instance_id, days)
    events = generate_event_data(instance_id, days)
    
    # Get instances for filter dropdown
    instances = get_instances()
    
    # Calculate trends (percentage change from previous period)
    trends = calculate_trends(instance_id, os_type, status, days)
    
    return jsonify({
        'stats': stats,
        'charts': charts,
        'alerts': alerts,
        'events': events,
        'instances': instances,
        'trends': trends
    })

def calculate_dashboard_stats(instance_id, os_type, status, days):
    """Calculate dashboard statistics."""
    # In a real implementation, query the database
    # For demonstration, return mock data
    
    # Get total agents count
    total_agents = Agent.query.count()
    
    # Get connected agents count
    connected_agents = Agent.query.filter(Agent.status == 'Connected').count()
    
    # Get disconnected agents count
    disconnected_agents = Agent.query.filter(Agent.status == 'Disconnected').count()
    
    # Get isolated agents count
    isolated_agents = Agent.query.filter(Agent.network_status == 'Isolated').count()
    
    # Get instances count
    total_instances = CBInstance.query.count()
    
    # Get response instances count
    response_instances = CBInstance.query.filter(CBInstance.server_type == 'response').count()
    
    # Get protection instances count
    protection_instances = CBInstance.query.filter(CBInstance.server_type == 'protection').count()
    
    # Get active instances count
    active_instances = CBInstance.query.filter(CBInstance.is_active == True).count()
    
    # Get active response instances count
    active_response_instances = CBInstance.query.filter(
        CBInstance.is_active == True,
        CBInstance.server_type == 'response'
    ).count()
    
    # Get active protection instances count
    active_protection_instances = CBInstance.query.filter(
        CBInstance.is_active == True,
        CBInstance.server_type == 'protection'
    ).count()
    
    # Determine system health based on various factors
    system_health = determine_system_health()
    
    return {
        'totalAgents': total_agents,
        'connectedAgents': connected_agents,
        'disconnectedAgents': disconnected_agents,
        'isolatedAgents': isolated_agents,
        'totalInstances': total_instances,
        'responseInstances': response_instances,
        'protectionInstances': protection_instances,
        'activeInstances': active_instances,
        'activeResponseInstances': active_response_instances,
        'activeProtectionInstances': active_protection_instances,
        'systemHealth': system_health
    }

def determine_system_health():
    """Determine overall system health status."""
    # In a real implementation, this would check various factors like:
    # - Connection status of instances
    # - Agent health metrics
    # - Server resource utilization
    # - Recent alerts and their severity
    
    # For demonstration, return random status
    statuses = ['Healthy', 'Warning', 'Critical']
    weights = [0.7, 0.2, 0.1]  # More likely to be healthy
    
    return {
        'status': random.choices(statuses, weights=weights, k=1)[0]
    }

def generate_chart_data(instance_id, os_type, status, days):
    """Generate chart data for the dashboard."""
    # In a real implementation, query the database
    # For demonstration, return mock data
    
    # Generate date labels for the time period
    date_labels = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        date_labels.append(date.strftime('%Y-%m-%d'))
    
    # Agent status over time
    agent_status = {
        'labels': date_labels,
        'connected': [random.randint(80, 100) for _ in range(days)],
        'disconnected': [random.randint(10, 20) for _ in range(days)],
        'isolated': [random.randint(0, 5) for _ in range(days)]
    }
    
    # OS type distribution
    os_type_data = {
        'windows': random.randint(80, 120),
        'mac': random.randint(20, 40),
        'linux': random.randint(10, 30),
        'other': random.randint(0, 5)
    }
    
    # Sensor version distribution
    sensor_versions = ['7.0.0', '7.1.0', '7.2.0', '7.3.0', '7.4.0']
    sensor_version_data = {
        'labels': sensor_versions,
        'counts': [random.randint(10, 50) for _ in range(len(sensor_versions))]
    }
    
    # Instance status distribution
    instance_status_data = {
        'connected': random.randint(5, 10),
        'connectionError': random.randint(0, 2),
        'authFailed': random.randint(0, 1),
        'apiError': random.randint(0, 1),
        'unknown': random.randint(0, 1)
    }
    
    return {
        'agentStatus': agent_status,
        'osType': os_type_data,
        'sensorVersion': sensor_version_data,
        'instanceStatus': instance_status_data
    }

def generate_alert_data(instance_id, days):
    """Generate alert data for the dashboard."""
    # In a real implementation, query the database
    # For demonstration, return mock data
    
    alert_types = [
        'Agent disconnected',
        'Malware detected',
        'Suspicious activity',
        'Network connection blocked',
        'Authentication failure',
        'Process terminated'
    ]
    
    severities = ['critical', 'warning', 'info']
    severity_weights = [0.2, 0.3, 0.5]
    
    instance_names = [
        'CB Response Server',
        'CB Protection Server',
        'CB Cloud Instance'
    ]
    
    # Generate random alerts
    num_alerts = random.randint(3, 8)
    alerts = []
    
    for i in range(num_alerts):
        # Random timestamp within the time period
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, days-1), 
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        alert = {
            'message': f"{random.choice(alert_types)} on device {random.randint(1000, 9999)}",
            'severity': random.choices(severities, weights=severity_weights, k=1)[0],
            'timestamp': timestamp.isoformat(),
            'instance': random.choice(instance_names)
        }
        
        alerts.append(alert)
    
    # Sort by timestamp (newest first)
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return alerts

def generate_event_data(instance_id, days):
    """Generate event data for the dashboard."""
    # In a real implementation, query the database
    # For demonstration, return mock data
    
    event_types = [
        'Agent registered',
        'Agent updated',
        'Agent synced',
        'Policy updated',
        'Scan completed',
        'Instance restarted',
        'Configuration changed',
        'User login'
    ]
    
    instance_names = [
        'CB Response Server',
        'CB Protection Server',
        'CB Cloud Instance'
    ]
    
    # Generate random events
    num_events = random.randint(5, 10)
    events = []
    
    for i in range(num_events):
        # Random timestamp within the time period
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, days-1), 
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        event = {
            'message': f"{random.choice(event_types)}",
            'timestamp': timestamp.isoformat(),
            'instance': random.choice(instance_names)
        }
        
        events.append(event)
    
    # Sort by timestamp (newest first)
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return events

def get_instances():
    """Get all instances for filter dropdown."""
    instances = CBInstance.query.all()
    return [{'id': instance.id, 'name': instance.name} for instance in instances]

def calculate_trends(instance_id, os_type, status, days):
    """Calculate trend percentages."""
    # In a real implementation, compare current period with previous period
    # For demonstration, return random trends
    
    return {
        'totalAgents': random.randint(-10, 20),
        'connectedAgents': random.randint(-5, 15),
        'disconnectedAgents': random.randint(-15, 5),
        'isolatedAgents': random.randint(-5, 5)
    } 