#!/bin/sh
set -e

# Выполняем seed (создаст записи предметов на основе файлов в subjects/)
python seeder.py

# Запуск бота (основной процесс)
exec python main.py