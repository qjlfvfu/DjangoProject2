from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class CustomUser(AbstractUser):
    name = models.CharField(max_length=40, help_text="Введите Ф.И.О.", null=False, verbose_name="Ф.И.О. пользователя")
    email= models.EmailField(unique=True, null=False, help_text="Введите email", verbose_name="mail пользователя")
    comment = models.TextField(null=True, blank=True, verbose_name="комментарии")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

class Client(models.Model):
    """Получатель рассылки (клиент)"""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф.И.О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='clients', verbose_name="Владелец")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["-created_at"]

