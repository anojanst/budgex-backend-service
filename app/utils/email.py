"""
Email service for sending OTP emails using Resend API
"""

import asyncio
import logging
from typing import Optional

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Resend with API key
resend.api_key = settings.RESEND_API_KEY


async def send_otp_email(email: str, otp_code: str, purpose: str = "authentication") -> bool:
    """
    Send OTP code via email using Resend API

    Args:
        email: Recipient email address
        otp_code: The OTP code to send
        purpose: Purpose of OTP (default: 'authentication' for unified flow)

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        html_body = f"""
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
        """

        logger.info(f"Attempting to send OTP email to {email} via Resend")

        # Resend API call (synchronous SDK, run in thread pool to avoid blocking)
        params = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": "Your BudgeX Verification Code",
            "html": html_body,
        }

        # Run synchronous Resend call in thread pool to avoid blocking event loop
        result = await asyncio.to_thread(resend.Emails.send, params)

        logger.info(f"OTP email sent successfully to {email} via Resend. ID: {result.get('id', 'unknown')}")
        return True

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email to {email} via Resend: {error_msg}")

        # Provide specific error messages for common Resend issues
        if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            logger.error(
                f"Resend API authentication failed. Check:\n"
                f"1. RESEND_API_KEY is set correctly in environment variables\n"
                f"2. API key is valid and not expired\n"
                f"3. Get your API key from https://resend.com/api-keys"
            )
        elif "domain" in error_msg.lower() or "from" in error_msg.lower():
            logger.error(
                f"Resend sender domain issue. Check:\n"
                f"1. RESEND_FROM_EMAIL={settings.RESEND_FROM_EMAIL}\n"
                f"2. Domain is verified in Resend dashboard\n"
                f"3. For testing, use 'onboarding@resend.dev' (default)\n"
                f"4. For production, verify your domain at https://resend.com/domains"
            )
        else:
            logger.error(f"Unexpected error from Resend: {error_msg}")

        return False
