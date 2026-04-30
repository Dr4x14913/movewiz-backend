import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from captcha.image import ImageCaptcha

from flask import render_template
from .extensions import db
from .models import Event, Participant
from .config import Config

# In-memory captcha store: {token: captcha_text}
_captcha_store = {}


def store_captcha(captcha_text):
    token = uuid.uuid4().hex
    _captcha_store[token] = captcha_text
    return token


def verify_captcha(token, answer):
    stored = _captcha_store.pop(token, None)
    return stored == answer and stored is not None


def send_email(to, subject, html):
    msg = MIMEMultipart('alternative')
    msg['From'] = Config.SMTP_FROM
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))

    try:
        if Config.SMTP_SECURE:
            server = smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT)
        else:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            if Config.SMTP_TLS:
                server.starttls()

        if Config.SMTP_USER and Config.SMTP_PASS:
            server.login(Config.SMTP_USER, Config.SMTP_PASS)

        server.sendmail(Config.SMTP_FROM, to, msg.as_string())
        server.quit()
    except Exception as e:
        print(f'Error sending email: {e}', flush=True)
    else:
        print("Sending email successful", flush=True)


def notify_all(event_id, owner_email, subject, data, template):
    participants = Participant.query.filter_by(
        notifyMe=True, eventId=event_id
    ).all()

    html = render_template(template, **data)

    send_email(owner_email, subject, html)

    for participant in participants:
        send_email(participant.email, subject, html)

    print(f'Emails sent to {len(participants)} participants and owner.', flush=True)


def generate_captcha():
    image = ImageCaptcha(width=150, height=50)
    data = uuid.uuid4().hex[:5].replace('0', '').replace('o', '').replace('1', '').replace('i', '')[:5]
    # Ensure we have 5 characters
    while len(data) < 5:
        data += uuid.uuid4().hex[-1]

    captcha_image = image.generate(data)
    return captcha_image, data
