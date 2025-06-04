#!/bin/bash
#
# Установочный скрипт для VPN-бота (TG-Bot-OpenVPN-Antizapret)
# Версия: учёт ${FILEVPN_NAME}-плейсхолдера
#
# Что делает этот скрипт:
# 1) Спрашивает у вас BOT_TOKEN и ADMIN_ID, сохраняет их в .env
# 2) Спрашивает у вас FILEVPN_NAME, затем во всех файлах заменяет буквальную строку "${FILEVPN_NAME}" на введённое вами имя
# 3) Клонирует (или обновляет) репозиторий, создаёт виртуальное окружение, устанавливает зависимости
# 4) Создаёт systemd-юнит vpnbot.service, который подхватывает переменные из .env и запускает bot.py
# 5) Активирует службу и показывает базовые команды управления

set -e

### 0) Проверка, что скрипт запущен под root
if [ "$EUID" -ne 0 ]; then
  echo "Ошибка: этот скрипт нужно запустить от root."
  exit 1
fi

echo "=============================================="
echo "Установка VPN-бота (TG-Bot-OpenVPN-Antizapret)"
echo "=============================================="
echo

### 1) Запрашиваем BOT_TOKEN и ADMIN_ID
read -p "1) Введите BOT_TOKEN (токен из BotFather): " BOT_TOKEN
BOT_TOKEN="$(echo "$BOT_TOKEN" | xargs)"
if [ -z "$BOT_TOKEN" ]; then
  echo "Ошибка: BOT_TOKEN не может быть пустым."
  exit 1
fi

read -p "2) Введите ADMIN_ID (ваш Telegram User ID, например 123456789): " ADMIN_ID
ADMIN_ID="$(echo "$ADMIN_ID" | xargs)"
if [ -z "$ADMIN_ID" ]; then
  echo "Ошибка: ADMIN_ID не может быть пустым."
  exit 1
fi

### 2) Запрашиваем FILEVPN_NAME (т. е. то, что раньше было «БичиVPN»)
echo
echo "3) Теперь задайте базовое имя для VPN-файлов (замена плейсхолдера \${FILEVPN_NAME})."
read -p "   Введите, например, БичиVPN или MyVPN: " FILEVPN_NAME
FILEVPN_NAME="$(echo "$FILEVPN_NAME" | xargs)"
if [ -z "$FILEVPN_NAME" ]; then
  echo "Ошибка: имя для VPN-файлов не может быть пустым."
  exit 1
fi

echo
echo "Вы ввели:"
echo "  BOT_TOKEN    = \"$BOT_TOKEN\""
echo "  ADMIN_ID     = \"$ADMIN_ID\""
echo "  FILEVPN_NAME = \"$FILEVPN_NAME\""
echo

### 3) Создаём (или очищаем) каталог для репозитория
REPO_DIR="/root/antizapret-bot"
if [ -d "$REPO_DIR" ]; then
  echo "Каталог $REPO_DIR уже существует."
  read -p "Обновить существующий репозиторий (git pull)? [Y/n]: " yn
  yn="${yn:-Y}"
  if [[ "$yn" =~ ^[Yy]$ ]]; then
    cd "$REPO_DIR"
    echo "  Выполняем git pull..."
    git pull
  else
    echo "  Выбран пропуск обновления, пропускаем git pull."
  fi
else
  echo "Клонируем репозиторий из GitHub в $REPO_DIR..."
  git clone https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret.git "$REPO_DIR"
fi

cd "$REPO_DIR"

### 4) Создаём (или очищаем) файл .env с переменными BOT_TOKEN, ADMIN_ID и FILEVPN_NAME
echo
echo "Создаём файл .env в $REPO_DIR/.env"
cat > ".env" <<EOF
BOT_TOKEN="$BOT_TOKEN"
ADMIN_ID="$ADMIN_ID"
FILEVPN_NAME="$FILEVPN_NAME"
EOF

### 5) Во всех файлах заменяем "${FILEVPN_NAME}" на введённое имя
echo
echo "Ищем и заменяем Literal \"\${FILEVPN_NAME}\" → \"$FILEVPN_NAME\" во всех файлах репозитория..."

# Найдём все файлы, содержащие последовательность ${FILEVPN_NAME}
FILES_WITH_PLACEHOLDER=$(grep -RIl '\${FILEVPN_NAME}' .)

if [ -z "$FILES_WITH_PLACEHOLDER" ]; then
  echo "  ⚠️  Не найден ни один файл с \"\${FILEVPN_NAME}\". Проверьте, что вы вставили плейсхолдер в нужных местах."
else
  for f in $FILES_WITH_PLACEHOLDER; do
    sed -i "s|\${FILEVPN_NAME}|${FILEVPN_NAME}|g" "$f"
    echo "  Заменено в: $f"
  done
fi

### 6) Создаём виртуальное окружение и устанавливаем зависимости
VENV_DIR="/root/venv"
echo
echo "=== Установка Python-виртуального окружения ==="
if [ ! -d "$VENV_DIR" ]; then
  echo "Создаём виртуальное окружение: python3 -m venv $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "Виртуальное окружение $VENV_DIR уже существует, пропускаем создание."
fi

echo "Активируем venv и устанавливаем зависимости (requirements.txt)..."
source "$VENV_DIR/bin/activate"
if [ -f "requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "  ⚠️  Файл requirements.txt не найден — зависимости не установлены!"
fi
deactivate

### 7) Делаем client.sh исполняемым (если он есть)
if [ -f "client.sh" ]; then
  chmod +x client.sh
fi

### 8) Создаём systemd-юнит vpnbot.service
echo
echo "=== Создаём systemd-юнит: /etc/systemd/system/vpnbot.service ==="
cat > /etc/systemd/system/vpnbot.service <<EOF
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
# Подхватываем .env (BOT_TOKEN, ADMIN_ID, FILEVPN_NAME)
EnvironmentFile=$REPO_DIR/.env
# Запуск бота через виртуальное окружение:
ExecStart=$VENV_DIR/bin/python $REPO_DIR/bot.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

### 9) Перезагружаем systemd, включаем автозапуск и запускаем службу
echo
echo "Перезагружаем demon, включаем автозапуск и стартуем vpnbot.service..."
systemctl daemon-reload
systemctl enable vpnbot.service
systemctl restart vpnbot.service

### 10) Завершающее сообщение
echo
echo "=============================================="
echo "Установка завершена! Бот запущен как vpnbot.service."
echo
echo "Полезные команды для управления ботом:"
echo "  ● Проверить статус:     systemctl status vpnbot.service"
echo "  ● Перезапустить бота:   systemctl restart vpnbot.service"
echo "  ● Смотреть логи:        journalctl -u vpnbot -f"
echo
echo "Параметры установки:"
echo "  ● Репозиторий:          $REPO_DIR"
echo "  ● Виртуальное окружение: $VENV_DIR"
echo "  ● Файл с переменными:   $REPO_DIR/.env"
echo "       • BOT_TOKEN    = $BOT_TOKEN"
echo "       • ADMIN_ID     = $ADMIN_ID"
echo "       • FILEVPN_NAME = $FILEVPN_NAME"
echo "=============================================="
