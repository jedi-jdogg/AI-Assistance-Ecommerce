"""Delivery of reports/alerts: Slack incoming webhook, SMTP email, or stdout."""
from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText

import httpx


def send_slack(text: str, webhook: str | None = None) -> bool:
    url = webhook or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return False
    # Slack caps a single message at ~40k chars; chunk on blank lines.
    chunks, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) > 3500:
            chunks.append(cur)
            cur = ""
        cur += para + "\n\n"
    if cur:
        chunks.append(cur)
    for c in chunks:
        httpx.post(url, json={"text": c}, timeout=20).raise_for_status()
    return True


def send_email(subject: str, body: str) -> bool:
    host = os.environ.get("SMTP_HOST")
    to = os.environ.get("ALERT_EMAIL_TO")
    if not host or not to:
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_USER", "agent@lindas.com")
    msg["To"] = to
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587"))) as s:
        s.starttls()
        if os.environ.get("SMTP_USER"):
            s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
        s.send_message(msg)
    return True


def deliver(subject: str, body: str, quiet: bool = False) -> None:
    sent = send_slack(f"*{subject}*\n\n{body}")
    sent = send_email(subject, body) or sent
    if not sent and not quiet:
        print(f"# {subject}\n\n{body}")
