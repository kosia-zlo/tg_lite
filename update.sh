#!/bin/bash

cd /root || exit 1

# Сохраняем .env
cp .env .env.bak

# Обновляем репозиторий
git pull origin main

# Восстанавливаем .env
mv .env.bak .env

# Обновляем зависимости
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Перезапуск службы
systemctl restart vpnbot

echo "✅ Бот успешно обновлён!"