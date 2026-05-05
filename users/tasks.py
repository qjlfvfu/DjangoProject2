from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Client
from spammanager.models import Message, Mailing
import logging

logger = logging.getLogger(__name__)


@shared_task
def block_inactive_users():
    """Блокирует пользователей, не заходивших более 30 дней"""
    month_ago = timezone.now() - timedelta(days=30)

    inactive_users = CustomUser.objects.filter(is_active=True, last_login__lt=month_ago)

    count = inactive_users.count()
    blocked_emails = []

    for user in inactive_users:
        user.is_active = False
        user.save()
        blocked_emails.append(user.email)
        logger.info(f"Заблокирован {user.email}")

    return {
        "status": "success",
        "blocked_count": count,
        "blocked_users": blocked_emails,
    }


@shared_task
def send_welcome_email(user_id):
    """Отправка приветственного письма новому пользователю"""
    try:
        user = CustomUser.objects.get(id=user_id)

        send_mail(
            subject="Добро пожаловать в SpamManager!",
            message=f"""
Приветствуем, {user.name or user.email}!

Рады видеть вас на нашем сервисе управления рассылками.

Что вы можете делать:
- Создавать рассылки
- Управлять клиентами
- Отслеживать статистику

С уважением,
Команда SpamManager
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Приветственное письмо отправлено {user.email}")
        return {"status": "success", "email": user.email}

    except CustomUser.DoesNotExist:
        logger.error(f"Пользователь {user_id} не найден")
        return {"status": "error", "error": f"Пользователь {user_id} не найден"}


@shared_task
def send_daily_stats():
    """Отправка статистики администратору"""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    stats = {
        "new_users": CustomUser.objects.filter(date_joined__date=today).count(),
        "new_clients": Client.objects.filter(created_at__date=today).count(),
        "new_messages": Message.objects.filter(created_at__date=today).count(),
        "new_mailings": Mailing.objects.filter(created_at__date=today).count(),
        "total_users": CustomUser.objects.count(),
        "total_clients": Client.objects.count(),
        "total_mailings": Mailing.objects.count(),
    }

    # Статистика за предыдущий день для сравнения
    prev_stats = {
        "new_users": CustomUser.objects.filter(date_joined__date=yesterday).count(),
        "new_clients": Client.objects.filter(created_at__date=yesterday).count(),
    }

    message = f"""
📊 Ежедневная статистика за {today}:

📈 Новые данные:
- Новых пользователей: {stats['new_users']}
  (против {prev_stats['new_users']} вчера)
- Новых клиентов: {stats['new_clients']}
  (против {prev_stats['new_clients']} вчера)
- Новых сообщений: {stats['new_messages']}
- Новых рассылок: {stats['new_mailings']}

📊 Общая статистика:
- Всего пользователей: {stats['total_users']}
- Всего клиентов: {stats['total_clients']}
- Всего рассылок: {stats['total_mailings']}

---
SpamManager Bot
"""

    admins = CustomUser.objects.filter(is_staff=True)
    sent_count = 0

    for admin in admins:
        send_mail(
            subject=f"Ежедневная статистика | {today}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            fail_silently=True,
        )
        sent_count += 1
        logger.info(f"Статистика отправлена админу {admin.email}")

    return {"status": "success", "stats": stats, "sent_to": sent_count}


@shared_task
def send_test_email(recipient_email):
    """Отправка тестового письма (для отладки)"""
    try:
        send_mail(
            subject="Тестовое письмо от Celery",
            message="Если вы читаете это, значит Celery работает правильно!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return {"status": "success", "email": recipient_email}
    except Exception as e:
        logger.error(f"Ошибка отправки тестового письма: {e}")
        return {"status": "error", "error": str(e)}
