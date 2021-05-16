# celery tasks autodiscover working on files with "tasks"
from checksho.celery import app as celery_app


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
