from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from users.forms import ClientForm
from .forms import MailingForm, MessageForm
from .models import Client, Message, Mailing, MailingAttempt


class HomeView(TemplateView):
    """Главная страница со статистикой"""

    template_name = "spammanager/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            # Статистика для авторизованного пользователя
            context["total_clients"] = Client.objects.filter(
                owner=self.request.user
            ).count()
            context["total_messages"] = Message.objects.filter(
                owner=self.request.user
            ).count()

            mailings = Mailing.objects.filter(owner=self.request.user)
            context["total_mailings"] = mailings.count()

            # Статусы рассылок
            context["created_mailings"] = mailings.filter(
                status=Mailing.STATUS_CREATED
            ).count()
            context["started_mailings"] = mailings.filter(
                status=Mailing.STATUS_STARTED
            ).count()
            context["completed_mailings"] = mailings.filter(
                status=Mailing.STATUS_COMPLETED
            ).count()

            # Статистика попыток через рассылки пользователя
            attempts = MailingAttempt.objects.filter(mailing__owner=self.request.user)
            context["success_attempts"] = attempts.filter(status="success").count()
            context["failed_attempts"] = attempts.filter(status="failed").count()
        else:
            # Для неавторизованных - нули
            context["total_clients"] = 0
            context["total_messages"] = 0
            context["total_mailings"] = 0
            context["created_mailings"] = 0
            context["started_mailings"] = 0
            context["completed_mailings"] = 0
            context["success_attempts"] = 0
            context["failed_attempts"] = 0

        return context


# --- СООБЩЕНИЯ (Message) ---
class MessageListView(LoginRequiredMixin, ListView):
    """Список сообщений"""

    model = Message
    template_name = "spammanager/message_list.html"
    context_object_name = "messages"
    paginate_by = 10

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения"""

    model = Message
    form_class = MessageForm
    template_name = "spammanager/message_form.html"
    success_url = reverse_lazy("spammanager:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Устанавливаем владельца
        messages.success(self.request, "Сообщение успешно создано!")
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сообщения"""

    model = Message
    form_class = MessageForm
    template_name = "spammanager/message_form.html"
    success_url = reverse_lazy("spammanager:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Сообщение успешно обновлено!")
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление сообщения"""

    model = Message
    template_name = "spammanager/message_confirm_delete.html"
    success_url = reverse_lazy("spammanager:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Сообщение успешно удалено!")
        return super().delete(request, *args, **kwargs)


# --- РАССЫЛКИ (Mailing) ---
class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок"""

    model = Mailing
    template_name = "spammanager/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10

    def get_queryset(self):
        # Получаем все рассылки пользователя
        mailings = Mailing.objects.filter(owner=self.request.user)
        # Обновляем статусы
        for mailing in mailings:
            mailing.update_status()
        return mailings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем оригинальный QuerySet для подсчета (не пагинированный)
        all_mailings = Mailing.objects.filter(owner=self.request.user)
        for mailing in all_mailings:
            mailing.update_status()

        # Считаем по статусам из оригинального QuerySet
        context["created_count"] = all_mailings.filter(
            status=Mailing.STATUS_CREATED
        ).count()
        context["started_count"] = all_mailings.filter(
            status=Mailing.STATUS_STARTED
        ).count()
        context["completed_count"] = all_mailings.filter(
            status=Mailing.STATUS_COMPLETED
        ).count()

        # Для каждой рассылки в пагинированном списке добавляем статистику
        for mailing in context["mailings"]:
            mailing.success_count = mailing.attempts.filter(status="success").count()
            mailing.failed_count = mailing.attempts.filter(status="failed").count()
            mailing.total_attempts = mailing.attempts.count()

        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки"""

    model = Mailing
    form_class = MailingForm
    template_name = "spammanager/mailing_form.html"
    success_url = reverse_lazy("spammanager:mailing_list")

    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Устанавливаем владельца рассылки"""
        form.instance.owner = self.request.user
        # Статус устанавливается автоматически в модели (по умолчанию 'created')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Создание рассылки"
        return context


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование рассылки"""

    model = Mailing
    form_class = MailingForm
    template_name = "spammanager/mailing_form.html"
    success_url = reverse_lazy("spammanager:mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Рассылка успешно обновлена!")
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление рассылки"""

    model = Mailing
    template_name = "spammanager/mailing_confirm_delete.html"
    success_url = reverse_lazy("spammanager:mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Рассылка успешно удалена!")
        return super().delete(request, *args, **kwargs)


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр рассылки"""

    model = Mailing
    template_name = "spammanager/mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # Обновляем статус при просмотре
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attempts"] = self.object.attempts.all()[:10]  # Последние 10 попыток
        return context


@method_decorator(cache_page(60 * 30), name="dispatch")
class MailingAttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = "spammanager/mailing_attempt_list.html"
    context_object_name = "attempts"
    paginate_by = 20

    def get_queryset(self):
        return MailingAttempt.objects.filter(
            mailing__owner=self.request.user
        ).select_related("mailing", "recipient")


class ClientListView(LoginRequiredMixin, ListView):
    """Список клиентов"""

    model = Client
    template_name = "spammanager/client_list.html"
    context_object_name = "clients"
    paginate_by = 10

    def get_queryset(self):
        queryset = Client.objects.filter(owner=self.request.user)
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search)
                | models.Q(full_name__icontains=search)
            )
        return queryset


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание клиента"""

    model = Client
    form_class = ClientForm
    template_name = "spammanager/client_form.html"
    success_url = reverse_lazy("spammanager:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Клиент успешно создан!")
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование клиента"""

    model = Client
    form_class = ClientForm
    template_name = "spammanager/client_form.html"
    success_url = reverse_lazy("spammanager:client_list")

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Клиент успешно обновлен!")
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление клиента"""

    model = Client
    template_name = "spammanager/client_confirm_delete.html"
    success_url = reverse_lazy("spammanager:client_list")

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Клиент успешно удален!")
        return super().delete(request, *args, **kwargs)
