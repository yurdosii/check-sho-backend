from django.conf import settings
from django.core.mail import EmailMessage

# TODO - html response in email (щоб гарно було, може якусь табличку)


def send_email_message(subject, body, to):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )

    email.send()
