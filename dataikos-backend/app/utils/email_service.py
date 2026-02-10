import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
import jinja2
import os
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.templates_dir = Path("app/templates/email")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default templates if they don't exist
        self._create_default_templates()
        
        # Setup Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    def _create_default_templates(self):
        """Create default email templates"""
        templates = {
            "appointment_confirmation.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px; }
        .content { background: #f9f9f9; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .appointment-details { background: white; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #4F46E5; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Confirmation de rendez-vous</h1>
        </div>
        <div class="content">
            <p>Bonjour {{ client_name }},</p>
            <p>Votre rendez-vous a été confirmé avec succès.</p>
            
            <div class="appointment-details">
                <h3>Détails du rendez-vous :</h3>
                <p><strong>Service :</strong> {{ service }}</p>
                <p><strong>Date :</strong> {{ appointment_date }}</p>
                <p><strong>Heure :</strong> {{ appointment_time }}</p>
                <p><strong>Prix :</strong> {{ price }} XAF</p>
                {% if notes %}
                <p><strong>Notes :</strong> {{ notes }}</p>
                {% endif %}
            </div>
            
            <p>Un rappel vous sera envoyé 24h avant votre rendez-vous.</p>
            <p>Pour modifier ou annuler votre rendez-vous, veuillez nous contacter.</p>
        </div>
        <div class="footer">
            <p>© 2024 DATAIKÔS. Tous droits réservés.</p>
            <p>Email : contact@dataikos.com | Tél : +237 6XX XX XX XX</p>
        </div>
    </div>
</body>
</html>
            """,
            "appointment_reminder.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #10B981; color: white; padding: 20px; text-align: center; border-radius: 5px; }
        .content { background: #f9f9f9; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .appointment-details { background: white; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #10B981; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
        .reminder-note { background: #FEF3C7; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Rappel de rendez-vous</h1>
        </div>
        <div class="content">
            <p>Bonjour {{ client_name }},</p>
            <p>Ceci est un rappel pour votre rendez-vous prévu demain.</p>
            
            <div class="reminder-note">
                <p>💡 <strong>N'oubliez pas :</strong> Votre rendez-vous est dans 24h.</p>
            </div>
            
            <div class="appointment-details">
                <h3>Détails du rendez-vous :</h3>
                <p><strong>Service :</strong> {{ service }}</p>
                <p><strong>Date :</strong> {{ appointment_date }}</p>
                <p><strong>Heure :</strong> {{ appointment_time }}</p>
                <p><strong>Prix :</strong> {{ price }} XAF</p>
                {% if notes %}
                <p><strong>Notes :</strong> {{ notes }}</p>
                {% endif %}
            </div>
            
            <p>Nous avons hâte de vous rencontrer !</p>
        </div>
        <div class="footer">
            <p>© 2024 DATAIKÔS. Tous droits réservés.</p>
            <p>Email : contact@dataikos.com | Tél : +237 6XX XX XX XX</p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                template_path.write_text(content, encoding='utf-8')
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using SMTP"""
        if not settings.EMAIL_ENABLED:
            logger.warning("Email service is disabled")
            return True  # Return True for testing
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg['To'] = to_email
            
            # Attach both HTML and plain text versions
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Connect to SMTP server
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_appointment_confirmation(
        self,
        to_email: str,
        client_name: str,
        appointment_date: str,
        appointment_time: str,
        service: str,
        price: float,
        notes: Optional[str] = None
    ) -> bool:
        """Send appointment confirmation email"""
        template = self.jinja_env.get_template("appointment_confirmation.html")
        
        html_content = template.render(
            client_name=client_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service=service,
            price=price,
            notes=notes
        )
        
        subject = f"Confirmation de rendez-vous - {service}"
        
        return self.send_email(to_email, subject, html_content)
    
    def send_appointment_reminder(
        self,
        to_email: str,
        client_name: str,
        appointment_date: str,
        appointment_time: str,
        service: str,
        price: float,
        notes: Optional[str] = None
    ) -> bool:
        """Send appointment reminder email"""
        template = self.jinja_env.get_template("appointment_reminder.html")
        
        html_content = template.render(
            client_name=client_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            service=service,
            price=price,
            notes=notes
        )
        
        subject = f"Rappel de rendez-vous - {service}"
        
        return self.send_email(to_email, subject, html_content)

# Create global instance
email_service = EmailService()