# auth/email_utils.py
import os
import smtplib
from email.message import EmailMessage
from typing import Tuple

SMTP_HOST = os.getenv("SMARTLEND_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMARTLEND_SMTP_PORT", 587))

EMAIL_SENDER = os.getenv("SMARTLEND_EMAIL")              
EMAIL_PASSWORD = os.getenv("SMARTLEND_EMAIL_PASSWORD")    

def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Simple, fail-safe plain-text email sender.
    If EMAIL_SENDER or EMAIL_PASSWORD is not set this will print a message and return.
    This avoids breaking your app if email is not configured.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        #Fail silently (log to console)
        print("Email not sent: SMARTLEND_EMAIL / SMARTLEND_EMAIL_PASSWORD not configured.")
        return

    msg = EmailMessage()
    msg["From"] = f"SmartLend <{EMAIL_SENDER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            if SMTP_PORT == 587:
                server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Failed to send email:", e)


# --- Basic message templates ---
def approval_template(applicant_email: str, admin_email: str, note: str = None) -> Tuple[str, str]:
    subject = "SmartLend — Loan Application Approved"
    body_lines = [
        "Dear Customer,",
        "",
        "Good news! — your loan application has been reviewed and approved.",
        "",
        "What happens next:",
        "- Our loan operations team will contact you within 24 business hours to complete documentation and disbursement.",
        "",
    ]
    if note:
        body_lines += [f"Note from reviewer: {note}", ""]
    body_lines += [
        "If you have any questions, reply to this email or contact support.",
        "",
        "Thank you for choosing SmartLend.",
        "",
        "Sincerely,",
        f"SmartLend Credit Team ({admin_email})"
    ]
    return subject, "\n".join(body_lines)


def rejection_template(applicant_email: str, admin_email: str, note: str = None) -> Tuple[str, str]:
    subject = "SmartLend — Loan Application Outcome"
    body_lines = [
        "Dear Customer,",
        "",
        "Thank you for applying to SmartLend.",
        "After careful review, we are unable to approve your loan application at this time.",
        "",
    ]
    if note:
        body_lines += [f"Reviewer note: {note}", ""]
    body_lines += [
        "This decision does not affect future applications — you may re-apply after addressing the points in the note.",
        "",
        "For clarifications, please contact support.",
        "",
        "Kind regards,",
        f"SmartLend Credit Team ({admin_email})"
    ]
    return subject, "\n".join(body_lines)
