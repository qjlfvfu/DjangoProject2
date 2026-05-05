import os
from celery import Celery
from celery.schedules import crontab

# Установка модуля настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Загрузка настроек из Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматическое обнаружение задач в приложениях
app.autodiscover_tasks()

# Периодические задачи (beat schedule)
app.conf.beat_schedule = {
    "block-inactive-users-daily": {
        "task": "users.tasks.block_inactive_users",
        "schedule": crontab(hour=3, minute=0),
    },
    "send-daily-stats-morning": {
        "task": "users.tasks.send_daily_stats",
        "schedule": crontab(hour=9, minute=0),
    },
    "check-mailings-every-minute": {
        "task": "spammanager.tasks.check_pending_mailings",
        "schedule": crontab(minute="*/1"),
    },
    # Дополнительно: проверка рассылок каждую минуту (для вашего проекта)
    "check-mailing-status": {
        "task": "spammanager.tasks.check_mailing_status",
        "schedule": crontab(minute="*/1"),  # каждую минуту
    },
}

# Настройки для продакшена
app.conf.timezone = "UTC"
app.conf.enable_utc = True
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 минут
app.conf.task_soft_time_limit = 25 * 60  # 25 минут
