"""Statistics API endpoints."""
from flask import Blueprint, jsonify
from app.models import Service, Professional, Customer, ServiceRequest
from app.decorators import admin_required
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('statistics', __name__)

@bp.route('/api/stats/admin', methods=['GET'])
@admin_required
def get_admin_stats():
    """Get admin dashboard statistics."""
    try:
        # Service Statistics
        service_stats = {
            'total': Service.query.count(),
            'pending_requests': ServiceRequest.query.filter_by(status='requested').count(),
            'by_type': get_service_distribution(),
            'recent_requests': get_recent_requests()
        }

        # Professional Statistics
        professional_stats = {
            'total': Professional.query.count(),
            'active': Professional.query.filter_by(status='approved', available=True).count(),
            'pending': get_pending_professionals(),
            'status_distribution': get_professional_status_distribution()
        }

        # Customer Statistics
        customer_stats = {
            'total': Customer.query.count(),
            'active': Customer.query.filter_by(active=True).count()
        }

        return jsonify({
            'services': service_stats,
            'professionals': professional_stats,
            'customers': customer_stats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_service_distribution():
    """Get distribution of services by type."""
    services = Service.query.with_entities(
        Service.type,
        func.count(Service.id).label('count')
    ).group_by(Service.type).all()
    
    return {service.type: service.count for service in services}

def get_professional_status_distribution():
    """Get distribution of professionals by status."""
    professionals = Professional.query.with_entities(
        Professional.status,
        func.count(Professional.id).label('count')
    ).group_by(Professional.status).all()
    
    return {pro.status: pro.count for pro in professionals}

def get_recent_requests(limit=5):
    """Get recent service requests."""
    requests = ServiceRequest.query\
        .join(Service)\
        .join(Customer)\
        .order_by(ServiceRequest.request_date.desc())\
        .limit(limit)\
        .all()
    
    return [{
        'id': req.id,
        'service_name': req.service.name,
        'customer_name': req.customer.name,
        'date': req.request_date.isoformat(),
        'status': req.status
    } for req in requests]

def get_pending_professionals(limit=5):
    """Get pending professional approvals."""
    professionals = Professional.query\
        .filter_by(status='pending')\
        .order_by(Professional.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [{
        'id': pro.id,
        'name': pro.name,
        'service_type': pro.service_type,
        'experience': pro.experience
    } for pro in professionals]
