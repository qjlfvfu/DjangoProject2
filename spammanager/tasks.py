from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import Mailing, MailingAttempt, Client, Message
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_mailing(mailing_id):
    """Обработка рассылки"""
    try:
        mailing = Mailing.objects.get(id=mailing_id)

        if not mailing.can_send():
            logger.warning(f"Рассылка {mailing_id} не может быть отправлена")
            return {"status": "skipped", "reason": "cannot send"}

        recipients = mailing.recipients.all()
        success_count = 0
        fail_count = 0

        for recipient in recipients:
            try:
                # Отправка письма
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

                # Запись успешной попытки
                MailingAttempt.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status="success",
                    server_response="Письмо успешно отправлено",
                )
                success_count += 1

            except Exception as e:
                # Запись неудачной попытки
                MailingAttempt.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status="failed",
                    server_response=str(e),
                )
                fail_count += 1
                logger.error(f"Ошибка отправки {recipient.email}: {e}")

        mailing.update_status()

        return {
            "status": "completed",
            "mailing_id": mailing_id,
            "success": success_count,
            "failed": fail_count,
        }

    except Mailing.DoesNotExist:
        return {"status": "error", "error": f"Рассылка {mailing_id} не найдена"}
