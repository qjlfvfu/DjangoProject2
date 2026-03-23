from django.utils import timezone

from django import forms
from rest_framework.exceptions import ValidationError

from users.models import Client
from .models import Mailing, Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки"""

    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "message": forms.Select(attrs={"class": "form-select"}),
            "recipients": forms.SelectMultiple(
                attrs={"class": "form-select", "size": "8"}
            ),
        }
        labels = {
            "start_time": "Дата и время начала",
            "end_time": "Дата и время окончания",
            "message": "Сообщение",
            "recipients": "Получатели",
        }
        help_texts = {
            "start_time": "Укажите дату и время начала рассылки",
            "end_time": "Укажите дату и время окончания рассылки",
            "recipients": "Вы можете выбрать несколько получателей (зажмите Ctrl)",
        }

    def __init__(self, *args, **kwargs):
        # Получаем пользователя из kwargs
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Фильтруем сообщения и клиентов по текущему пользователю
        if self.user:
            self.fields["message"].queryset = Message.objects.filter(owner=self.user)
            self.fields["recipients"].queryset = Client.objects.filter(owner=self.user)

        # Делаем поля обязательными
        self.fields["start_time"].required = True
        self.fields["end_time"].required = True
        self.fields["message"].required = True
        self.fields["recipients"].required = True

        # Добавляем классы Bootstrap
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                if "class" not in field.widget.attrs:
                    field.widget.attrs["class"] = "form-control"
                elif "form-control" not in field.widget.attrs["class"]:
                    field.widget.attrs["class"] += " form-control"

    def clean_start_time(self):
        """Валидация даты начала"""
        start_time = self.cleaned_data.get("start_time")
        now = timezone.now()

        if start_time and start_time < now:
            raise ValidationError("Дата начала не может быть в прошлом")

        return start_time

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        # Проверка, что дата окончания позже даты начала
        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError(
                    {"end_time": "Дата окончания должна быть позже даты начала"}
                )

        return cleaned_data
