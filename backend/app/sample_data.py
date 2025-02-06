from app.models import db, Service, Professional, Customer, Admin, ServiceRequest
from datetime import datetime, timezone, timedelta

def create_sample_data():
    """Create sample data for testing"""
    try:
        # Create services
        services = [
            # Cleaning Services
            Service(
                name="Deep House Cleaning",
                type="Cleaning",
                description="Professional deep cleaning of entire house including dusting, mopping, and sanitization",
                price=2499.00,
                time_required="4-5 hours"
            ),
            Service(
                name="Bathroom Deep Cleaning",
                type="Cleaning",
                description="Complete bathroom cleaning and sanitization",
                price=899.00,
                time_required="1-2 hours"
            ),
            # Repair Services
            Service(
                name="AC Service & Repair",
                type="Repair",
                description="AC maintenance, service and repair by experts",
                price=499.00,
                time_required="1-2 hours"
            ),
            Service(
                name="RO Water Purifier Repair",
                type="Repair",
                description="RO repair, service and filter replacement",
                price=399.00,
                time_required="1 hour"
            ),
            # Plumbing Services
            Service(
                name="Plumbing Repair",
                type="Plumbing",
                description="Fix leaks, blockages and all plumbing issues",
                price=299.00,
                time_required="1 hour"
            ),
            Service(
                name="Basin & Sink Work",
                type="Plumbing",
                description="Installation and repair of basins and sinks",
                price=399.00,
                time_required="1-2 hours"
            ),
            # Electrical Services
            Service(
                name="Electrical Wiring",
                type="Electrical",
                description="New wiring installation and repair",
                price=399.00,
                time_required="1-2 hours"
            ),
            Service(
                name="Switch & Socket Repair",
                type="Electrical",
                description="Repair and replacement of switches and sockets",
                price=199.00,
                time_required="30-60 mins"
            ),
            # Painting Services
            Service(
                name="Full Home Painting",
                type="Painting",
                description="Complete home painting with premium paints",
                price=15000.00,
                time_required="3-4 days"
            ),
            Service(
                name="Wall Painting",
                type="Painting",
                description="Individual wall painting and touch-ups",
                price=2999.00,
                time_required="4-5 hours"
            )
        ]
        db.session.add_all(services)
        db.session.commit()

        # Create admin
        admin = Admin(
            email="admin@scarlett.com",
            name="Admin User",
            phone="1234567890"
        )
        admin.set_password("Seagate@123")
        db.session.add(admin)
        db.session.commit()

        # Create customers
        customers = [
            Customer(
                email="customer1@scarlett.com",
                name="John Doe",
                phone="9876543210",
                address="123 Main St",
                pincode="400001"
            ),
            Customer(
                email="customer2@scarlett.com",
                name="Jane Smith",
                phone="9876543211",
                address="456 Oak St",
                pincode="400002"
            )
        ]
        for customer in customers:
            customer.set_password("Seagate@123")
        db.session.add_all(customers)
        db.session.commit()

        # Create professionals
        professionals = [
            Professional(
                email="pro1@scarlett.com",
                name="Bob Wilson",
                phone="9876543212",
                experience="5",
                service_type="Cleaning",
                status="approved",
                verified=True
            ),
            Professional(
                email="pro2@scarlett.com",
                name="Alice Brown",
                phone="9876543213",
                experience="8",
                service_type="Plumbing",
                status="approved",
                verified=True
            ),
            Professional(
                email="pro3@scarlett.com",
                name="Charlie Davis",
                phone="9876543214",
                experience="6",
                service_type="Electrical",
                status="approved",
                verified=True
            ),
            Professional(
                email="pro4@scarlett.com",
                name="David Miller",
                phone="9876543215",
                experience="10",
                service_type="Painting",
                status="approved",
                verified=True
            )
        ]
        for professional in professionals:
            professional.set_password("Seagate@123")
        db.session.add_all(professionals)
        db.session.commit()

        return True

    except Exception as e:
        print(f"Error creating sample data: {e}")
        return False
