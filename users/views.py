from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .tasks import send_welcome_email


class UserRegisterView(CreateView):
    """Регистрация нового пользователя"""

    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        # Отправляем приветственное письмо после успешной регистрации
        send_welcome_email.delay(self.object.id)
        messages.success(self.request, "Регистрация прошла успешно! Проверьте почту.")
        return response


class UserLoginView(LoginView):
    """Вход в систему"""

    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # Перенаправляем на главную страницу spammanager
        return reverse_lazy("spammanager:home")

    def form_valid(self, form):
        messages.success(self.request, f"Добро пожаловать, {form.get_user().email}!")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """Выход из системы"""

    next_page = reverse_lazy("spammanager:home")  # На главную после выхода

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Вы вышли из системы.")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, DetailView):
    """Профиль пользователя"""

    model = CustomUser
    template_name = "users/profile.html"
    context_object_name = "user"

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем статистику
        try:
            from spammanager.models import Client, Message, Mailing

            context["total_clients"] = Client.objects.filter(
                owner=self.request.user
            ).count()
            context["total_messages"] = Message.objects.filter(
                owner=self.request.user
            ).count()
            context["total_mailings"] = Mailing.objects.filter(
                owner=self.request.user
            ).count()
        except Exception:
            # Если модели еще не созданы или приложение не установлено
            context["total_clients"] = 0
            context["total_messages"] = 0
            context["total_mailings"] = 0
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля"""

    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, **kwargs):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Профиль успешно обновлен!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме.")
        return super().form_invalid(form)
