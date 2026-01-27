"""
Email service for sending OTP emails
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from typing import Optional


# Email configuration
# Note: fastapi-mail ConnectionConfig parameters
# For port 587 (TLS): MAIL_STARTTLS=True, MAIL_SSL_TLS=False
# For port 465 (SSL): MAIL_STARTTLS=False, MAIL_SSL_TLS=True
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=settings.SMTP_TLS and settings.SMTP_PORT == 587,  # STARTTLS for port 587
    MAIL_SSL_TLS=settings.SMTP_TLS and settings.SMTP_PORT == 465,  # SSL for port 465
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fastmail = FastMail(conf)


async def send_otp_email(email: str, otp_code: str, purpose: str = "registration") -> bool:
    """
    Send OTP code via email
    
    Args:
        email: Recipient email address
        otp_code: The OTP code to send
        purpose: Purpose of OTP ('registration' or 'login')
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        subject = "Your BudgeX Verification Code" if purpose == "registration" else "Your BudgeX Login Code"
        
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=f"""
            <html>
            <body>
                <h2>Your BudgeX Verification Code</h2>
                <p>Your verification code is:</p>
                <h1 style="color: #6366F1; font-size: 32px; letter-spacing: 4px;">{otp_code}</h1>
                <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">This is an automated message from BudgeX.</p>
            </body>
            </html>
            """,
            subtype="html",
        )
        
        await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

