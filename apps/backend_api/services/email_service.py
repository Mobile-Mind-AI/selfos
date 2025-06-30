"""
Email service for sending password reset and other emails.

This service provides:
1. Firebase email integration (primary)
2. SMTP fallback for custom email sending
3. Email template management
4. Development mode with console output
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with Firebase and SMTP fallback"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@selfos.app')
        self.from_name = os.getenv('FROM_NAME', 'SelfOS')
        
    def send_password_reset_email(self, 
                                to_email: str, 
                                reset_link: str, 
                                user_name: Optional[str] = None) -> bool:
        """
        Send password reset email using available email service.
        
        Args:
            to_email: Recipient email address
            reset_link: Password reset URL
            user_name: Optional user display name
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            subject = "Reset Your SelfOS Password"
            
            # Generate email content
            html_content = self._generate_password_reset_html(reset_link, user_name, to_email)
            text_content = self._generate_password_reset_text(reset_link, user_name)
            
            # Always attempt SMTP email sending when credentials are provided
            if self.smtp_username and self.smtp_password:
                return self._send_smtp_email(to_email, subject, text_content, html_content)
            else:
                # No SMTP credentials - show console message with instructions
                return self._send_development_email(to_email, subject, text_content, html_content)
                
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False
    
    def _send_development_email(self, 
                              to_email: str, 
                              subject: str, 
                              text_content: str, 
                              html_content: str) -> bool:
        """Print email to console in development mode"""
        print("\n" + "="*60)
        print("📧 DEVELOPMENT EMAIL SERVICE")
        print("="*60)
        print(f"To: {to_email}")
        print(f"From: {self.from_name} <{self.from_email}>")
        print(f"Subject: {subject}")
        print("-"*60)
        print("EMAIL CONTENT:")
        print(text_content)
        print("="*60)
        print("⚠️  NO SMTP CREDENTIALS CONFIGURED")
        print("📧 To enable real email sending, configure these environment variables:")
        print("   SMTP_USERNAME=your-email@gmail.com")
        print("   SMTP_PASSWORD=your-app-password")
        print("   (See .env file for example configuration)")
        print("="*60 + "\n")
        return True
    
    def _send_smtp_email(self, 
                        to_email: str, 
                        subject: str, 
                        text_content: str, 
                        html_content: str) -> bool:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Attach text and HTML versions
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP email sending failed: {e}")
            return False
    
    def _generate_password_reset_html(self, 
                                    reset_link: str, 
                                    user_name: Optional[str], 
                                    email: str) -> str:
        """Generate HTML email template for password reset"""
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .warning {{ background-color: #FEF3C7; border: 1px solid #F59E0B; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                
                <div class="content">
                    <p>{greeting}</p>
                    
                    <p>We received a request to reset the password for your SelfOS account associated with <strong>{email}</strong>.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset My Password</a>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important Security Information:</strong>
                        <ul>
                            <li>This link expires in 1 hour for your security</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Never share this link with anyone</li>
                        </ul>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 3px; font-family: monospace;">
                        {reset_link}
                    </p>
                    
                    <p>If you're having trouble, contact our support team.</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 SelfOS. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_password_reset_text(self, 
                                    reset_link: str, 
                                    user_name: Optional[str]) -> str:
        """Generate plain text email for password reset"""
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        return f"""
{greeting}

We received a request to reset the password for your SelfOS account.

To reset your password, click the link below or copy and paste it into your browser:

{reset_link}

IMPORTANT SECURITY INFORMATION:
- This link expires in 1 hour for your security
- If you didn't request this reset, please ignore this email
- Never share this link with anyone

If you're having trouble, contact our support team.

Best regards,
The SelfOS Team

---
© 2025 SelfOS. All rights reserved.
This is an automated email. Please do not reply to this message.
        """


# Singleton instance
email_service = EmailService()