from datetime import datetime
from . import db

class AuditLog(db.Model):
    """Model for tracking actions and system events."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # Optional, no foreign key
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    resource_type = db.Column(db.String(64), index=True)
    resource_id = db.Column(db.String(64), index=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))  # IPv6 can be up to 45 chars
    user_agent = db.Column(db.String(256))
    status = db.Column(db.String(32), default="success")  # success, failure, etc.
    
    def __init__(self, user_id=None, action=None, resource_type=None, resource_id=None, 
                 details=None, ip_address=None, user_agent=None, status="success"):
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = status
    
    @classmethod
    def log_action(cls, action, resource_type=None, resource_id=None, 
                  details=None, ip_address=None, user_agent=None, status="success", user_id=None):
        """Create and save a new audit log entry."""
        log = cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def log_system_action(cls, action, details=None, status="success"):
        """Log system-level actions."""
        return cls.log_action(
            action=action,
            resource_type='system',
            details=details,
            status=status
        )
    
    def to_dict(self):
        """Convert audit log to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status
        }
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action}>'


class AuditActions:
    """Constants for audit log actions to ensure consistency."""
    
    # Instance actions
    INSTANCE_CREATE = "instance_create"
    INSTANCE_UPDATE = "instance_update"
    INSTANCE_DELETE = "instance_delete"
    INSTANCE_TEST = "instance_test"
    
    # Agent actions
    AGENT_SYNC = "agent_sync"
    AGENT_ISOLATE = "agent_isolate"
    AGENT_UNISOLATE = "agent_unisolate"
    AGENT_UPGRADE = "agent_upgrade"
    
    # Service actions
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    SERVICE_RESTART = "service_restart"
    
    # Watchlist actions
    WATCHLIST_CREATE = "watchlist_create"
    WATCHLIST_UPDATE = "watchlist_update"
    WATCHLIST_DELETE = "watchlist_delete"
    
    # Policy actions
    POLICY_CREATE = "policy_create"
    POLICY_UPDATE = "policy_update"
    POLICY_DELETE = "policy_delete"
    
    # System actions
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    
    # License actions
    LICENSE_CHECK = "license_check"
    LICENSE_EXPIRED = "license_expired"
    LICENSE_UPDATED = "license_updated" 