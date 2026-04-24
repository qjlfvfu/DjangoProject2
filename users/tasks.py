from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Client
import logging

logger = logging.getLogger(__name__)


@shared_task
def block_inactive_users():
    """Блокирует пользователей, не заходивших более 30 дней"""
    month_ago = timezone.now() - timedelta(days=30)

    inactive_users = CustomUser.objects.filter(
        is_active=True,
        last_login__lt=month_ago
    )

    count = inactive_users.count()

    for user in inactive_users:
        user.is_active = False
        user.save()
        logger.info(f'Заблокирован {user.email}')

    return f'Заблокировано {count} пользователей'


@shared_task
def send_welcome_email(user_id):
    """Отправка приветственного письма новому пользователю"""
    try:
        user = CustomUser.objects.get(id=user_id)

        send_mail(
            subject='Добро пожаловать!',
            message=f'Приветствуем, {user.name or user.email}! Рады видеть вас на нашем сервисе.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return f'Письмо отправлено {user.email}'
    except CustomUser.DoesNotExist:
        return f'Пользователь {user_id} не найден'


@shared_task
def send_daily_stats():
    """Отправка статистики администратору"""
    today = timezone.now().date()

    stats = {
        'new_users': CustomUser.objects.filter(date_joined__date=today).count(),
        'new_clients': Client.objects.filter(created_at__date=today).count(),
    }

    admins = CustomUser.objects.filter(is_staff=True)

    for admin in admins:
        send_mail(
            subject='Ежедневная статистика',
            message=f'За сегодня:\n- Новых пользователей: {stats["new_users"]}\n- Новых клиентов: {stats["new_clients"]}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            fail_silently=True,
        )

    return stats