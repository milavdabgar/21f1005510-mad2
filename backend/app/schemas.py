from marshmallow import fields, validate, pre_load, post_dump
from .models import User, Customer, Professional, Service, ServiceRequest, ProfessionalDocument, Admin
from .extensions import db, ma

class BaseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        sqla_session = db.session
        load_instance = True  # Deserialize to model instances

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = User
        include_fk = True
        load_only = ('password',)
        dump_only = ('created_at', 'updated_at')
    
    id = fields.Integer(dump_only=True)
    email = fields.Email(required=True)
    name = fields.String(required=True)
    phone = fields.String()
    type = fields.String(data_key='user_type', validate=validate.OneOf(['customer', 'professional', 'admin']))
    
    @post_dump
    def remove_none_values(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}

class CustomerSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = Customer
        include_fk = True
        dump_only = ('created_at', 'updated_at')
    
    id = fields.Integer(dump_only=True)
    user = fields.Nested(UserSchema)
    requests = fields.List(fields.Nested(lambda: ServiceRequestSchema(exclude=('customer',))), dump_only=True)

class ServiceSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = Service
        dump_only = ('created_at', 'updated_at')
    
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    type = fields.String(required=True)
    description = fields.String()
    price = fields.Float(required=True)
    time_required = fields.String(required=True)
    professionals = fields.List(fields.Nested(lambda: ProfessionalSchema(exclude=('service',))), dump_only=True)
    requests = fields.List(fields.Nested(lambda: ServiceRequestSchema(exclude=('service',))), dump_only=True)

class ProfessionalDocumentSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = ProfessionalDocument
        include_fk = True
        dump_only = ('created_at', 'updated_at', 'verified_at', 'verified_by', 'verified')
    
    id = fields.Integer(dump_only=True)
    professional_id = fields.Integer(required=True)
    document_type = fields.String(required=True, validate=validate.OneOf(['id_proof', 'certification', 'license']))
    file_path = fields.String(data_key='document_url')
    uploaded_at = fields.DateTime(dump_only=True)
    verified = fields.Boolean(dump_only=True)
    verified_at = fields.DateTime(dump_only=True)
    verified_by = fields.Integer(dump_only=True, allow_none=True)

    @post_dump
    def remove_none_values(self, data, **kwargs):
        """Remove None values from response"""
        return {key: value for key, value in data.items() if value is not None}

class ProfessionalSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = Professional
        include_fk = True
        dump_only = ('created_at', 'updated_at', 'status', 'id_proof_path', 'certification_path', 'rating')
    
    id = fields.Integer(dump_only=True)
    user = fields.Nested(UserSchema)
    service_type = fields.String(required=True)
    experience = fields.String(required=True)
    status = fields.String(validate=validate.OneOf(['registered', 'approved', 'rejected']), dump_only=True)
    available = fields.Boolean(dump_default=True)
    address = fields.String()
    city = fields.String()
    state = fields.String()
    pin_code = fields.String()
    latitude = fields.Float()
    longitude = fields.Float()
    id_proof_path = fields.String(dump_only=True)
    certification_path = fields.String(dump_only=True)
    rating = fields.Float(dump_only=True)
    verified = fields.Boolean(dump_only=True)
    verified_at = fields.DateTime(dump_only=True)
    rejection_reason = fields.String(dump_only=True)
    requests = fields.List(fields.Nested(lambda: ServiceRequestSchema(exclude=('professional',))), dump_only=True)

    @post_dump
    def remove_none_values(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}

class ServiceRequestSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = ServiceRequest
        include_fk = True
    
    id = fields.Integer(dump_only=True)
    customer = fields.Nested(CustomerSchema(exclude=('requests',)))
    service = fields.Nested(ServiceSchema(exclude=('requests',)))
    professional = fields.Nested(ProfessionalSchema(exclude=('requests',)))
    status = fields.String(validate=validate.OneOf(['requested', 'assigned', 'in_progress', 'completed', 'cancelled']))
    request_date = fields.DateTime()
    completion_date = fields.DateTime(attribute='completed_at', dump_only=True)
    rating = fields.Float()
    review = fields.String()
    remarks = fields.String()

    @pre_load
    def process_input(self, data, **kwargs):
        """Convert empty strings to None and handle date fields"""
        processed = {key: value if value != "" else None for key, value in data.items()}
        # Map scheduled_at to request_date if present
        if 'scheduled_at' in processed:
            processed['request_date'] = processed.pop('scheduled_at')
        return processed

class AdminSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = Admin
        include_fk = True
    
    id = fields.Integer(dump_only=True)
    user = fields.Nested(UserSchema)

class BlockUserSchema(ma.Schema):
    """Schema for blocking/unblocking users"""
    reason = fields.String(required=False, allow_none=True)

class ProfessionalListSchema(ma.Schema):
    """Schema for listing professionals"""
    id = fields.Integer()
    email = fields.String()
    name = fields.String()
    phone = fields.String()
    service_type = fields.String()
    experience = fields.String()
    status = fields.String()
    verified = fields.Boolean()
    verified_at = fields.DateTime()
    active = fields.Boolean()

class UserSearchSchema(ma.Schema):
    """Schema for user search results"""
    id = fields.Integer()
    email = fields.String()
    name = fields.String()
    phone = fields.String()
    type = fields.String()
    active = fields.Boolean()
    created_at = fields.DateTime()

class UserSearchParamsSchema(ma.Schema):
    """Schema for user search parameters"""
    q = fields.String(required=False, load_default='')
    type = fields.String(required=False, validate=validate.OneOf(['customer', 'professional', None]))

class CustomerProfileSchema(ma.Schema):
    """Schema for customer profile updates"""
    name = fields.String(required=False)
    phone = fields.String(required=False)
    address = fields.String(required=False)
    pincode = fields.String(required=False)

class CreateServiceRequestSchema(ma.Schema):
    """Schema for creating service requests"""
    service_id = fields.Integer(required=True)
    remarks = fields.String(required=False)

# Initialize schemas with different serialization options
user_schema = UserSchema()
users_schema = UserSchema(many=True)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True)

professional_schema = ProfessionalSchema()
professionals_schema = ProfessionalSchema(many=True)

professional_document_schema = ProfessionalDocumentSchema()
professional_documents_schema = ProfessionalDocumentSchema(many=True)

service_request_schema = ServiceRequestSchema()
service_requests_schema = ServiceRequestSchema(many=True)

admin_schema = AdminSchema()
admins_schema = AdminSchema(many=True)

block_user_schema = BlockUserSchema()
block_users_schema = BlockUserSchema(many=True)

professional_list_schema = ProfessionalListSchema()
professionals_list_schema = ProfessionalListSchema(many=True)

user_search_schema = UserSearchSchema()
users_search_schema = UserSearchSchema(many=True)

user_search_params_schema = UserSearchParamsSchema()

customer_profile_schema = CustomerProfileSchema()
customers_profile_schema = CustomerProfileSchema(many=True)

create_service_request_schema = CreateServiceRequestSchema()
create_service_requests_schema = CreateServiceRequestSchema(many=True)

# Schema with specific field exclusions
service_list_schema = ServiceSchema(exclude=('professionals', 'requests'))
services_list_schema = ServiceSchema(many=True, exclude=('professionals', 'requests'))

professional_list_schema = ProfessionalSchema(exclude=('requests',))
professionals_list_schema = ProfessionalSchema(many=True, exclude=('requests',))

service_request_list_schema = ServiceRequestSchema(exclude=('customer.requests', 'service.requests', 'professional.requests'))
service_requests_list_schema = ServiceRequestSchema(many=True, exclude=('customer.requests', 'service.requests', 'professional.requests'))
