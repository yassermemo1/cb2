from .base import db, ma, BaseModel
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
import json
from datetime import datetime

class CBInstance(db.Model, BaseModel):
    """Model for Carbon Black server instances."""
    __tablename__ = 'instances'

    # Override BaseModel id to match existing schema
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    api_base_url = db.Column(db.Text, nullable=False)
    api_token = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    connection_status = db.Column(db.String(50), default='offline')
    last_checked = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    sensors = db.Column(db.Integer, default=0)
    version = db.Column(db.String(100), default='Unknown')
    connection_message = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    server_type = db.Column(db.String(50), default='response')
    
    # Relationships
    agents = db.relationship('Agent', backref='instance', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CBInstance {self.name}>'
    
    def update_connection_status(self, status, message=''):
        """Update connection status and last connected timestamp."""
        self.connection_status = status
        self.connection_message = message
        self.last_checked = datetime.utcnow()
        db.session.commit()
    
    @property
    def url(self):
        """Get the base URL for compatibility."""
        return self.api_base_url
    
    @url.setter
    def url(self, value):
        """Set the base URL for compatibility."""
        self.api_base_url = value
    
    @property
    def ssl_verify(self):
        """Default to True for SSL verification."""
        return True
    
    def to_credential_dict(self):
        """Convert to a credentials dictionary format for the Carbon Black SDK."""
        return {
            'url': self.api_base_url,
            'token': self.api_token,
            'ssl_verify': True  # Default to True
        }


class Agent(db.Model, BaseModel):
    """Model for Carbon Black agents/sensors."""
    __tablename__ = 'agents'

    # Override BaseModel id to match existing schema
    id = db.Column(db.String(50), primary_key=True)
    device_id = db.Column(db.String(50))
    instance_id = db.Column(db.String(50), db.ForeignKey('instances.id'))
    hostname = db.Column(db.String(255), nullable=False)
    os = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(100), nullable=False)
    last_check_in = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    status = db.Column(db.String(50), default='offline')
    groups = db.Column(db.ARRAY(db.Text), default=[])
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Agent {self.hostname} {self.id}>'
    
    @classmethod
    def get_by_device_id(cls, device_id, instance_id):
        """Get an agent by device ID and instance ID."""
        return cls.query.filter_by(device_id=device_id, instance_id=instance_id).first()
    
    # Map properties for compatibility
    @property
    def device_id(self):
        """Get device_id (which is actually the id field)."""
        return self.id if not getattr(self, '_device_id', None) else self._device_id
    
    @device_id.setter
    def device_id(self, value):
        """Set device_id."""
        self._device_id = value
    
    @property
    def computer_name(self):
        """Computer name is the same as hostname."""
        return self.hostname
    
    @property
    def os_type(self):
        """OS type is the same as os."""
        return self.os
    
    @property
    def os_version(self):
        """OS version is derived from os."""
        return self.os
    
    @property
    def sensor_version(self):
        """Sensor version is the same as version."""
        return self.version
    
    @property
    def network_status(self):
        """Network status is always Normal for now."""
        return 'Normal'
    
    @property
    def group_name(self):
        """Group name is the first group if any."""
        return self.groups[0] if self.groups else ''


# Marshmallow Schemas for serialization/deserialization
class AgentSchema(SQLAlchemyAutoSchema):
    """Schema for Agent model."""
    computer_name = fields.String(dump_only=True)
    os_type = fields.String(dump_only=True)
    os_version = fields.String(dump_only=True)
    sensor_version = fields.String(dump_only=True)
    network_status = fields.String(dump_only=True)
    group_name = fields.Method("get_group_name")
    
    def get_group_name(self, obj):
        return obj.groups[0] if obj.groups else ''
    
    class Meta:
        model = Agent
        include_relationships = True
        load_instance = True


class CBInstanceSchema(SQLAlchemyAutoSchema):
    """Schema for CBInstance model."""
    agents = fields.Nested(AgentSchema, many=True, exclude=('instance_id',))
    server_type = fields.String()
    ssl_verify = fields.Boolean()
    
    class Meta:
        model = CBInstance
        include_relationships = True
        load_instance = True
        exclude = ('api_token',)


# Initialize schemas
cb_instance_schema = CBInstanceSchema()
cb_instances_schema = CBInstanceSchema(many=True)
agent_schema = AgentSchema()
agents_schema = AgentSchema(many=True) 