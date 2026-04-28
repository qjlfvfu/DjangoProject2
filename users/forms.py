from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Client


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя"""

    email = forms.EmailField(required=True, label="Email")
    name = forms.CharField(required=True, label="Ф.И.О.")

    class Meta:
        model = CustomUser
        fields = ("email", "name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # Используем email как username
        user.email = self.cleaned_data["email"]
        user.name = self.cleaned_data["name"]
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Форма редактирования профиля"""

    password = None  # Скрываем поле пароля

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "readonly": "readonly"})
    )
    name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = CustomUser
        fields = ("email", "name", "comment")


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
