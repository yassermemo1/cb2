from flask import Blueprint, jsonify, request, current_app
from werkzeug.exceptions import Forbidden
from sqlalchemy import desc
from ..models import db
from ..models.audit_log import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

@audit_bp.route('/', methods=['GET'])
def get_audit_logs():
    """Get audit logs with filtering options."""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # Default to 50 logs per page
        max_per_page = 100  # Limit to 100 logs per page max
        per_page = min(per_page, max_per_page)
        
        # Filter parameters
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        resource_type = request.args.get('resource_type')
        resource_id = request.args.get('resource_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        # Build the query
        query = AuditLog.query
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        # Order by timestamp (newest first)
        query = query.order_by(desc(AuditLog.timestamp))
        
        # Paginate the results
        logs_page = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert logs to dicts
        logs = []
        for log in logs_page.items:
            log_dict = log.to_dict()
            log_dict['username'] = 'System'  # Default username since we don't have users
            logs.append(log_dict)
        
        return jsonify({
            'status': 'success',
            'data': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': logs_page.pages,
                'total_items': logs_page.total
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving audit logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving audit logs: {str(e)}'
        }), 500

@audit_bp.route('/actions', methods=['GET'])
def get_audit_actions():
    """Get a list of all possible audit actions."""
    try:
        # Get all distinct actions from the database
        actions = db.session.query(AuditLog.action).distinct().all()
        action_list = [action[0] for action in actions]
        
        return jsonify({
            'status': 'success',
            'data': action_list
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving audit actions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving audit actions: {str(e)}'
        }), 500

@audit_bp.route('/resource-types', methods=['GET'])
def get_resource_types():
    """Get a list of all resource types in audit logs."""
    try:
        # Get all distinct resource types from the database
        resource_types = db.session.query(AuditLog.resource_type).distinct().all()
        resource_type_list = [rt[0] for rt in resource_types if rt[0]]  # Filter out None values
        
        return jsonify({
            'status': 'success',
            'data': resource_type_list
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving resource types: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving resource types: {str(e)}'
        }), 500

@audit_bp.route('/stats', methods=['GET'])
def get_audit_stats():
    """Get statistics about audit logs."""
    try:
        # Total number of logs
        total_logs = AuditLog.query.count()
        
        # Recent activity (logs from the last 24 hours)
        from datetime import datetime, timedelta
        recent_logs = AuditLog.query.filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Most common actions
        from sqlalchemy import func
        action_counts = db.session.query(
            AuditLog.action,
            func.count(AuditLog.id).label('action_count')
        ).group_by(AuditLog.action)\
            .order_by(desc('action_count'))\
            .limit(5)\
            .all()
        
        common_actions = [
            {'action': action, 'count': count}
            for action, count in action_counts
        ]
        
        # Most affected resources
        resource_counts = db.session.query(
            AuditLog.resource_type,
            func.count(AuditLog.id).label('resource_count')
        ).filter(AuditLog.resource_type.isnot(None))\
            .group_by(AuditLog.resource_type)\
            .order_by(desc('resource_count'))\
            .limit(5)\
            .all()
        
        common_resources = [
            {'resource_type': resource_type, 'count': count}
            for resource_type, count in resource_counts
        ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_logs': total_logs,
                'recent_logs': recent_logs,
                'common_actions': common_actions,
                'common_resources': common_resources
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error retrieving audit stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving audit stats: {str(e)}'
        }), 500 