import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from backend.core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
        self.from_name = settings.EMAILS_FROM_NAME or "SQL Genius AI"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_user,
                password=self.smtp_password,
            )
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    async def send_verification_email(
        self, 
        email: str, 
        full_name: str, 
        token: str
    ) -> bool:
        verification_url = f"https://app.sqlgenius.ai/verify-email?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - SQL Genius AI</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-top: none; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to SQL Genius AI!</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>Thanks for signing up for SQL Genius AI! Please verify your email address to complete your registration.</p>
                    <p>Click the button below to verify your email:</p>
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                    <p>Or copy and paste this link into your browser:</p>
                    <p><a href="{verification_url}">{verification_url}</a></p>
                    <p>This link will expire in 48 hours.</p>
                    <p>If you didn't create an account with SQL Genius AI, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 SQL Genius AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to SQL Genius AI!
        
        Hi {full_name},
        
        Thanks for signing up for SQL Genius AI! Please verify your email address to complete your registration.
        
        Click this link to verify your email: {verification_url}
        
        This link will expire in 48 hours.
        
        If you didn't create an account with SQL Genius AI, you can safely ignore this email.
        
        © 2024 SQL Genius AI. All rights reserved.
        """
        
        return await self.send_email(
            email,
            "Verify Your Email - SQL Genius AI",
            html_content,
            text_content
        )
    
    async def send_password_reset_email(
        self, 
        email: str, 
        full_name: str, 
        token: str
    ) -> bool:
        reset_url = f"https://app.sqlgenius.ai/reset-password?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password - SQL Genius AI</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-top: none; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reset Your Password</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>You requested to reset your password for your SQL Genius AI account.</p>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_url}" class="button">Reset Password</a>
                    <p>Or copy and paste this link into your browser:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    <p>This link will expire in 48 hours.</p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 SQL Genius AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password - SQL Genius AI
        
        Hi {full_name},
        
        You requested to reset your password for your SQL Genius AI account.
        
        Click this link to reset your password: {reset_url}
        
        This link will expire in 48 hours.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        © 2024 SQL Genius AI. All rights reserved.
        """
        
        return await self.send_email(
            email,
            "Reset Your Password - SQL Genius AI",
            html_content,
            text_content
        )
    
    async def send_welcome_email(self, email: str, full_name: str) -> bool:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to SQL Genius AI</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-top: none; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to SQL Genius AI! 🚀</h1>
                </div>
                <div class="content">
                    <h2>Hi {full_name},</h2>
                    <p>Your email has been verified and your account is now active! Welcome to the future of data analysis.</p>
                    
                    <h3>What you can do now:</h3>
                    <ul>
                        <li>Upload your CSV or Excel files</li>
                        <li>Ask questions in natural language</li>
                        <li>Get instant SQL queries and insights</li>
                        <li>Create beautiful visualizations</li>
                    </ul>
                    
                    <a href="https://app.sqlgenius.ai/dashboard" class="button">Start Analyzing Data</a>
                    
                    <p>Need help getting started? Check out our <a href="https://docs.sqlgenius.ai">documentation</a> or reply to this email.</p>
                    
                    <p>Happy analyzing!</p>
                    <p>The SQL Genius AI Team</p>
                </div>
                <div class="footer">
                    <p>© 2024 SQL Genius AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            email,
            "Welcome to SQL Genius AI! 🚀",
            html_content
        )


email_service = EmailService()