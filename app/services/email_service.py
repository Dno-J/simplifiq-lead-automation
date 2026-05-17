import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Dict

from app.config import settings


def smtp_is_configured() -> bool:
    """
    Check whether SMTP credentials are available.

    This lets the app run locally even when email credentials are not configured.
    """
    return all(
        [
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
        ]
    )


def build_email_subject(company_name: str) -> str:
    """
    Build a clear personalized subject line.
    """
    return f"Your Personalized AI Opportunity Audit for {company_name}"


def build_default_email_body(
    full_name: str,
    company_name: str,
) -> str:
    """
    Fallback email body if AI/fallback report generation did not provide one.
    """
    return (
        f"Hi {full_name},\n\n"
        f"Thank you for sharing details about {company_name}.\n\n"
        "We prepared a personalized AI opportunity audit based on your submitted "
        "company details and publicly available website context.\n\n"
        "Please find the report attached.\n\n"
        "Best,\n"
        "SimplifiQ Team"
    )


def send_report_email(
    recipient_email: str,
    full_name: str,
    company_name: str,
    pdf_path: str,
    email_body: str | None = None,
) -> Dict[str, str]:
    """
    Send the generated PDF report to the prospect.

    Returns a status dictionary instead of raising errors directly, so the main
    workflow can update the database cleanly.
    """

    if not smtp_is_configured():
        return {
            "status": "skipped",
            "error": "SMTP credentials are not configured. Email delivery skipped.",
        }

    if not pdf_path or not os.path.exists(pdf_path):
        return {
            "status": "failed",
            "error": f"PDF file not found at path: {pdf_path}",
        }

    subject = build_email_subject(company_name)

    body = email_body or build_default_email_body(
        full_name=full_name,
        company_name=company_name,
    )

    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = recipient_email
        message.set_content(body)

        pdf_file = Path(pdf_path)

        with open(pdf_file, "rb") as file:
            pdf_bytes = file.read()

        message.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=pdf_file.name,
        )

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)

        return {
            "status": "sent",
            "error": "",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }