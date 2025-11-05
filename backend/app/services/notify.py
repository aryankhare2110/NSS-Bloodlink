from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.database import settings

def send_email(to_email: str, subject: str, content: str):
    """
    Send email using SendGrid transactional email API
    """
    if not settings.SENDGRID_API_KEY:
        print("⚠️ No SENDGRID_API_KEY found in settings. Skipping email send.")
        return False

    if not settings.EMAIL_FROM:
        print("⚠️ No EMAIL_FROM found in settings. Skipping email send.")
        return False

    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email} ({response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
