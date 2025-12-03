from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from app.extensions import db
from datetime import datetime, timedelta
import uuid
from flask import current_app

class User(db.Model):
    # Use singular table name 'user' to match foreign key references elsewhere
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.Enum('user', 'Admin'), default='user')
    is_active = db.Column(db.Boolean, default=True)
    
    # Additional fields that were missing
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    is_verified = db.Column(db.Boolean, default=True)
    login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    lock_until = db.Column(db.DateTime)
    last_failed_attempt = db.Column(db.DateTime)
    
    # Relationships
    # Add relationships here if needed
    
    def __init__(self, username, email, password, first_name='', last_name='', role='user'):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        """Create hashed password."""
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:600000',  # Strong hashing with high iteration count
            salt_length=16
        )
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login required methods
    def get_id(self):
        """Return user ID as string for Flask-Login."""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        """Return True if user is authenticated."""
        return True
    
    @property
    def is_anonymous(self):
        """Return True if user is anonymous."""
        return False
    
    def generate_reset_token(self, expires_in=3600):
        """Generate a password reset token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.reset_token = serializer.dumps(self.email, salt='password-reset-salt')
        self.reset_token_expires = datetime.utcnow() + timedelta(seconds=expires_in)
        db.session.commit()
        return self.reset_token
    
    @staticmethod
    def verify_reset_token(token, max_age=3600):
        """Verify password reset token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=max_age
            )
        except:
            return None
        return User.query.filter_by(email=email).first()
    
    def generate_verification_token(self):
        """Generate email verification token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.verification_token = serializer.dumps(
            self.email, 
            salt='email-verification-salt'
        )
        db.session.commit()
        return self.verification_token
    
    @staticmethod
    def verify_verification_token(token, max_age=86400):
        """Verify email verification token."""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='email-verification-salt',
                max_age=max_age
            )
        except:
            return None
        return User.query.filter_by(email=email).first()
    
    def increment_login_attempts(self):
        """Increment failed login attempts and lock account if needed."""
        self.login_attempts += 1
        self.last_failed_attempt = datetime.utcnow()
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.login_attempts >= 5:
            self.is_locked = True
            self.lock_until = datetime.utcnow() + timedelta(minutes=30)
            
        db.session.commit()
    
    def reset_login_attempts(self):
        """Reset failed login attempts."""
        self.login_attempts = 0
        self.last_failed_attempt = None
        self.is_locked = False
        self.lock_until = None
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Return user data as dictionary.
        
        Args:
            include_sensitive (bool): Whether to include sensitive information
        """
        data = {
            'id': self.public_id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name or ''} {self.last_name or ''}".strip() or None,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data.update({
                'is_locked': self.is_locked,
                'login_attempts': self.login_attempts,
                'last_failed_attempt': self.last_failed_attempt.isoformat() if self.last_failed_attempt else None,
                'lock_until': self.lock_until.isoformat() if self.lock_until else None
            })
            
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'