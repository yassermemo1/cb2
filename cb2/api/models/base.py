from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy()
ma = Marshmallow()

class BaseModel:
    """Base model with common fields and methods."""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        """Save the instance to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the instance from the database."""
        db.session.delete(self)
        db.session.commit()
        return self

    @classmethod
    def get_by_id(cls, id):
        """Get an instance by ID."""
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """Get all instances."""
        return cls.query.all() 