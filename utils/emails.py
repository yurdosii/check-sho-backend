from django.conf import settings
from django.core.mail import EmailMultiAlternatives


# TODO - html response in email (щоб гарно було, може якусь табличку)


def send_email_message(subject, body, to):
    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    email.content_subtype = "html"  # Main content is now text/html

    email.send()
