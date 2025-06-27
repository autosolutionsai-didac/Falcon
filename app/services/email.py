import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """Send email using SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add plain text part
        msg.attach(MIMEText(body, 'plain'))
        
        # Add HTML part if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # Send email in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_smtp_email, msg)
        
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


def _send_smtp_email(msg: MIMEMultipart):
    """Synchronous SMTP email sending."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_verification_email(email: str, full_name: str) -> bool:
    """Send email verification link."""
    # Create verification token
    token = create_access_token(
        data={"email": email, "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    
    verification_url = f"{settings.CORS_ORIGINS[0]}/verify-email/{token}"
    
    subject = "Verify your Falcon account"
    
    body = f"""
Hello {full_name},

Welcome to Falcon! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The Falcon Team
"""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a365d; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f7f7f7; padding: 30px; margin-top: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Falcon</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>Thank you for registering with Falcon. Please verify your email address to complete your registration.</p>
            <a href="{verification_url}" class="button">Verify Email Address</a>
            <p style="margin-top: 30px; font-size: 14px; color: #666;">
                This link will expire in 24 hours. If you didn't create this account, please ignore this email.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return await send_email(email, subject, body, html_body)


async def send_password_reset_email(email: str, full_name: str) -> bool:
    """Send password reset link."""
    # Create reset token
    token = create_access_token(
        data={"email": email, "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )
    
    reset_url = f"{settings.CORS_ORIGINS[0]}/reset-password/{token}"
    
    subject = "Reset your Falcon password"
    
    body = f"""
Hello {full_name},

You requested to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email. Your password won't be changed.

Best regards,
The Falcon Team
"""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1a365d; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f7f7f7; padding: 30px; margin-top: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <h2>Hello {full_name},</h2>
            <p>You requested to reset your password for your Falcon account.</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <div class="warning">
                <strong>Security Notice:</strong> This link will expire in 1 hour. If you didn't request this password reset, please ignore this email and your password will remain unchanged.
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return await send_email(email, subject, body, html_body)


async def send_case_completion_email(
    to_email: str,
    user_name: str,
    case_id: int,
    summary: str,
    confidence_level: str,
    is_error: bool = False
) -> bool:
    """Send notification when case analysis is complete."""
    if is_error:
        subject = f"Falcon Alert: Analysis Failed for Case #{case_id}"
        body = f"""
Hello {user_name},

Unfortunately, the forensic analysis for Case #{case_id} has encountered an error:

Error: {summary}

Our team has been notified and will investigate this issue. Please try again later or contact support if the problem persists.

Best regards,
The Falcon Team
"""
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #d32f2f; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f7f7f7; padding: 30px; margin-top: 20px; }}
        .error-box {{ background-color: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Analysis Failed</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Unfortunately, the forensic analysis for Case #{case_id} has encountered an error:</p>
            <div class="error-box">
                <strong>Error:</strong> {summary}
            </div>
            <p>Our team has been notified and will investigate this issue. Please try again later or contact support if the problem persists.</p>
        </div>
    </div>
</body>
</html>
"""
    else:
        subject = f"Falcon Analysis Complete: Case #{case_id}"
        body = f"""
Hello {user_name},

The comprehensive forensic analysis for Case #{case_id} has been completed successfully.

Overall Confidence Level: {confidence_level}

Analysis Summary:
{summary}

Available Reports:
- Executive Summary Report
- Confidence Analysis Report  
- Detailed Forensic Report

You can access all reports and detailed findings by logging into your Falcon dashboard.

Best regards,
The Falcon Team
"""
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f7f7f7; padding: 30px; margin-top: 20px; }}
        .summary-box {{ background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        .reports-list {{ background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Forensic Analysis Complete</h1>
        </div>
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>The comprehensive forensic analysis for Case #{case_id} has been completed successfully.</p>
            
            <div class="summary-box">
                <h3>Analysis Summary</h3>
                <p><strong>Overall Confidence Level:</strong> {confidence_level}</p>
                <p>{summary}</p>
            </div>
            
            <div class="reports-list">
                <h4>Available Reports:</h4>
                <ul>
                    <li>Executive Summary Report</li>
                    <li>Confidence Analysis Report</li>
                    <li>Detailed Forensic Report</li>
                </ul>
            </div>
            
            <center>
                <a href="{settings.CORS_ORIGINS[0]}/cases/{case_id}" class="button">View Full Report</a>
            </center>
            
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                This analysis was performed using Falcon v3.0 with Revolutionary Anti-Hallucination Architecture.
                All findings include confidence levels and are traceable to source documentation.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return await send_email(to_email, subject, body, html_body)