import os

from celery import Celery, Task
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "checksho.settings")


class CheckShoTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True


app = Celery("checksho", task_cls=CheckShoTask)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from campaigns.tasks import run_scheduled_campaigns

    sender.add_periodic_task(
        crontab(minute="*/60"),  # every 60 minutes
        run_scheduled_campaigns.s(),
        name="run_scheduled_campaigns",
    )

    # This 3 tasks tested
    # # Calls test('hello') every 10 seconds.
    # sender.add_periodic_task(
    #     10.0, test_celery_task.s("hello 10 sec"), name="'add every 10'",
    # )

    # # Calls test('world') every 30 seconds
    # sender.add_periodic_task(
    #     30.0,
    #     test_celery_task.s("world"),
    #     name="'add every 30'",
    # )

    # sender.add_periodic_task(
    #     crontab(minute="*/2"),  # every 2 minutes
    #     test_celery_task.s("hello 2 min"),
    #     name="add every 2 minutes",
    # )

    # Example with cron
    # # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test_celery_task.s('Happy Mondays!'),
    # )


@app.task
def test_celery_task(arg):
    print(arg)
