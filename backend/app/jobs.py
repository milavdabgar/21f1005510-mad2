import os
import csv
from datetime import datetime, timedelta
from app.celery_app import celery
from app.models import Professional, ServiceRequest, Customer, Service
from app.extensions import db
from flask_mail import Message
from app.email import send_email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List
from app import create_app

# Constants
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

class FlaskTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with create_app().app_context():
            return self.run(*args, **kwargs)

@celery.task(base=FlaskTask)
def export_service_requests(professional_id: int) -> str:
    """Export completed service requests for a professional."""
    try:
        # Get professional's completed service requests
        requests = ServiceRequest.query.filter_by(
            professional_id=professional_id,
            status=ServiceRequest.STATUS_COMPLETED
        ).all()
        
        if not requests:
            return "No completed service requests found"
        
        # Create CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"service_requests_{professional_id}_{timestamp}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Service ID', 'Customer ID', 'Professional ID',
                'Date of Request', 'Completion Date', 'Service Type',
                'Status', 'Rating', 'Remarks'
            ])
            
            for req in requests:
                writer.writerow([
                    req.id, req.customer_id, req.professional_id,
                    req.request_date, req.completion_date,
                    req.service.type if req.service else 'Unknown',
                    req.status, req.rating, req.remarks
                ])
        
        # Send email with attachment
        professional = Professional.query.get(professional_id)
        if professional and professional.email:
            subject = "Service Requests Export"
            body = "Please find attached your service requests export."
            send_email(professional.email, subject, body, [filepath])
        
        return f"Export completed: {filename}"
    except Exception as e:
        return f"Export failed: {str(e)}"

@celery.task(base=FlaskTask)
def process_daily_reminders():
    """Send daily reminders to professionals with pending service requests."""
    try:
        # Get all professionals with pending requests
        professionals = Professional.query.join(ServiceRequest).filter(
            ServiceRequest.status == ServiceRequest.STATUS_REQUESTED
        ).distinct().all()
        
        reminders_sent = 0
        for prof in professionals:
            pending_count = ServiceRequest.query.filter_by(
                professional_id=prof.id,
                status=ServiceRequest.STATUS_REQUESTED
            ).count()
            
            if pending_count > 0:
                subject = "Pending Service Requests Reminder"
                body = f"Hello {prof.name},\n\nYou have {pending_count} pending service requests that require your attention."
                send_email(prof.email, subject, body)
                reminders_sent += 1
        
        return f"Daily reminders sent to {reminders_sent} professionals"
    except Exception as e:
        return f"Error sending daily reminders: {str(e)}"

@celery.task(base=FlaskTask)
def process_monthly_reports():
    """Process monthly activity reports."""
    try:
        # Get last month's date range
        today = datetime.now()
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        # Get all customers with activity last month
        customers = Customer.query.join(ServiceRequest).filter(
            ServiceRequest.request_date >= last_month_start,
            ServiceRequest.request_date <= last_month_end
        ).distinct().all()
        
        reports_sent = 0
        for customer in customers:
            # Get customer's service requests from last month
            requests = ServiceRequest.query.filter(
                ServiceRequest.customer_id == customer.id,
                ServiceRequest.request_date >= last_month_start,
                ServiceRequest.request_date <= last_month_end
            ).all()
            
            if requests:
                # Generate report
                subject = f"Monthly Activity Report - {last_month_start.strftime('%B %Y')}"
                body = f"""Hello {customer.name},

Here's your activity summary for {last_month_start.strftime('%B %Y')}:
Total Services Requested: {len(requests)}
Completed Services: {sum(1 for r in requests if r.status == ServiceRequest.STATUS_COMPLETED)}
Average Rating: {sum(r.rating or 0 for r in requests)/len(requests):.1f}

Thank you for using our services!
"""
                send_email(customer.email, subject, body)
                reports_sent += 1
        
        return f"Monthly reports sent to {reports_sent} customers"
    except Exception as e:
        return f"Error processing monthly reports: {str(e)}"

# Schedule daily reminders for 6 PM every day
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=18, minute=0),  # 6 PM daily
        process_daily_reminders.s(),
        name='daily-reminders'
    )

    # Schedule monthly reports for 1st day of every month at 1 AM
    sender.add_periodic_task(
        crontab(day_of_month=1, hour=1, minute=0),
        process_monthly_reports.s(),
        name='monthly-reports'
    )
