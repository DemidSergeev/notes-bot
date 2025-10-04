FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое папки bot в контейнер
COPY . .

# Создаём директории и делаем entrypoint исполняемым
RUN mkdir -p /app/check /app/data/notes /app/subjects
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]

