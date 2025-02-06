from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Professional, Customer
from app.utils.auth import admin_required, professional_required, customer_required
from app.utils.stats import Statistics
from app.utils.errors import APIError

bp = Blueprint('stats', __name__)

@bp.route('/stats/admin', methods=['GET'])
@jwt_required()
@admin_required()
def admin_stats():
    """Get admin dashboard statistics"""
    service_stats = Statistics.get_service_stats()
    pro_stats = Statistics.get_professional_stats()
    customer_stats = Statistics.get_customer_stats()
    
    return jsonify({
        'services': service_stats,
        'professionals': pro_stats,
        'customers': customer_stats
    })

@bp.route('/stats/professional', methods=['GET'])
@jwt_required()
@professional_required()
def professional_stats():
    """Get professional's personal statistics"""
    professional = Professional.query.filter_by(email=get_jwt_identity()).first_or_404()
    stats = Statistics.get_professional_stats(professional_id=professional.id)
    return jsonify(stats)

@bp.route('/stats/customer', methods=['GET'])
@jwt_required()
@customer_required()
def customer_stats():
    """Get customer's request statistics"""
    customer = Customer.query.filter_by(email=get_jwt_identity()).first_or_404()
    stats = Statistics.get_customer_stats(customer_id=customer.id)
    return jsonify(stats)
