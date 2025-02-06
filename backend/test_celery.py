from app.jobs import export_service_requests, process_daily_reminders
from app.models import Professional, ServiceRequest, Customer, Service
from app import create_app
from datetime import datetime, timedelta
from app.extensions import db

app = create_app()

# Create all database tables
with app.app_context():
    db.create_all()
    
    # Create test data
    prof = Professional.query.filter_by(name='Alice Brown').first()
    if not prof:
        prof = Professional(
            email='alice@scarlett.com',
            name='Alice Brown',
            phone='0987654321',
            experience='5 years',
            service_type='cleaning',
            verified=True
        )
        db.session.add(prof)
        db.session.commit()
    
    print(f"Found professional: {prof.id} - {prof.name}")
    
    # Create a test customer if doesn't exist
    customer = Customer.query.filter_by(email='test@scarlett.com').first()
    if not customer:
        customer = Customer(
            email='test@scarlett.com',
            name='Test Customer',
            phone='1234567890',
            address='123 Test St',
            pincode='12345'
        )
        db.session.add(customer)
        db.session.commit()
        print(f"Created test customer: {customer.id} - {customer.name}")
    
    # Create a service if it doesn't exist
    service = Service.query.filter_by(name='Deep House Cleaning').first()
    if not service:
        try:
            service = Service(
                name='Deep House Cleaning',
                type='cleaning',
                price=2499.0,
                time_required='4-5 hours',
                description='Professional deep cleaning of entire house including dusting, mopping, and sanitization'
            )
            db.session.add(service)
            db.session.commit()
            print(f"Created service: {service.id} - {service.name}")
        except Exception as e:
            print(f"Error creating service: {str(e)}")
            service = Service.query.filter_by(name='Deep House Cleaning').first()
    
    # Create a pending service request for testing reminders
    pending_request = ServiceRequest.query.filter_by(
        professional_id=prof.id,
        status=ServiceRequest.STATUS_REQUESTED
    ).first()
    
    if not pending_request:
        pending_request = ServiceRequest(
            professional_id=prof.id,
            customer_id=customer.id,
            service_id=service.id,
            status=ServiceRequest.STATUS_REQUESTED,
            request_date=datetime.now()
        )
        db.session.add(pending_request)
        db.session.commit()
        print(f"Created pending request: {pending_request.id}")
    
    # Create a completed request for testing exports
    completed_request = ServiceRequest.query.filter_by(
        professional_id=prof.id,
        status=ServiceRequest.STATUS_COMPLETED
    ).first()
    
    if not completed_request:
        completed_request = ServiceRequest(
            professional_id=prof.id,
            customer_id=customer.id,
            service_id=service.id,
            status=ServiceRequest.STATUS_COMPLETED,
            request_date=datetime.now() - timedelta(days=7),
            completion_date=datetime.now() - timedelta(days=1),
            rating=4,
            remarks="Great service, completed!"
        )
        db.session.add(completed_request)
        db.session.commit()
        print(f"Created completed request: {completed_request.id}")
    
    # Store IDs for use outside app context
    prof_id = prof.id

# Test export functionality
print("\nTesting export_service_requests...")
export_result = export_service_requests.delay(prof_id)
print(f"Export Task ID: {export_result.id}")
print("Export task started")

try:
    output = export_result.get(timeout=30)  # Increased timeout
    print(f"Export task result: {output}")
except Exception as e:
    print(f"Export task error: {str(e)}")
    
# Test daily reminders
print("\nTesting process_daily_reminders...")
reminder_result = process_daily_reminders.delay()
print("Daily reminder task started")

try:
    output = reminder_result.get(timeout=30)  # Increased timeout
    print(f"Reminder task result: {output}")
except Exception as e:
    print(f"Reminder task error: {str(e)}")
