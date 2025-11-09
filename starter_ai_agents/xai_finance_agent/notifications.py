"""
Notification System for Price Alerts and Market Events
Supports Email, Slack, and console notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import requests
from datetime import datetime
from agno.utils.log import logger


class NotificationManager:
    """Manages notifications for price alerts and market events"""

    def __init__(
        self,
        email_config: Optional[dict] = None,
        slack_webhook: Optional[str] = None,
        discord_webhook: Optional[str] = None
    ):
        """
        Initialize notification manager

        Args:
            email_config: Dict with 'smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'recipients'
            slack_webhook: Slack webhook URL
            discord_webhook: Discord webhook URL
        """
        self.email_config = email_config
        self.slack_webhook = slack_webhook
        self.discord_webhook = discord_webhook

    def send_email_alert(self, subject: str, message: str, recipients: Optional[List[str]] = None):
        """
        Send email notification

        Args:
            subject: Email subject
            message: Email body
            recipients: List of recipient emails (optional, uses config default)
        """
        if not self.email_config:
            logger.warning("Email configuration not set")
            return False

        try:
            recipients = recipients or self.email_config.get('recipients', [])

            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[IBKR Alert] {subject}"

            # Add timestamp
            body = f"Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{message}"
            msg.attach(MIMEText(body, 'plain'))

            # Connect and send
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_slack_alert(self, message: str, title: Optional[str] = None):
        """
        Send Slack notification

        Args:
            message: Alert message
            title: Optional title for the alert
        """
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return False

        try:
            payload = {
                "text": title or "IBKR Portfolio Alert",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title or "📊 IBKR Portfolio Alert"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }

            response = requests.post(self.slack_webhook, json=payload)
            response.raise_for_status()

            logger.info("Slack notification sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def send_discord_alert(self, message: str, title: Optional[str] = None):
        """
        Send Discord notification

        Args:
            message: Alert message
            title: Optional title for the alert
        """
        if not self.discord_webhook:
            logger.warning("Discord webhook not configured")
            return False

        try:
            payload = {
                "embeds": [{
                    "title": title or "📊 IBKR Portfolio Alert",
                    "description": message,
                    "color": 3447003,  # Blue
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "XAI Finance Agent"
                    }
                }]
            }

            response = requests.post(self.discord_webhook, json=payload)
            response.raise_for_status()

            logger.info("Discord notification sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def send_alert(self, title: str, message: str, channels: Optional[List[str]] = None):
        """
        Send alert through all configured channels

        Args:
            title: Alert title
            message: Alert message
            channels: List of channels to use ['email', 'slack', 'discord'] or None for all
        """
        channels = channels or ['email', 'slack', 'discord']

        results = {}

        if 'email' in channels and self.email_config:
            results['email'] = self.send_email_alert(title, message)

        if 'slack' in channels and self.slack_webhook:
            results['slack'] = self.send_slack_alert(message, title)

        if 'discord' in channels and self.discord_webhook:
            results['discord'] = self.send_discord_alert(message, title)

        # Console output always
        print(f"\n{'='*60}")
        print(f"🔔 ALERT: {title}")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}\n")

        return results


class PriceAlertCondition:
    """Define conditions for price alerts"""

    def __init__(
        self,
        symbol: str,
        condition_type: str,
        threshold: float,
        reference_price: Optional[float] = None
    ):
        """
        Create price alert condition

        Args:
            symbol: Stock symbol
            condition_type: 'above', 'below', 'percent_change_up', 'percent_change_down'
            threshold: Price threshold or percentage
            reference_price: Reference price for percentage calculations
        """
        self.symbol = symbol
        self.condition_type = condition_type
        self.threshold = threshold
        self.reference_price = reference_price
        self.triggered = False

    def check(self, current_price: float) -> bool:
        """
        Check if alert condition is met

        Args:
            current_price: Current market price

        Returns:
            True if condition is met
        """
        if self.condition_type == 'above':
            return current_price > self.threshold

        elif self.condition_type == 'below':
            return current_price < self.threshold

        elif self.condition_type == 'percent_change_up':
            if self.reference_price:
                change = ((current_price - self.reference_price) / self.reference_price) * 100
                return change >= self.threshold
            return False

        elif self.condition_type == 'percent_change_down':
            if self.reference_price:
                change = ((self.reference_price - current_price) / self.reference_price) * 100
                return change >= self.threshold
            return False

        return False

    def get_description(self) -> str:
        """Get human-readable description of the condition"""
        if self.condition_type == 'above':
            return f"{self.symbol} price above ${self.threshold:.2f}"
        elif self.condition_type == 'below':
            return f"{self.symbol} price below ${self.threshold:.2f}"
        elif self.condition_type == 'percent_change_up':
            return f"{self.symbol} up {self.threshold}% from ${self.reference_price:.2f}"
        elif self.condition_type == 'percent_change_down':
            return f"{self.symbol} down {self.threshold}% from ${self.reference_price:.2f}"
        return f"{self.symbol} - {self.condition_type}"
