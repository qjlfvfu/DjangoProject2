from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from users.models import Client, CustomUser


# Create your models here.
class Message(models.Model):
    """Сообщение для рассылки"""
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
    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    # Для отображения в шаблонах
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

    def update_status(self):
        """Обновление статуса на основе текущего времени"""
        now = timezone.now()

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_STARTED
        else:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])
        return self.status

    def clean(self):
        """Валидация данных"""
        now = timezone.now()

        # Проверка: start_time не может быть в прошлом
        if self.start_time and self.start_time < now:
            raise ValidationError({
                'start_time': 'Дата начала не может быть в прошлом'
            })

        # Проверка: start_time должен быть раньше end_time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'Дата окончания должна быть позже даты начала'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def can_send(self):
        """Проверка возможности отправки"""
        now = timezone.now()
        return (self.start_time <= now <= self.end_time and
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