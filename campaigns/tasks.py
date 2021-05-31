import logging

from django.utils import timezone

from campaigns import helpers as campaigns_helpers

# celery tasks autodiscover working on files with "tasks"
from checksho.celery import app as celery_app
from users.models import User


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@celery_app.task(bind=True)
def run_scheduled_campaigns(self):
    logging.info("Running celery task run_scheduled_campaigns")

    users = User.objects.filter(is_active=True)
    for user in users:
        now = timezone.now()
        campaigns = user.campaigns.filter(is_active=True, next_run__lte=now)
        if campaigns.exists():
            campaigns_helpers.run_campaigns(user, campaigns)

    logging.info("Running campaign finished")
