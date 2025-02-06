import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from app.jobs import (
    send_email, get_html_report, get_active_user,
    process_daily_reminders, send_professional_reminder,
    process_monthly_reports, send_customer_report,
    export_service_requests
)
from app.models import ServiceRequest, Professional, Customer, Service

@pytest.fixture
def mock_smtp(monkeypatch):
    smtp_mock = MagicMock()
    smtp_instance = MagicMock()
    smtp_mock.return_value = smtp_instance
    smtp_instance.__enter__.return_value = smtp_instance
    monkeypatch.setattr('smtplib.SMTP', smtp_mock)
    return smtp_mock

@pytest.fixture
def service_requests(session, approved_professional, customer, service):
    """Create test service requests"""
    requests = [
        ServiceRequest(
            professional_id=approved_professional.id,
            customer_id=customer.id,
            service_id=service.id,
            status='requested',
            request_date=datetime.now(timezone.utc) + timedelta(days=1)
        ),
        ServiceRequest(
            professional_id=approved_professional.id,
            customer_id=customer.id,
            service_id=service.id,
            status='completed',
            request_date=datetime.now(timezone.utc) - timedelta(days=1)
        )
    ]
    for req in requests:
        session.add(req)
    session.commit()
    return requests

def test_send_email(mock_smtp):
    """Test email sending functionality"""
    to_email = "test@scarlett.com"
    subject = "Test Subject"
    html_body = "<p>Test Body</p>"
    
    send_email(to_email, subject, html_body)
    
    mock_smtp.assert_called_once_with('localhost')
    mock_smtp.return_value.send_message.assert_called_once()

def test_get_html_report(service_requests):
    """Test HTML report generation"""
    title = "Test Report"
    html = get_html_report(service_requests, title)
    
    assert title in html
    assert "Total Requests: 2" in html
    assert "Completed: 1" in html
    assert "Pending: 1" in html

def test_get_active_user(session, approved_professional):
    """Test getting active user"""
    user = get_active_user(Professional, approved_professional.id)
    assert user == approved_professional
    
    # Test with non-existent user
    user = get_active_user(Professional, 9999)
    assert user is None

@patch('app.jobs.send_professional_reminder.delay')
def test_process_daily_reminders(mock_send_reminder, session, approved_professional):
    """Test processing of daily reminders"""
    process_daily_reminders()
    mock_send_reminder.assert_called_once_with(approved_professional.id)

@patch('app.jobs.send_email')
def test_send_professional_reminder(mock_send_email, session, approved_professional, service_requests, mock_smtp):
    """Test sending professional reminder"""
    send_professional_reminder(approved_professional.id)
    mock_send_email.assert_called_once()
    
    # Verify email content
    call_args = mock_send_email.call_args[0]
    assert approved_professional.email == call_args[0]
    assert "Pending Service Requests" in call_args[1]

@patch('app.jobs.send_customer_report.delay')
def test_process_monthly_reports(mock_send_report, session, customer):
    """Test processing of monthly reports"""
    process_monthly_reports()
    mock_send_report.assert_called_once_with(customer.id)

@patch('app.jobs.send_email')
def test_send_customer_report(mock_send_email, session, customer, service_requests, mock_smtp):
    """Test sending customer report"""
    send_customer_report(customer.id)
    mock_send_email.assert_called_once()
    
    # Verify email content
    call_args = mock_send_email.call_args[0]
    assert customer.email == call_args[0]
    assert "Monthly Activity Report" in call_args[1]

def test_export_service_requests(session, approved_professional, service_requests, tmp_path, mock_smtp):
    """Test service request export"""
    with patch('app.jobs.EXPORT_DIR', str(tmp_path)):
        result = export_service_requests(approved_professional.id)
        
        assert result['status'] == 'success'
        assert result['count'] == len(service_requests)
        
        # Verify email was sent
        mock_smtp.return_value.send_message.assert_called_once()
