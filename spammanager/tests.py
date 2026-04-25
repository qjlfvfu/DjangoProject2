from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from .models import Client, Message, Mailing, MailingAttempt

User = get_user_model()


class ClientModelTest(TestCase):
    """Тесты для модели Client"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email="test@test.com", password="testpass123", name="Test User"
        )

    def test_create_client(self):
        """Тест создания клиента"""
        client = Client.objects.create(
            email="client@example.com",
            full_name="Иван Иванов",
            comment="Тестовый клиент",
            owner=self.user,
        )
        self.assertEqual(client.email, "client@example.com")
        self.assertEqual(client.full_name, "Иван Иванов")
        self.assertEqual(str(client), "Иван Иванов (client@example.com)")

    def test_client_owner_relation(self):
        """Тест связи клиента с владельцем"""
        client = Client.objects.create(
            email="client@example.com", full_name="Иван Иванов", owner=self.user
        )
        self.assertEqual(client.owner.email, "test@test.com")
        self.assertEqual(self.user.clients.count(), 1)


class MessageModelTest(TestCase):
    """Тесты для модели Message"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email="test@test.com", password="testpass123", name="Test User"
        )

    def test_create_message(self):
        """Тест создания сообщения"""
        message = Message.objects.create(
            subject="Тестовая тема", body="Тестовое тело письма", owner=self.user
        )
        self.assertEqual(message.subject, "Тестовая тема")
        self.assertEqual(message.body, "Тестовое тело письма")
        self.assertEqual(str(message), "Тестовая тема")

    def test_message_owner_relation(self):
        """Тест связи сообщения с владельцем"""
        message = Message.objects.create(subject="Тест", body="Тело", owner=self.user)
        self.assertEqual(message.owner.email, "test@test.com")
        self.assertEqual(self.user.messages.count(), 1)


class MailingModelTest(TestCase):
    """Тесты для модели Mailing"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email="test@test.com", password="testpass123", name="Test User"
        )
        self.message = Message.objects.create(
            subject="Тестовая тема", body="Тестовое тело", owner=self.user
        )

    def test_create_mailing(self):
        """Тест создания рассылки"""
        now = timezone.now()
        mailing = Mailing.objects.create(
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=7),
            message=self.message,
            owner=self.user,
        )
        self.assertEqual(mailing.status, Mailing.STATUS_CREATED)

    def test_status_created_when_now_before_start(self):
        """Тест: статус 'Создана', если текущее время раньше start_time"""
        now = timezone.now()
        mailing = Mailing.objects.create(
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=7),
            message=self.message,
            owner=self.user,
        )
        mailing.update_status()
        self.assertEqual(mailing.status, Mailing.STATUS_CREATED)

    @freeze_time("2024-01-15 10:00:00")
    def test_status_started_when_now_between_start_and_end(self):
        """Тест: статус 'Запущена', если текущее время между start_time и end_time"""
        mailing = Mailing.objects.create(
            start_time=timezone.now() + timedelta(minutes=10),
            end_time=timezone.now() + timedelta(minutes=20),
            message=self.message,
            owner=self.user,
        )
        with freeze_time("2024-01-15 10:15:00"):
            mailing.update_status()
            self.assertEqual(mailing.status, Mailing.STATUS_STARTED)

    @freeze_time("2024-01-15 10:00:00")
    def test_status_completed_when_now_after_end(self):
        """Тест: статус 'Завершена', если текущее время позже end_time"""
        mailing = Mailing.objects.create(
            start_time=timezone.now() + timedelta(minutes=10),
            end_time=timezone.now() + timedelta(minutes=20),
            message=self.message,
            owner=self.user,
        )
        with freeze_time("2024-01-15 10:30:00"):
            mailing.update_status()
            self.assertEqual(mailing.status, Mailing.STATUS_COMPLETED)

    def test_validation_start_time_not_in_past(self):
        """Тест: валидация — start_time не может быть в прошлом"""
        now = timezone.now()
        mailing = Mailing(
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            message=self.message,
            owner=self.user,
        )
        with self.assertRaises(ValidationError):
            mailing.full_clean()

    def test_validation_end_time_after_start_time(self):
        """Тест: валидация — end_time должен быть позже start_time"""
        now = timezone.now()
        mailing = Mailing(
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=1),
            message=self.message,
            owner=self.user,
        )
        with self.assertRaises(ValidationError):
            mailing.full_clean()

    @freeze_time("2024-01-15 10:00:00")
    def test_can_send_true_when_active(self):
        """Тест: can_send возвращает True, если рассылка активна и время подходит"""
        mailing = Mailing.objects.create(
            start_time=timezone.now() + timedelta(minutes=10),
            end_time=timezone.now() + timedelta(minutes=20),
            message=self.message,
            owner=self.user,
            is_active=True,
        )
        with freeze_time("2024-01-15 10:15:00"):
            mailing.update_status()
            self.assertTrue(mailing.can_send())

    @freeze_time("2024-01-15 10:00:00")
    def test_can_send_false_when_inactive(self):
        """Тест: can_send возвращает False, если рассылка не активна"""
        mailing = Mailing.objects.create(
            start_time=timezone.now() + timedelta(minutes=10),
            end_time=timezone.now() + timedelta(minutes=20),
            message=self.message,
            owner=self.user,
            is_active=False,
        )
        with freeze_time("2024-01-15 10:15:00"):
            mailing.update_status()
            self.assertFalse(mailing.can_send())


class MailingAttemptModelTest(TestCase):
    """Тесты для модели MailingAttempt"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email="test@test.com", password="testpass123", name="Test User"
        )
        self.message = Message.objects.create(
            subject="Тест", body="Тело", owner=self.user
        )
        self.client_obj = Client.objects.create(
            email="client@example.com", full_name="Клиент", owner=self.user
        )
        now = timezone.now()
        self.mailing = Mailing.objects.create(
            start_time=now + timedelta(minutes=1),
            end_time=now + timedelta(days=1),
            message=self.message,
            owner=self.user,
        )

    def test_create_successful_attempt(self):
        """Тест создания успешной попытки отправки"""
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing,
            status=MailingAttempt.STATUS_SUCCESS,
            server_response="Письмо успешно отправлено",
            recipient=self.client_obj,
        )
        self.assertEqual(attempt.status, "success")
        self.assertEqual(str(attempt), f"Попытка #{attempt.id} - Успешно")

    def test_create_failed_attempt(self):
        """Тест создания неуспешной попытки отправки"""
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing,
            status=MailingAttempt.STATUS_FAILED,
            server_response="Ошибка: неверный email",
            recipient=self.client_obj,
        )
        self.assertEqual(attempt.status, "failed")
        self.assertEqual(str(attempt), f"Попытка #{attempt.id} - Не успешно")

    def test_attempt_relation_to_mailing(self):
        """Тест связи попытки с рассылкой"""
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing, status="success", server_response="OK"
        )
        self.assertEqual(attempt.mailing.id, self.mailing.id)
        self.assertEqual(self.mailing.attempts.count(), 1)


class PermissionsTest(TestCase):
    """Тесты прав доступа"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1', email="user1@test.com", password="pass123", name="User One"
        )
        self.user2 = User.objects.create_user(
            username='testuser2', email="user2@test.com", password="pass123", name="User Two"
        )
        self.message1 = Message.objects.create(
            subject="User1 message", body="Body", owner=self.user1
        )
        self.message2 = Message.objects.create(
            subject="User2 message", body="Body", owner=self.user2
        )

    def test_user_sees_only_own_messages(self):
        """Тест: пользователь видит только свои сообщения"""
        self.assertEqual(self.user1.messages.count(), 1)
        self.assertEqual(self.user1.messages.first().subject, "User1 message")

    def test_user_cannot_see_other_messages(self):
        """Тест: пользователь не видит чужие сообщения"""
        self.assertEqual(self.user2.messages.count(), 1)
        self.assertEqual(self.user2.messages.first().subject, "User2 message")
        self.assertNotIn(self.message2, self.user1.messages.all())


class EmailSendingTest(TestCase):
    """Тесты отправки писем"""

    def test_email_sending(self):
        """Базовый тест отправки письма"""
        from django.core.mail import send_mail

        send_mail(
            subject="Test",
            message="Content",
            from_email="test@test.com",
            recipient_list=["recipient@example.com"],
            fail_silently=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test")