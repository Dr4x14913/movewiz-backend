import json
import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import render_template
from .models import Event, Participant
from .config import Config

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def verify_turnstile(token):
    """Verify a Cloudflare Turnstile response token server-side.

    When no secret key is configured (local development), verification is
    skipped and the request is allowed.
    """
    if not Config.TURNSTILE_SECRET_KEY:
        print('WARNING: TURNSTILE_SECRET_KEY not set - Turnstile verification skipped', flush=True)
        return True
    if not token:
        return False

    payload = urllib.parse.urlencode({
        'secret': Config.TURNSTILE_SECRET_KEY,
        'response': token,
    }).encode()
    try:
        req = urllib.request.Request(
            TURNSTILE_VERIFY_URL,
            data=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        print(f'Error verifying Turnstile token: {e}', flush=True)
        return False

    return bool(result.get('success'))


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


def notify_all(event_id, owner_email, subject, data, template, exclude_id=None):
    participants = Participant.query.filter_by(
        notifyMe=True, eventId=event_id
    )
    if exclude_id is not None:
        participants = participants.filter(Participant.id != exclude_id)
    participants = participants.all()

    html = render_template(template, **data)

    if owner_email:
        send_email(owner_email, subject, html)

    for participant in participants:
        send_email(participant.email, subject, html)

    owner_count = 1 if owner_email else 0
    print(f'Emails sent to {len(participants)} participants and {owner_count} owner.', flush=True)
