import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Периодические задачи
app.conf.beat_schedule = {
    "block-inactive-users-daily": {
        "task": "users.tasks.block_inactive_users",
        "schedule": crontab(hour=3, minute=0),  # каждый день в 3:00
    },
    "send-daily-stats-morning": {
        "task": "users.tasks.send_daily_stats",
        "schedule": crontab(hour=9, minute=0),  # каждый день в 9:00
    },
}
