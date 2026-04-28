 SpamManager - Система управления рассылками

## 📋 Описание проекта

SpamManager - это веб-приложение на Django для управления email-рассылками. Проект позволяет создавать, управлять и отслеживать рассылки сообщений по клиентам с гибкой системой планирования.

### 🚀 Основные возможности

#### Модели данных:
- **Client** - клиенты (получатели рассылок)
- **Message** - шаблоны сообщений
- **Mailing** - рассылки с планированием по времени

#### Функционал:
✅ Создание, редактирование и удаление клиентов
✅ Управление шаблонами сообщений
✅ Планирование рассылок с указанием времени старта и окончания
✅ Автоматическое обновление статуса рассылок (Создана/Запущена/Завершена)
✅ Привязка данных к конкретному пользователю (владелец)
✅ Валидация дат (запрет на прошедшие даты)

## 🛠 Технологии

- Python 3.13+
- Django 6.0
- PostgreSQL / SQLite3
- Bootstrap 5 (для интерфейса)
- Django Authentication (система авторизации)
- Gunicorn (production сервер)
- Nginx (reverse proxy)
- GitHub Actions (CI/CD)

## 📦 Установка и запуск локально

### 1. Клонирование репозитория

`git clone https://github.com/qjlfvfu/DjangoProject2.git
cd DjangoProject2 `

2. Создание виртуального окружения
Windows: 

`python -m venv .venv
.venv\Scripts\activate `
Linux/Mac:

`python3 -m venv .venv
source .venv/bin/activate`
3. Установка зависимостей
`pip install -r requirements.txt`
4. Настройка переменных окружения
Создайте файл .env в корне проекта:

env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=DjangoProject2
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
5. Настройка базы данных
Для SQLite (по умолчанию):
`python manage.py migrate`
Для PostgreSQL:
sql
CREATE DATABASE DjangoProject2;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE DjangoProject2 TO your_user;
6. Применение миграций
`python manage.py migrate`
7. Создание суперпользователя
`python manage.py createsuperuser`
8. Запуск сервера разработки
`python manage.py runserver`
Приложение будет доступно по адресу: http://127.0.0.1:8000

🚀 Деплой на production сервер
Подготовка сервера (Ubuntu 22.04/24.04)
1. Подключение к серверу
ssh user@your-server-ip
2. Установка необходимого ПО
`sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git nginx postgresql postgresql-contrib -y`
3. Настройка PostgreSQL
`sudo -u postgres psql`
sql
CREATE DATABASE DjangoProject2;
CREATE USER your_user WITH PASSWORD 'your_password';
ALTER ROLE your_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE DjangoProject2 TO your_user;
\q
4. Клонирование проекта
`git clone https://github.com/qjlfvfu/DjangoProject2.git
cd DjangoProject2`
5. Настройка виртуального окружения
bash
`python3 -m venv venv
source venv/bin/activate`
`pip install -r requirements.txt`
6.  Применение миграций и сбор статики
bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
7. Настройка Gunicorn
Создайте systemd сервис:

bash
sudo nano /etc/systemd/system/gunicorn.service
ini
[Unit]
Description=Gunicorn for SpamManager
After=network.target

[Service]
User=your_user
Group=www-data
WorkingDirectory=/home/your_user/DjangoProject2
EnvironmentFile=/home/your_user/DjangoProject2/.env
ExecStart=/home/your_user/DjangoProject2/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 config.wsgi:application

[Install]
WantedBy=multi-user.target
Запустите Gunicorn:

bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
9. Настройка Nginx
Создайте конфигурацию сайта:

bash
`sudo nano /etc/nginx/sites-available/spammanager`
nginx
server {
    listen 80;
    server_name your-server-ip;

    location /static/ {
        alias /home/your_user/DjangoProject2/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
Активируйте сайт:

bash
`sudo ln -s /etc/nginx/sites-available/spammanager /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx`
10. Настройка фаервола
bash
`sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable`
🔄 CI/CD Pipeline (GitHub Actions)
Настройка секретов в GitHub
Перейдите в Settings → Secrets and variables → Actions вашего репозитория и добавьте следующие секреты:

## Secret Name	Описание

_SSH_PRIVATE_KEY_	Приватный SSH ключ для доступа к серверу
_SSH_USER_	Имя пользователя на сервере (например, your_user)
_SERVER_IP_	IP адрес сервера (например, 81.26.185.12)
_DEPLOY_DIR_	Путь к проекту на сервере (например, /home/your_user/DjangoProject2)
Настройка SSH ключей для CI/CD
bash
# Создайте ключ для GitHub Actions
`ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions_key`

# Скопируйте публичный ключ на сервер
`ssh-copy-id -i ~/.ssh/github_actions_key.pub your_user@your-server-ip`

# Скопируйте приватный ключ в GitHub Secret
cat ~/.ssh/github_actions_key
Workflow файл (.github/workflows/deploy.yml)
yaml
name: Deploy

on:
  push:
    branches: [main, master]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - name: Add server to known_hosts
        run: |
          mkdir -p ~/.ssh
          ssh-keyscan -H ${{ secrets.SERVER_IP }} >> ~/.ssh/known_hosts

      - name: Deploy to server
        run: |
          ssh ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }} "
            cd ${{ secrets.DEPLOY_DIR }} &&
            git pull &&
            source venv/bin/activate &&
            pip install -r requirements.txt &&
            python manage.py migrate &&
            python manage.py collectstatic --noinput &&
            sudo systemctl restart gunicorn &&
            sudo systemctl restart nginx
          "
Автоматизация деплоя
При каждом git push в ветку main или master:

✅ GitHub Actions клонирует проект

✅ Устанавливает SSH подключение

✅ Копирует файлы на сервер

✅ Устанавливает зависимости

✅ Выполняет миграции

✅ Собирает статику

✅ Перезапускает Gunicorn и Nginx

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
│   ├── models.py          # Модели данных
│   ├── views.py           # Представления
│   ├── forms.py           # Формы
│   ├── urls.py            # URL-маршруты
│   └── admin.py           # Админка
├── users/                 # Приложение пользователей
│   ├── models.py          # Модель пользователя
│   └── urls.py            # URL-маршруты
├── .github/               # GitHub Actions
│   └── workflows/
│       └── deploy.yml     # CI/CD pipeline
├── manage.py              # Управляющий скрипт
├── requirements.txt       # Зависимости
├── .env.template          # Шаблон переменных окружения
└── .gitignore            # Исключения для Git
🔐 Безопасность
✅ Все секреты хранятся в GitHub Secrets

✅ .env файл добавлен в .gitignore

✅ DEBUG=False в production

✅ Пароль базы данных не хранится в коде

✅ SSH ключ безопасно передан через GitHub Secrets

🔧 Команды для управления на сервере
bash
# Проверка статуса
sudo systemctl status gunicorn
sudo systemctl status nginx

# Перезапуск сервисов
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Просмотр логов
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log

# Обновление вручную
cd /home/your_user/DjangoProject2
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
📊 URL-маршруты
Главное приложение (spammanager)
URL	Название	Описание
/	home	Главная страница
/clients/	client_list	Список клиентов
/clients/create/	client_create	Создание клиента
/clients/<id>/update/	client_update	Редактирование клиента
/clients/<id>/delete/	client_delete	Удаление клиента
/messages/	message_list	Список сообщений
/messages/create/	message_create	Создание сообщения
/messages/<id>/update/	message_update	Редактирование сообщения
/messages/<id>/delete/	message_delete	Удаление сообщения
/mailings/	mailing_list	Список рассылок
/mailings/create/	mailing_create	Создание рассылки
/mailings/<id>/	mailing_detail	Детали рассылки
/mailings/<id>/update/	mailing_update	Редактирование рассылки
/mailings/<id>/delete/	mailing_delete	Удаление рассылки
Пользователи (users)
URL	Название	Описание
/users/login/	login	Вход в систему
/users/logout/	logout	Выход из системы
/users/register/	register	Регистрация
/users/profile/	profile	Профиль пользователя
👨‍💻 Автор
Николай Малышкин

📌 Важно: Проект Сделан с доработками ИИ в разумных пределах.