import os
from flask_mail import Message
from app.extensions import mail
from typing import List, Optional

def send_email(to_email: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
    """
    Send email with optional attachments.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        attachments: Optional list of file paths to attach
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender='noreply@scarlett.com'  # Configure this in config.py
        )
        
        if attachments:
            for attachment in attachments:
                if not os.path.exists(attachment):
                    print(f"Warning: Attachment not found: {attachment}")
                    continue
                    
                try:
                    with open(attachment, 'rb') as f:
                        msg.attach(
                            filename=os.path.basename(attachment),
                            content_type='application/octet-stream',
                            data=f.read()
                        )
                except Exception as e:
                    print(f"Error attaching file {attachment}: {e}")
                    continue
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
