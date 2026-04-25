from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import CustomUser, Client


class Message(models.Model):
    """Сообщение для рассылки"""
    objects = None
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='messages', verbose_name="Владелец")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["-created_at"]


class Mailing(models.Model):
    """Рассылка"""

    # Статусы рассылки
    objects = None
    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    STATUS_DISPLAY = {
        STATUS_CREATED: 'Создана',
        STATUS_STARTED: 'Запущена',
        STATUS_COMPLETED: 'Завершена',
    }

    start_time = models.DateTimeField(verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='mailings', verbose_name="Сообщение")
    recipients = models.ManyToManyField(Client, related_name='mailings', verbose_name="Получатели")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mailings', verbose_name="Владелец")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return f"Рассылка #{self.id} от {self.start_time.strftime('%d.%m.%Y %H:%M')}"

    def _ensure_datetime(self, value, field_name):
        """Преобразует значение в datetime, если это словарь"""
        if value is None:
            return value

        # Если уже datetime, возвращаем как есть
        if isinstance(value, (timezone.datetime, timezone.datetime.__class__)):
            return value

        # Если словарь, преобразуем в datetime
        if isinstance(value, dict):
            from datetime import datetime
            try:
                return datetime(
                    value.get('year', 1),
                    value.get('month', 1),
                    value.get('day', 1),
                    value.get('hour', 0),
                    value.get('minute', 0),
                    value.get('second', 0)
                )
            except:
                pass

        return value

    def update_status(self):
        """Обновление статуса на основе текущего времени"""
        try:
            now = timezone.now()

            # Преобразуем даты, если нужно
            start_time = self._ensure_datetime(self.start_time, 'start_time')
            end_time = self._ensure_datetime(self.end_time, 'end_time')

            # Если преобразование не удалось, используем текущие значения
            if start_time is None or end_time is None:
                return self.status

            # Определяем новый статус
            if now < start_time:
                new_status = self.STATUS_CREATED
            elif start_time <= now <= end_time:
                new_status = self.STATUS_STARTED
            else:
                new_status = self.STATUS_COMPLETED

            # Обновляем статус если изменился
            if self.status != new_status:
                self.status = new_status
                self.save(update_fields=['status'])

            return self.status

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating status for mailing {self.id}: {e}")
            return self.status

    def clean(self):
        """Валидация данных"""
        super().clean()
        now = timezone.now()

        # Преобразуем даты
        start_time = self._ensure_datetime(self.start_time, 'start_time')
        end_time = self._ensure_datetime(self.end_time, 'end_time')

        if start_time is None:
            raise ValidationError({'start_time': 'Неверный формат даты начала'})

        if end_time is None:
            raise ValidationError({'end_time': 'Неверный формат даты окончания'})

        # Проверка: start_time не может быть в прошлом
        if start_time < now:
            raise ValidationError({'start_time': 'Дата начала не может быть в прошлом'})

        # Проверка: start_time должен быть раньше end_time
        if start_time >= end_time:
            raise ValidationError({'end_time': 'Дата окончания должна быть позже даты начала'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def can_send(self):
        """Проверка возможности отправки"""
        now = timezone.now()
        start_time = self._ensure_datetime(self.start_time, 'start_time')
        end_time = self._ensure_datetime(self.end_time, 'end_time')

        if start_time is None or end_time is None:
            return False

        return (start_time <= now <= end_time and
                self.is_active and
                self.status != self.STATUS_COMPLETED)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]
        permissions = [
            ("can_view_all_mailings", "Может просматривать все рассылки"),
            ("can_block_mailings", "Может блокировать рассылки"),
        ]


class MailingAttempt(models.Model):
    """Попытка отправки"""

    objects = None
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts', verbose_name="Рассылка")
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(verbose_name="Ответ почтового сервера")
    recipient = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Получатель")

    def __str__(self):
        return f"Попытка #{self.id} - {self.get_status_display()}"

    class Meta:
        verbose_name = "Попытка отправки"
        verbose_name_plural = "Попытки отправки"
        ordering = ["-attempt_time"]