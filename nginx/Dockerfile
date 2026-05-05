# Используем образ Nginx alpine
FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
# Копируем файл конфигурации Nginx в контейнер
COPY nginx.conf /etc/nginx/nginx.conf

# Открываем порт 80 для HTTP-трафика
EXPOSE 80
