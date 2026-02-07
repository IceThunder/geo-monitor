"""
Email service for sending user notifications.

Uses aiosmtplib for async SMTP email sending.
"""
import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        """Initialize email service with settings."""
        self.smtp_host = getattr(settings, 'SMTP_HOST', None)
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = getattr(settings, 'SMTP_FROM_EMAIL', None)
        self.from_name = getattr(settings, 'SMTP_FROM_NAME', 'GEO Monitor')

        # Check if SMTP is configured
        self.is_configured = all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.from_email
        ])

        if not self.is_configured:
            logger.warning(
                "SMTP not fully configured - emails will not be sent. "
                "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM_EMAIL."
            )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning(f"Skipping email to {to_email} - SMTP not configured")
            return False

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email

            # Add plain text version
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)

            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: str
    ) -> bool:
        """
        Send email verification link.

        Args:
            to_email: Recipient email address
            verification_token: Verification token
            user_name: User's name

        Returns:
            True if email sent successfully
        """
        # Construct verification URL (adjust based on your frontend)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email?token={verification_token}"

        subject = "Verify your email - GEO Monitor"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 30px;
            margin: 20px 0;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1f2937;
            font-size: 24px;
            margin: 0;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: 500;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 14px;
            color: #6b7280;
        }}
        .link {{
            color: #3b82f6;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to GEO Monitor!</h1>
        </div>
        <div class="content">
            <p>Hi {user_name},</p>
            <p>Thank you for signing up for GEO Monitor. Please verify your email address to get started.</p>
            <p style="text-align: center;">
                <a href="{verification_url}" class="button">Verify Email Address</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p class="link">{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
        </div>
        <div class="footer">
            <p>If you didn't create an account, you can safely ignore this email.</p>
            <p>&copy; 2024 GEO Monitor. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Welcome to GEO Monitor!

Hi {user_name},

Thank you for signing up for GEO Monitor. Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

© 2024 GEO Monitor. All rights reserved.
"""

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: str
    ) -> bool:
        """
        Send password reset link.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User's name

        Returns:
            True if email sent successfully
        """
        # Construct reset URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        subject = "Reset your password - GEO Monitor"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 30px;
            margin: 20px 0;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1f2937;
            font-size: 24px;
            margin: 0;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: 500;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 14px;
            color: #6b7280;
        }}
        .link {{
            color: #3b82f6;
            word-break: break-all;
        }}
        .warning {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 12px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hi {user_name},</p>
            <p>We received a request to reset your password for your GEO Monitor account.</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p class="link">{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <div class="warning">
                <strong>Security Notice:</strong> If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            </div>
        </div>
        <div class="footer">
            <p>&copy; 2024 GEO Monitor. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Password Reset Request

Hi {user_name},

We received a request to reset your password for your GEO Monitor account.

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

Security Notice: If you didn't request a password reset, please ignore this email. Your password will remain unchanged.

© 2024 GEO Monitor. All rights reserved.
"""

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_invitation_email(
        self,
        to_email: str,
        inviter_name: str,
        tenant_name: str,
        role: str
    ) -> bool:
        """
        Send team invitation email.

        Args:
            to_email: Recipient email address
            inviter_name: Name of person who sent the invitation
            tenant_name: Name of the tenant/team
            role: Role being assigned

        Returns:
            True if email sent successfully
        """
        # Construct invitation URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        invitation_url = f"{frontend_url}/accept-invitation?email={to_email}"

        subject = f"You've been invited to join {tenant_name} on GEO Monitor"

        # Map role to readable name
        role_names = {
            'owner': 'Owner',
            'admin': 'Administrator',
            'member': 'Member',
            'viewer': 'Viewer'
        }
        role_display = role_names.get(role, role.title())

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 30px;
            margin: 20px 0;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1f2937;
            font-size: 24px;
            margin: 0;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: 500;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 14px;
            color: #6b7280;
        }}
        .link {{
            color: #3b82f6;
            word-break: break-all;
        }}
        .info-box {{
            background-color: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 16px;
            margin: 20px 0;
        }}
        .info-box p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Team Invitation</h1>
        </div>
        <div class="content">
            <p>Hi there,</p>
            <p><strong>{inviter_name}</strong> has invited you to join <strong>{tenant_name}</strong> on GEO Monitor.</p>
            <div class="info-box">
                <p><strong>Team:</strong> {tenant_name}</p>
                <p><strong>Role:</strong> {role_display}</p>
                <p><strong>Invited by:</strong> {inviter_name}</p>
            </div>
            <p>GEO Monitor helps teams monitor and analyze AI model responses about their brands and products.</p>
            <p style="text-align: center;">
                <a href="{invitation_url}" class="button">Accept Invitation</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p class="link">{invitation_url}</p>
        </div>
        <div class="footer">
            <p>If you don't want to join this team, you can safely ignore this email.</p>
            <p>&copy; 2024 GEO Monitor. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Team Invitation

Hi there,

{inviter_name} has invited you to join {tenant_name} on GEO Monitor.

Team: {tenant_name}
Role: {role_display}
Invited by: {inviter_name}

GEO Monitor helps teams monitor and analyze AI model responses about their brands and products.

Accept your invitation by clicking this link:

{invitation_url}

If you don't want to join this team, you can safely ignore this email.

© 2024 GEO Monitor. All rights reserved.
"""

        return await self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
