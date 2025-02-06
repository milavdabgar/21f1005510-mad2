from sqlalchemy import func, case
from datetime import datetime, timedelta, timezone
from ..models import db, Service, Professional, Customer, ServiceRequest
from ..schemas import ServiceSchema, ProfessionalSchema, CustomerSchema

class Statistics:
    """Statistics utility for the application"""

    DEFAULT_DAYS = 30
    DEFAULT_LIMIT = 5
    DEFAULT_TRENDING_DAYS = 7

    @staticmethod
    def _get_date_filter(days=DEFAULT_DAYS):
        """Get date filter for statistics queries"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return ServiceRequest.request_date >= since

    @staticmethod
    def _count_by_status(stats, status):
        """Count requests by status"""
        return sum(stat.count for stat in stats if stat.status == status)

    @staticmethod
    def _get_base_query():
        """Get base query for service request statistics"""
        return db.session.query(
            ServiceRequest.status,
            func.count(ServiceRequest.id).label('count'),
            func.avg(case(
                (ServiceRequest.rating.isnot(None), ServiceRequest.rating),
                else_=None
            )).label('avg_rating'),
            func.count(case(
                (ServiceRequest.rating.isnot(None), 1),
                else_=None
            )).label('rated_count')
        )

    @staticmethod
    def _get_total_requests(date_filter, **filters):
        """Get total requests count with filters"""
        query = db.session.query(func.count(ServiceRequest.id)).filter(date_filter)
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(ServiceRequest, key) == value)
        return query.scalar() or 0

    @staticmethod
    def _calculate_avg_rating(stats):
        """Calculate average rating for completed requests"""
        completed_stats = [s for s in stats if s.status == 'completed' and s.avg_rating is not None]
        if not completed_stats:
            return 0
        return round(sum(s.avg_rating for s in completed_stats) / len(completed_stats), 2)

    @staticmethod
    def get_service_stats(service_id=None, days=DEFAULT_DAYS):
        """Get service statistics"""
        date_filter = Statistics._get_date_filter(days)
        query = Statistics._get_base_query()
        
        if service_id:
            query = query.filter(ServiceRequest.service_id == service_id)
        
        query = query.filter(date_filter)
        stats = query.group_by(ServiceRequest.status).all()
        
        total_requests = Statistics._get_total_requests(date_filter, service_id=service_id)
        
        return {
            'total_requests': total_requests,
            'status_breakdown': {stat.status: stat.count for stat in stats},
            'avg_rating': Statistics._calculate_avg_rating(stats),
            'rated_requests': sum(stat.rated_count for stat in stats),
            'time_period_days': days
        }
    
    @staticmethod
    def get_professional_stats(professional_id=None, days=DEFAULT_DAYS):
        """Get professional statistics"""
        date_filter = Statistics._get_date_filter(days)
        query = Statistics._get_base_query().add_columns(
            func.sum(case(
                (ServiceRequest.status == 'completed', Service.price),
                else_=0
            )).label('earnings')
        ).join(Service)
        
        if professional_id:
            query = query.filter(ServiceRequest.professional_id == professional_id)
        
        query = query.filter(date_filter)
        stats = query.group_by(ServiceRequest.status).all()
        
        total_requests = Statistics._get_total_requests(date_filter, professional_id=professional_id)
        total_professionals = db.session.query(func.count(Professional.id)).scalar() or 0
        
        if not stats:
            return {
                'total_requests': 0,
                'accepted_requests': 0,
                'rejected_requests': 0,
                'completed_requests': 0,
                'rated_requests': 0,
                'avg_rating': 0,
                'total_earnings': 0,
                'completion_rate': 0,
                'time_period_days': days,
                'total': total_professionals
            }
        
        completed_requests = Statistics._count_by_status(stats, 'completed')
        
        return {
            'total_requests': total_requests,
            'accepted_requests': Statistics._count_by_status(stats, 'accepted'),
            'rejected_requests': Statistics._count_by_status(stats, 'cancelled'),
            'completed_requests': completed_requests,
            'rated_requests': sum(stat.rated_count for stat in stats),
            'avg_rating': Statistics._calculate_avg_rating(stats),
            'total_earnings': round(sum(stat.earnings for stat in stats if stat.status == 'completed') or 0, 2),
            'completion_rate': round((completed_requests / total_requests * 100), 2) if total_requests > 0 else 0,
            'time_period_days': days,
            'total': total_professionals
        }

    @staticmethod
    def get_customer_stats(customer_id=None, days=DEFAULT_DAYS):
        """Get customer statistics"""
        date_filter = Statistics._get_date_filter(days)
        query = db.session.query(
            ServiceRequest.status,
            func.count(ServiceRequest.id).label('count'),
            func.sum(case(
                (ServiceRequest.status == 'completed', Service.price),
                else_=0
            )).label('total_spending')
        ).join(Service)
        
        if customer_id:
            query = query.filter(ServiceRequest.customer_id == customer_id)
        
        query = query.filter(date_filter)
        stats = query.group_by(ServiceRequest.status).all()
        
        if not stats:
            return {
                'total_requests': 0,
                'completed_requests': 0,
                'total_spending': 0,
                'status_counts': {},
                'rating_rate': 0,
                'time_period_days': days
            }
        
        total_requests = sum(stat.count for stat in stats)
        completed_requests = Statistics._count_by_status(stats, 'completed')
        
        return {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'total_spending': round(sum(stat.total_spending for stat in stats) or 0, 2),
            'status_counts': {stat.status: stat.count for stat in stats},
            'rating_rate': round((completed_requests / total_requests * 100), 2) if total_requests > 0 else 0,
            'time_period_days': days
        }
    
    @staticmethod
    def get_platform_stats(days=DEFAULT_DAYS):
        """Get overall platform statistics"""
        return {
            'services': Statistics.get_service_stats(days=days),
            'professionals': Statistics.get_professional_stats(days=days),
            'customers': Statistics.get_customer_stats(days=days)
        }
    
    @staticmethod
    def get_trending_services(limit=DEFAULT_LIMIT, days=DEFAULT_TRENDING_DAYS):
        """Get trending services based on request count"""
        date_filter = Statistics._get_date_filter(days)
        
        trending = db.session.query(
            Service,
            func.count(ServiceRequest.id).label('request_count'),
            func.avg(ServiceRequest.rating).label('avg_rating')
        ).join(
            ServiceRequest,
            ServiceRequest.service_id == Service.id
        ).filter(date_filter).group_by(
            Service.id
        ).order_by(
            func.count(ServiceRequest.id).desc()
        ).limit(limit).all()
        
        return [{
            **ServiceSchema().dump(service[0]),
            'request_count': service[1],
            'avg_rating': round(service[2] or 0, 2)
        } for service in trending]
