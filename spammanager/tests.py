from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from .models import Client, Message, Mailing, MailingAttempt

User = get_user_model()


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            name="Test User",
        )

    def test_create_client(self):
        client = Client.objects.create(
            email="client@example.com",
            full_name="Иван Иванов",
            comment="Тестовый клиент",
            owner=self.user,
        )
        self.assertEqual(client.email, "client@example.com")
        self.assertEqual(client.full_name, "Иван Иванов")

    def test_client_owner_relation(self):
        client = Client.objects.create(
            email="client@example.com", full_name="Иван Иванов", owner=self.user
        )
        self.assertEqual(client.owner.email, "test@test.com")
        self.assertEqual(self.user.clients.count(), 1)


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            name="Test User",
        )

    def test_create_message(self):
        message = Message.objects.create(
            subject="Тестовая тема", body="Тестовое тело письма", owner=self.user
        )
        self.assertEqual(message.subject, "Тестовая тема")
        self.assertEqual(message.body, "Тестовое тело письма")

    def test_message_owner_relation(self):
        message = Message.objects.create(subject="Тест", body="Тело", owner=self.user)
        self.assertEqual(message.owner.email, "test@test.com")
        self.assertEqual(self.user.messages.count(), 1)


class MailingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            name="Test User",
        )
        self.message = Message.objects.create(
            subject="Тестовая тема", body="Тестовое тело", owner=self.user
        )

    def test_create_mailing(self):
        now = timezone.now()
        mailing = Mailing.objects.create(
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=7),
            message=self.message,
            owner=self.user,
        )
        mailing.recipients.set([])
        self.assertEqual(mailing.message.subject, "Тестовая тема")

    def test_validation_start_time_not_in_past(self):
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
        now = timezone.now()
        mailing = Mailing(
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=1),
            message=self.message,
            owner=self.user,
        )
        with self.assertRaises(ValidationError):
            mailing.full_clean()


class MailingAttemptModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            name="Test User",
        )
        self.message = Message.objects.create(
            subject="Тест", body="Тело", owner=self.user
        )
        self.client_obj = Client.objects.create(
            email="client@example.com", full_name="Клиент", owner=self.user
        )
        now = timezone.now()
        self.mailing = Mailing.objects.create(
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=7),
            message=self.message,
            owner=self.user,
        )

    def test_create_successful_attempt(self):
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing,
            status="success",
            server_response="Письмо успешно отправлено",
            recipient=self.client_obj,
        )
        self.assertEqual(attempt.status, "success")

    def test_create_failed_attempt(self):
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing,
            status="failed",
            server_response="Ошибка: неверный email",
            recipient=self.client_obj,
        )
        self.assertEqual(attempt.status, "failed")

    def test_attempt_relation_to_mailing(self):
        attempt = MailingAttempt.objects.create(
            mailing=self.mailing, status="success", server_response="OK"
        )
        self.assertEqual(attempt.mailing.id, self.mailing.id)
        self.assertEqual(self.mailing.attempts.count(), 1)


class PermissionsTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@test.com",
            password="pass123",
            name="User One",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="user2@test.com",
            password="pass123",
            name="User Two",
        )
        self.message1 = Message.objects.create(
            subject="User1 message", body="Body", owner=self.user1
        )
        self.message2 = Message.objects.create(
            subject="User2 message", body="Body", owner=self.user2
        )

    def test_user_sees_only_own_messages(self):
        self.assertEqual(self.user1.messages.count(), 1)
        self.assertEqual(self.user1.messages.first().subject, "User1 message")

    def test_user_cannot_see_other_messages(self):
        self.assertEqual(self.user2.messages.count(), 1)
        self.assertNotIn(self.message2, self.user1.messages.all())


class MailingAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            name="Test User",
        )
        self.client.force_authenticate(user=self.user)
        self.message = Message.objects.create(
            subject="Тест", body="Тело", owner=self.user
        )
        self.client_obj = Client.objects.create(
            email="client@example.com", full_name="Клиент", owner=self.user
        )

    def test_create_mailing_via_api(self):
        url = "/api/mailings/"
        now = timezone.now()
        data = {
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=7)).isoformat(),
            "message": self.message.id,
            "recipients": [self.client_obj.id],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_mailings_via_api(self):
        url = "/api/mailings/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        url = "/api/mailings/"
        data = {
            "start_time": timezone.now().isoformat(),
            "end_time": timezone.now().isoformat(),
            "message": self.message.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EmailSendingTest(TestCase):
    def test_email_sending(self):
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
