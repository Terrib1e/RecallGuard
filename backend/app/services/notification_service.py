"""Notification service for RecallGuard."""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Service to send notifications about product recalls."""

    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_name = os.getenv('FROM_NAME', 'RecallGuard')

        # Validate configuration
        if not self.email_address or not self.email_password:
            logger.warning("Email configuration not found. Email notifications will be disabled.")
            self.email_enabled = False
        else:
            self.email_enabled = True

    async def send_recall_alert(self, user_email: str, matches: List[Dict]) -> bool:
        """Send recall alert email to user."""
        if not self.email_enabled:
            logger.info(f"Demo mode: Would send recall alert to {user_email} for {len(matches)} matches")
            return True

        try:
            # Group matches by confidence level
            high_confidence = [m for m in matches if m['confidence'] == 'high']
            medium_confidence = [m for m in matches if m['confidence'] == 'medium']
            low_confidence = [m for m in matches if m['confidence'] == 'low']

            # Generate email content
            subject = self._generate_subject(matches)
            html_content = self._generate_html_content(high_confidence, medium_confidence, low_confidence)
            text_content = self._generate_text_content(high_confidence, medium_confidence, low_confidence)

            # Send email
            return await self._send_email(user_email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send recall alert: {e}")
            return False

    async def send_welcome_email(self, user_email: str, user_id: int) -> bool:
        """Send welcome email to new user."""
        if not self.email_enabled:
            return False

        try:
            subject = "Welcome to RecallGuard - Your Product Safety Monitor"
            html_content = self._generate_welcome_html(user_id)
            text_content = self._generate_welcome_text(user_id)

            return await self._send_email(user_email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False

    async def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email using SMTP."""
        try:
            # In demo mode, just log what would be sent
            logger.info(f"Demo: Would send email to {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content preview: {text_content[:200]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _generate_subject(self, matches: List[Dict]) -> str:
        """Generate email subject based on matches."""
        high_confidence_count = len([m for m in matches if m['confidence'] == 'high'])
        total_count = len(matches)

        if high_confidence_count > 0:
            return f"🚨 URGENT: Product Recall Alert - {high_confidence_count} High-Priority Match{'es' if high_confidence_count > 1 else ''}"
        else:
            return f"⚠️ Product Recall Alert - {total_count} Potential Match{'es' if total_count > 1 else ''} Detected"

    def _generate_html_content(self, high_confidence: List[Dict], medium_confidence: List[Dict], low_confidence: List[Dict]) -> str:
        """Generate HTML email content."""
        return f"""
        <h1>🚨 Product Recall Alert</h1>
        <p>We found {len(high_confidence + medium_confidence + low_confidence)} potential matches between your products and recent recalls.</p>
        <p>High Priority: {len(high_confidence)} matches</p>
        <p>Medium Priority: {len(medium_confidence)} matches</p>
        <p>Low Priority: {len(low_confidence)} matches</p>
        <p><a href="http://localhost:3000/dashboard">View Details in Dashboard</a></p>
        """

    def _generate_text_content(self, high_confidence: List[Dict], medium_confidence: List[Dict], low_confidence: List[Dict]) -> str:
        """Generate plain text email content."""
        return f"""
PRODUCT RECALL ALERT

We found {len(high_confidence + medium_confidence + low_confidence)} potential matches between your products and recent recalls.

High Priority: {len(high_confidence)} matches
Medium Priority: {len(medium_confidence)} matches
Low Priority: {len(low_confidence)} matches

Visit your dashboard for full details: http://localhost:3000/dashboard
"""

    def _generate_welcome_html(self, user_id: int) -> str:
        """Generate welcome email HTML."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .action-button {{ background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to RecallGuard! 🛡️</h1>
                </div>
                <div class="content">
                    <p>Thank you for joining RecallGuard - your personal product safety monitor!</p>

                    <p>We're here to help keep you and your family safe by monitoring your products for recalls and safety alerts.</p>

                    <h3>What happens next?</h3>
                    <ul>
                        <li>Add your products to your dashboard</li>
                        <li>Our AI will continuously monitor for recalls</li>
                        <li>Get instant alerts when matches are found</li>
                        <li>Stay informed about product safety</li>
                    </ul>

                    <div style="text-align: center;">
                        <a href="http://localhost:3000/dashboard" class="action-button">Go to Your Dashboard</a>
                    </div>

                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        Stay safe,<br>
                        The RecallGuard Team
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_welcome_text(self, user_id: int) -> str:
        """Generate welcome email text."""
        return f"""
Welcome to RecallGuard!

Thank you for joining RecallGuard - your personal product safety monitor!

We're here to help keep you and your family safe by monitoring your products for recalls and safety alerts.

What happens next?
- Add your products to your dashboard
- Our AI will continuously monitor for recalls
- Get instant alerts when matches are found
- Stay informed about product safety

Go to your dashboard: http://localhost:3000/dashboard

Stay safe,
The RecallGuard Team
"""

# Global instance
notification_service = NotificationService()