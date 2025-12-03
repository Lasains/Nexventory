from app.extensions import db

class BaseModel(db.Model):
    """Base model class that provides common functionality"""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def save(self):
        """Save the current instance to the database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self):
        """Delete the current instance from the database"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def get_all(cls):
        """Get all instances of this model"""
        return cls.query.all()

    @classmethod
    def get_by_id(cls, id):
        """Get an instance by its ID"""
        return cls.query.get(id)

    @classmethod
    def get_first(cls):
        """Get the first instance of this model"""
        return cls.query.first()