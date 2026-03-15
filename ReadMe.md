# SpamManager - Система управления рассылками

## 📋 Описание проекта

SpamManager - это веб-приложение на Django для управления email-рассылками. Проект позволяет создавать, управлять и отслеживать рассылки сообщений по клиентам с гибкой системой планирования.

### 🚀 Основные возможности

#### Модели данных:

Client - клиенты (получатели рассылок)

Message - шаблоны сообщений

Mailing - рассылки с планированием по времени

Функционал:
✅ Создание, редактирование и удаление клиентов

✅ Управление шаблонами сообщений

✅ Планирование рассылок с указанием времени старта и окончания

✅ Автоматическое обновление статуса рассылок (Создана/Запущена/Завершена)

✅ Привязка данных к конкретному пользователю (владелец)

✅ Валидация дат (запрет на прошедшие даты)

🛠 Технологии
* Python 3.13+
* Django 6.0
* SQLite3 (по умолчанию)
* Bootstrap 5 (для интерфейса)
* Django Authentication (система авторизации)

📦 Установка и запуск
1. Клонирование репозитория
`bash
gh repo clone qjlfvfu/DjangoProject2
cd DjangoProject2`
2. Создание виртуального окружения
bash
# Windows
`python -m venv .venv
.venv\Scripts\activate`

# Linux/Mac
`python3 -m venv .venv
source .venv/bin/activate
Установка зависимостей
bash
pip install -r requirements.txt
Применение миграций
bash
python manage.py migrate
Создание суперпользователя
bash
python manage.py createsuperuser
Запуск сервера
bash
python manage.py runserver`
📁 Структура проекта
text
DjangoProject2/
├── config/                 # Настройки проекта
│   ├── settings.py        # Основные настройки
│   ├── urls.py            # Главный URL-конфиг
│   └── wsgi.py            # WSGI конфиг
├── spammanager/           # Главное приложение
│   ├── templates/         # Шаблоны
│   │   └── spammanager/   # Шаблоны приложения
│   │       ├── base.html
│   │       ├── mailing_list.html
│   │       ├── mailing_form.html
│   │       └── ...
│   ├── models.py          # Модели данных
│   ├── views.py           # Представления
│   ├── forms.py           # Формы
│   ├── urls.py            # URL-маршруты
│   └── admin.py           # Админка
├── users/                 # Приложение пользователей
│   ├── models.py          # Модель пользователя
│   └── urls.py            # URL-маршруты
├── manage.py              # Управляющий скрипт
└── requirements.txt       # Зависимости
📊 Модели данных
Client (Клиент)
python
email: EmailField (уникальный)
full_name: CharField
comment: TextField (опционально)
owner: ForeignKey(User)
created_at: DateTimeField
Message (Сообщение)
python
subject: CharField (тема)
body: TextField (текст)
owner: ForeignKey(User)
created_at: DateTimeField
Mailing (Рассылка)
python
start_time: DateTimeField
end_time: DateTimeField
status: CharField (created/started/completed)
message: ForeignKey(Message)
recipients: ManyToManyField(Client)
owner: ForeignKey(User)
created_at: DateTimeField
is_active: BooleanField
🔐 Права доступа
* Каждый пользователь видит только свои данные

* Анонимные пользователи не имеют доступа к функциям

* Суперпользователь имеет доступ ко всем данным через админку

🌐 URL-маршруты
* Главное приложение (spammanager)
* URL	Название	Описание
* /	home	Главная страница
* /clients/	client_list	Список клиентов
* /clients/create/	client_create	Создание клиента
* /clients/<id>/update/	client_update	Редактирование клиента
* /clients/<id>/delete/	client_delete	Удаление клиента
* /messages/	message_list	Список сообщений
* /messages/create/	message_create	Создание сообщения
* /messages/<id>/update/	message_update	Редактирование сообщения
* /messages/<id>/delete/	message_delete	Удаление сообщения
* /mailings/	mailing_list	Список рассылок
* /mailings/create/	mailing_create	Создание рассылки
* /mailings/<id>/	mailing_detail	Детали рассылки
* /mailings/<id>/update/	mailing_update	Редактирование рассылки
* /mailings/<id>/delete/	mailing_delete	Удаление рассылки
* Пользователи (users)
* URL	Название	Описание
* /users/login/	login	Вход в систему
* /users/logout/	logout	Выход из системы

##  Создание клиентов

`python manage.py shell
python
from spammanager.models import Client, Message
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()ёё`

## Создание клиентов

`Client.objects.create(
    email='client1@example.com',
    full_name='Иван Петров',
    comment='Тестовый клиент',
    owner=user
)`

## Создание сообщения
`Message.objects.create(
    subject='Тестовое сообщение',
    body='Привет! Это тестовое сообщение.',
    owner=user
)`
🔧 Настройка проекта
Основные настройки в settings.py:
python
## Авторизация
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'spammanager:home'
LOGOUT_REDIRECT_URL = 'spammanager:home'

## Кастомная модель пользователя
AUTH_USER_MODEL = 'users.CustomUser'

## 📝 Требования к окружению
1. [ ] Python 3.13 или выше
2. [ ] Django 6.0
3. [ ] SQLite (встроенный)

## 👨‍💻 Автор

#### _Николай Малышкин_


**Важно**: Проект находится в активной разработке. Возможны изменения и улучшения функционала.

