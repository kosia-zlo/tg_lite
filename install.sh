#!/bin/bash
#
# Установочный скрипт для VPN-бота (TG-Bot-OpenVPN-Antizapret)
# Версия: 2.0 — теперь автоматически ставит python3-venv и зависимые пакеты
#
# Что делает этот скрипт:
# 1) Проверяет и ставит (при необходимости) git, wget, curl, python3-venv
# 2) Спрашивает BOT_TOKEN и ADMIN_ID, сохраняет их в .env
# 3) Спрашивает FILEVPN_NAME, заменяет плейсхолдер "${FILEVPN_NAME}" на введённое имя во всех файлах (кроме install.sh)
# 4) Клонирует (или обновляет) репозиторий, создаёт виртуальное окружение, устанавливает зависимости
# 5) Делает client.sh исполняемым (если он есть)
# 6) Создаёт systemd-юнит vpnbot.service, включается автозапуск и сразу стартует его
# 7) Выводит на экран базовые команды для управления

set -e

### 0) Проверка, что скрипт запущен под root
if [ "$EUID" -ne 0 ]; then
  echo "Ошибка: этот скрипт нужно запустить от root."
  exit 1
fi

echo "=============================================="
echo "Установка VPN-бота (TG-Bot-OpenVPN-Antizapret) v2.0"
echo "=============================================="
echo

### 1) Проверка и установка обязательных пакетов
echo "=== Шаг 1: Устанавливаем необходимые системные пакеты ==="
apt update -qq

# Список нужных пакетов
REQUIRED_PKG=("git" "wget" "curl" "python3-venv" "python3-pip")

for pkg in "${REQUIRED_PKG[@]}"; do
  if ! dpkg -s "$pkg" &>/dev/null; then
    echo "  • Устанавливаем пакет: $pkg"
    apt install -y "$pkg"
  else
    echo "  • Пакет $pkg уже установлен — пропускаем."
  fi
done

echo "Системные зависимости установлены."
echo

### 2) Запрашиваем BOT_TOKEN и ADMIN_ID
echo "=== Шаг 2: Настройка BOT_TOKEN и ADMIN_ID ==="
read -p "Введите BOT_TOKEN (токен из BotFather): " BOT_TOKEN
BOT_TOKEN="$(echo "$BOT_TOKEN" | xargs)"
if [ -z "$BOT_TOKEN" ]; then
  echo "Ошибка: BOT_TOKEN не может быть пустым."
  exit 1
fi

read -p "Введите ADMIN_ID (ваш Telegram User ID, например 123456789): " ADMIN_ID
ADMIN_ID="$(echo "$ADMIN_ID" | xargs)"
if [ -z "$ADMIN_ID" ]; then
  echo "Ошибка: ADMIN_ID не может быть пустым."
  exit 1
fi

### 3) Запрашиваем FILEVPN_NAME
echo
echo "=== Шаг 3: Ввод базового имени для VPN-файлов (плейсхолдер \"\${FILEVPN_NAME}\") ==="
read -p "Введите желаемое имя (например, MyVPN): " FILEVPN_NAME
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

### 4) Готовим каталог репозитория
REPO_DIR="/root/antizapret-bot"

if [ -d "$REPO_DIR/.git" ]; then
  echo "Каталог $REPO_DIR уже содержит Git-репозиторий."
  read -p "Обновить его (git pull) [Y/n]? " yn
  yn="${yn:-Y}"
  if [[ "$yn" =~ ^[Yy]$ ]]; then
    echo "  Выполняем git pull..."
    cd "$REPO_DIR"
    git pull --ff-only
  else
    echo "  Пропускаем обновление."
  fi
else
  echo "Клонируем репозиторий из GitHub в $REPO_DIR..."
  git clone https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret.git "$REPO_DIR"
fi

cd "$REPO_DIR"

### 5) Создаём (или очищаем) файл .env с нашими переменными
echo
echo "=== Шаг 4: Запись переменных в .env ==="
cat > ".env" <<EOF
BOT_TOKEN="$BOT_TOKEN"
ADMIN_ID="$ADMIN_ID"
FILEVPN_NAME="$FILEVPN_NAME"
EOF
echo "  Файл .env записан."

### 6) Заменяем "${FILEVPN_NAME}" → введённое имя во всех файлах, кроме самого install.sh
echo
echo "=== Шаг 5: Ищем и заменяем literal \"\${FILEVPN_NAME}\" → \"$FILEVPN_NAME\" ==="
# Находим файлы, где встречается плейсхолдер, но пропускаем этот install.sh
FILES_WITH_PLACEHOLDER=$(grep -RIl '\${FILEVPN_NAME}' . | grep -v "./install.sh")

if [ -z "$FILES_WITH_PLACEHOLDER" ]; then
  echo "  ⚠️  Ни один файл (кроме install.sh) с \"\${FILEVPN_NAME}\" не найден."
  echo "      Проверьте, что вы действительно вставили плейсхолдер \"\${FILEVPN_NAME}\" в bot.py, client.sh, шаблоны и т. д."
else
  for f in $FILES_WITH_PLACEHOLDER; do
    sed -i "s|\${FILEVPN_NAME}|${FILEVPN_NAME}|g" "$f"
    echo "  Заменено в: $f"
  done
fi

### 7) Создаём виртуальное окружение в /root/venv и устанавливаем зависимости
VENV_DIR="/root/venv"
echo
echo "=== Шаг 6: Установка Python-виртуального окружения ==="

if [ ! -d "$VENV_DIR" ]; then
  echo "  Создаём venv: python3 -m venv $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "  Виртуальное окружение $VENV_DIR уже существует — пропускаем создание."
fi

echo "  Активируем venv и устанавливаем библиотеки из requirements.txt"
source "$VENV_DIR/bin/activate"
if [ -f "requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "  ⚠️  Файл requirements.txt не найден — зависимости не установлены!"
fi
deactivate

### 8) Делаем client.sh исполняемым (если он существует)
if [ -f "client.sh" ]; then
  chmod +x client.sh
fi

### 9) Создаём systemd-юнит vpnbot.service
echo
echo "=== Шаг 7: Создание systemd-юнита /etc/systemd/system/vpnbot.service ==="
cat > /etc/systemd/system/vpnbot.service <<EOF
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
EnvironmentFile=$REPO_DIR/.env
ExecStart=$VENV_DIR/bin/python $REPO_DIR/bot.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "  Юнит создан: /etc/systemd/system/vpnbot.service"

### 10) Перезагружаем daemon, включаем автозапуск и стартуем службу
echo
echo "Перезагружаем systemd-daemon, включаем автозапуск и запускаем vpnbot.service..."
systemctl daemon-reload
systemctl enable vpnbot.service
systemctl restart vpnbot.service

### 11) Завершающее сообщение и инструкции
echo
echo "=============================================="
echo "Установка завершена! Бот запущен как vpnbot.service."
echo
echo "Команды для управления ботом:"
echo "  ● Проверить статус:     systemctl status vpnbot.service"
echo "  ● Перезапустить бота:   systemctl restart vpnbot.service"
echo "  ● Смотреть логи:        journalctl -u vpnbot -f"
echo
echo "Основные пути и параметры:"
echo "  ● Репозиторий:          $REPO_DIR"
echo "  ● Виртуальное окружение: $VENV_DIR"
echo "  ● Файл .env:            $REPO_DIR/.env"
echo "       • BOT_TOKEN    = $BOT_TOKEN"
echo "       • ADMIN_ID     = $ADMIN_ID"
echo "       • FILEVPN_NAME = $FILEVPN_NAME"
echo "=============================================="
