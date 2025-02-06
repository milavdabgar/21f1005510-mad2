from datetime import datetime, timezone
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

db = db  # assuming db is an instance of SQLAlchemy

def utc_now():
    return datetime.now(timezone.utc)

class BaseModel(db.Model):
    """Base model class with common operations"""
    __abstract__ = True
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self
    
    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def refresh(self):
        """Refresh the instance from the database"""
        db.session.refresh(self)
        return self

class User(BaseModel):
    """Base user model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    type = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    
    # Add discriminator column for polymorphic inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def block(self):
        """Block a user by setting active to False"""
        self.active = False
        db.session.commit()
    
    def unblock(self):
        """Unblock a user by setting active to True"""
        self.active = True
        db.session.commit()

class Customer(User):
    """Customer model - joined table inheritance"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    address = db.Column(db.Text)
    pincode = db.Column(db.String(10))
    status = db.Column(db.String(20), default='registered')  # registered, blocked
    
    __mapper_args__ = {
        'polymorphic_identity': 'customer',
        'inherit_condition': (id == User.id)
    }

class Professional(User):
    """Professional model - joined table inheritance"""
    __tablename__ = 'professionals'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    experience = db.Column(db.String(100))
    service_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, blocked
    id_proof_path = db.Column(db.String(255))
    certification_path = db.Column(db.String(255))
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime(timezone=True))
    verified_by = db.Column(db.Integer, db.ForeignKey('admins.id', use_alter=True, name='fk_professional_verified_by'))
    available = db.Column(db.Boolean, default=True)
    current_request = db.Column(db.Integer, nullable=True)
    pending_assignment = db.Column(db.Integer, nullable=True)
    rejection_reason = db.Column(db.Text)
    
    __mapper_args__ = {
        'polymorphic_identity': 'professional',
        'inherit_condition': (id == User.id)
    }
    
    def approve(self, admin_email):
        """Approve a professional"""
        admin = Admin.query.filter_by(email=admin_email).first()
        if not admin:
            raise ValueError("Invalid admin")
        
        self.status = 'approved'
        self.verified = True
        self.verified_at = utc_now()
        self.verified_by = admin.id
        db.session.commit()
    
    def reject(self, admin_email, reason=None):
        """Reject a professional"""
        admin = Admin.query.filter_by(email=admin_email).first()
        if not admin:
            raise ValueError("Invalid admin")
        
        self.status = 'rejected'
        self.verified = False
        self.verified_at = utc_now()
        self.verified_by = admin.id
        self.rejection_reason = reason
        db.session.commit()

class Admin(User):
    """Admin model - joined table inheritance"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
        'inherit_condition': (id == User.id)
    }

class Service(BaseModel):
    """Service model"""
    __tablename__ = "services"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    def __init__(self, **kwargs):
        # Ensure type is always stored in lowercase
        if 'type' in kwargs:
            kwargs['type'] = kwargs['type'].lower()
        super().__init__(**kwargs)
    
    def update(self, data):
        # Ensure type is always stored in lowercase
        if 'type' in data:
            data['type'] = data['type'].lower()
        return super().update(data)

class ServiceRequest(BaseModel):
    """Service request model"""
    __tablename__ = "service_requests"

    # Status constants
    STATUS_REQUESTED = 'requested'  # Initial state when customer creates request
    STATUS_ASSIGNED = 'assigned'    # Admin has assigned a professional
    STATUS_ACCEPTED = 'accepted'    # Professional has accepted the request
    STATUS_REJECTED = 'rejected'    # Professional has rejected the request
    STATUS_COMPLETED = 'completed'  # Professional has completed the service
    STATUS_CLOSED = 'closed'        # Customer has rated and closed the request

    # Valid status transitions
    STATUS_TRANSITIONS = {
        STATUS_REQUESTED: [STATUS_ASSIGNED],
        STATUS_ASSIGNED: [STATUS_ACCEPTED, STATUS_REJECTED],
        STATUS_ACCEPTED: [STATUS_COMPLETED],
        STATUS_COMPLETED: [STATUS_CLOSED],
        STATUS_REJECTED: [STATUS_ASSIGNED],  # Can be reassigned if rejected
        STATUS_CLOSED: []  # Terminal state
    }

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"))
    request_date = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    completion_date = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), nullable=False, default=STATUS_REQUESTED)
    rating = db.Column(db.Integer)
    remarks = db.Column(db.Text)
    
    # Relationships
    service = db.relationship("Service", backref=db.backref("requests", lazy=True))
    customer = db.relationship("Customer", backref=db.backref("service_requests", lazy=True))
    professional = db.relationship("Professional", backref=db.backref("service_requests", lazy=True))

    def can_transition_to(self, new_status):
        """Check if the status transition is valid"""
        return new_status in self.STATUS_TRANSITIONS.get(self.status, [])

    def update_status(self, new_status):
        """Update the request status if transition is valid"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        
        self.status = new_status
        
        # Set completion date if status is completed
        if new_status == self.STATUS_COMPLETED:
            self.completion_date = utc_now()
        
        db.session.commit()

class ProfessionalDocument(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime(timezone=True))
    verified_by = db.Column(db.Integer, db.ForeignKey('admins.id', use_alter=True, name='fk_document_verified_by'))
    
    # Add relationship to Professional
    professional = db.relationship("Professional", backref=db.backref("documents", lazy=True))
