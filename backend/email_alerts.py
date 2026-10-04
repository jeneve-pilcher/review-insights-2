import smtplib
from email.mime.text import MIMEText

import config


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends a plain-text email via SMTP if configured. If SMTP env vars
    aren't set, logs the email instead of failing - useful for local dev
    before you've wired up a real provider (SendGrid, Postmark, AWS SES's
    SMTP interface, etc. all work here since this is just standard SMTP).
    """
    host = config.SMTP_HOST
    if not host:
        print(f"[email-alert] (SMTP not configured) To: {to_email} | Subject: {subject}\n{body}")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.SMTP_FROM or config.SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, config.SMTP_PORT) as server:
            server.starttls()
            if config.SMTP_USER and config.SMTP_PASSWORD:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"[email-alert] Failed to send to {to_email}: {exc}")
        return False
