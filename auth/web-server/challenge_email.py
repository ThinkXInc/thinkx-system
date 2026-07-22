# auth/web-server/challenge_email.py
#
# SMTP delivery adapter for signup and password-reset challenges.

import smtplib
from email.message import EmailMessage

from config import Config


def deliver_challenge_email(*, destination, code, purpose):
    content = f'Purpose: {purpose}\nVerification code: {code}\n'
    deliver_email(destination=destination, content=content)


def deliver_security_notification(*, destination, event):
    content = f'Security notification: {event}\n'
    deliver_email(destination=destination, content=content)


def deliver_email(*, destination, content):
    if not Config.AUTH_SMTP_HOST:
        if Config.ENV in ('development', 'test'):
            return
        raise RuntimeError('AUTH_SMTP_HOST is required outside development/test')

    message = EmailMessage()
    message['From'] = Config.AUTH_EMAIL_SENDER
    message['To'] = destination
    message['Subject'] = 'ThinkX account security'
    message.set_content(content)
    with smtplib.SMTP(Config.AUTH_SMTP_HOST, Config.AUTH_SMTP_PORT) as smtp:
        if Config.AUTH_SMTP_STARTTLS:
            smtp.starttls()
        if Config.AUTH_SMTP_USERNAME:
            smtp.login(Config.AUTH_SMTP_USERNAME, Config.AUTH_SMTP_PASSWORD)
        smtp.send_message(message)
