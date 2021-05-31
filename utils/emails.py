import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_email_message(subject, body, to):
    logging.info("Sending email message")

    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    email.content_subtype = "html"  # Main content is now text/html

    email.send()
