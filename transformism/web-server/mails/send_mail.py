from flask import Flask, render_template

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'ENV',
    'HOST_URL',
    'MAIL_SENDER',
    'MAIL_REPLY_TO',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_DEFAULT_REGION'
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

ENV = Config.ENV
HOST_URL = Config.HOST_URL
SENDER = Config.MAIL_SENDER
REPLY_TO = Config.MAIL_REPLY_TO

# Set logger
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.DEBUG)
from libcommon.color import *

# Local
from libcommon.locale import Locale
LOCALES_ROOT = Config.LOCALES_ROOT
EMAILS_LOCALE_FILE_PATH = f'{LOCALES_ROOT}/emails.json'
locale = Locale([EMAILS_LOCALE_FILE_PATH])

# Email
from libcommon.mail import Mail, MailSendError
mail = Mail(
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_DEFAULT_REGION)

# NOTE:
# In main.py, template root folder is added as:
# app.jinja_loader = ChoiceLoader([
#     FileSystemLoader(['views/templates', 'mails/templates']),
# ])
# then, proj_root/mails/templates/html/page.html can be specified as 'html/page.html'

TEST_SEND = False

if ENV != 'production' and TEST_SEND:
    # Basic test
    try:
        response = mail.send(
            sender=SENDER,
            reply_to=REPLY_TO,
            recipient='kaz@thinkxinc.com',
            subject='Mail Client Test 1',
            text='This is a SES mail client test.',
            html='<body>This is a SES mail client test.</body>',
        )
        logger.info(f"Send Mail Test: success - {response}")
    except Exception as e:
        logger.error(red(f"Send Mail Test: An error occurred: {e}"))
    
    
    # Test outside flask (celery worker)
    try:
        flask_app = Flask(__name__, template_folder='templates')
        with flask_app.app_context(): # celery worker process needs context
            html = render_template(
                'html/inquiry_confirm.html',
                body1="This is a sending email test.",
                name="Bill Gates",
                email="bill@microsoft.com",
                phone="",
                job_title="CEO",
                company_name="Microsoft",
                message="Hello",
                body2="Test")
            response = mail.send(
                sender=SENDER,
                reply_to=REPLY_TO,
                recipient='kaz@thinkxinc.com',
                subject='Mail Client Test 2 (https://thinkxinc.com)',
                text='This is a SES mail client test.',
                html=html
            )
    except Exception as e:
        logger.error(red(f"Send Mail Test: An error occurred: {e}"))

# send mails
def send_inquiry_confirm_email(
    lang,
    name: str,
    email: str,
    phone: str,
    job_title: str,
    company_name: str,
    message: str):

    subject = locale.get('inquiry_confirm_subject', lang)
    html_content = render_template(
        'html/inquiry_confirm.html',
        host_url=HOST_URL,
        body1=locale.get('inquiry_confirm_body_1', lang),
        name=name,
        name_label=locale.get('name_label', lang),
        email=email,
        email_label=locale.get('email_label', lang),
        phone=phone,
        phone_label=locale.get('phone_label', lang),
        job_title=job_title,
        job_title_label=locale.get('job_title_label', lang),
        company_name=company_name,
        company_name_label=locale.get('company_name_label', lang),
        message=message,
        message_label=locale.get('message_label', lang),
        body2=locale.get('inquiry_confirm_body_2', lang),
        support_email="inquiry@thinkxinc.com"
    )
    text_content = render_template(
        'plain/inquiry_confirm.txt',
        host_url=HOST_URL,
        body1=locale.get('inquiry_confirm_body_1', lang),
        name=name,
        name_label=locale.get('name_label', lang),
        email=email,
        email_label=locale.get('email_label', lang),
        phone=phone,
        phone_label=locale.get('phone_label', lang),
        job_title=job_title,
        job_title_label=locale.get('job_title_label', lang),
        company_name=company_name,
        company_name_label=locale.get('company_name_label', lang),
        message=message,
        message_label=locale.get('message_label', lang),
        support_email="inquiry@thinkxinc.com"
    )

    try:
        mail.send(
            sender=SENDER,
            reply_to=REPLY_TO,
            recipient=email,
            subject=subject,
            text=text_content,
            html=html_content,
        )
        logger.info(light_green(f'Email "{subject}" sent to {email}'))
    except MailSendError as e:
        raise MailSendError