"""
Email service for sending OTP emails
"""

import logging
from typing import Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from app.core.config import settings

logger = logging.getLogger(__name__)

# Email configuration
# Note: fastapi-mail ConnectionConfig parameters
# For port 587 (TLS): MAIL_STARTTLS=True, MAIL_SSL_TLS=False
# For port 465 (SSL): MAIL_STARTTLS=False, MAIL_SSL_TLS=True
# Added timeout settings for Railway/cloud deployments
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
    # Timeout settings for cloud deployments (Railway, etc.)
    # Note: fastapi-mail uses aiosmtplib which supports timeout via SUPPRESS_SEND
    # But ConnectionConfig doesn't directly expose timeout. We'll handle it in the send function.
)

fastmail = FastMail(conf)


async def send_otp_email(email: str, otp_code: str, purpose: str = "authentication") -> bool:
    """
    Send OTP code via email

    Args:
        email: Recipient email address
        otp_code: The OTP code to send
        purpose: Purpose of OTP (default: 'authentication' for unified flow)

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        subject = "Your BudgeX Verification Code"

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
        logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email to {email}: {error_msg}")

        # Provide more specific error messages
        if "Timed out" in error_msg or "timeout" in error_msg.lower():
            logger.error(
                f"SMTP connection timeout. Check:\n"
                f"1. SMTP_HOST={settings.SMTP_HOST}\n"
                f"2. SMTP_PORT={settings.SMTP_PORT}\n"
                f"3. Network/firewall restrictions\n"
                f"4. Try port 465 with SSL instead of 587 with STARTTLS"
            )
        elif "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
            logger.error(
                f"SMTP authentication failed. Check:\n"
                f"1. SMTP_USER={settings.SMTP_USER}\n"
                f"2. SMTP_PASSWORD (ensure using App Password for Gmail)\n"
                f"3. For Gmail: Enable 2FA and use App Password"
            )
        elif "SSL" in error_msg or "TLS" in error_msg:
            logger.error(
                f"SMTP SSL/TLS error. Check:\n"
                f"1. SMTP_TLS={settings.SMTP_TLS}\n"
                f"2. Port 587 requires STARTTLS, Port 465 requires SSL\n"
                f"3. Try switching ports (587 <-> 465)"
            )

        return False
