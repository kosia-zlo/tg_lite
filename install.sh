#!/bin/bash
#
# Установочный скрипт для VPN-бота (TG-Bot-OpenVPN-Antizapret)
# Версия: 2.6.1 — более точная замена, не трогаем остальные файлы в /root, и даём всем скопированным файлам права 777
#
# Что делает этот скрипт:
# 1) Проверяет и при необходимости устанавливает git, wget, curl, python3-venv, python3-pip
# 2) Спрашивает BOT_TOKEN, ADMIN_ID и FILEVPN_NAME, записывает их в /root/.env
# 3) Клонирует репозиторий во временную папку /tmp/antizapret-install и сбрасывает локальные правки
# 4) Копирует подпапки из временного клона:
#      • antizapret/ → /root/antizapret/     (перезапись только файлов из репо)
#      • etc/openvpn/ → /etc/openvpn/       (перезапись только файлов из репо)
#      • root/ → /root/                     (перезапись только файлов из репо)
# 5) Заменяет "${FILEVPN_NAME}" и "$FILEVPN_NAME" только в:
#      • /root/antizapret/** (исключая client/openvpn/vpn)
#      • /etc/openvpn/**
#      • /root/bot.py и /root/client.sh (если есть)
# 6) Принудительно пересоздаёт виртуальное окружение /root/venv и устанавливает зависимости из /root/requirements.txt
# 7) Даёт всем скопированным файлам права 777
# 8) Создаёт systemd-юнит vpnbot.service, включает автозапуск и запускает службу
# 9) Выводит инструкции по управлению ботом

set -e

### 0) Проверка, что скрипт запущен под root
if [ "$EUID" -ne 0 ]; then
  echo "Ошибка: этот скрипт нужно запустить от root."
  exit 1
fi

echo "=============================================="
echo "Установка VPN-бота (TG-Bot-OpenVPN-Antizapret) v2.6.1"
echo "=============================================="
echo

### 1) Установка системных пакетов (git, wget, curl, python3-venv, python3-pip)
echo "=== Шаг 1: Установка системных пакетов ==="
apt update -qq

REQUIRED_PKG=("git" "wget" "curl" "python3-venv" "python3-pip")
for pkg in "${REQUIRED_PKG[@]}"; do
  if ! dpkg -s "$pkg" &>/dev/null; then
    echo "  • Устанавливаем: $pkg"
    apt install -y "$pkg"
  else
    echo "  • $pkg уже установлен — пропускаем."
  fi
done

echo

### 2) Запрос BOT_TOKEN, ADMIN_ID и FILEVPN_NAME
echo "=== Шаг 2: Настройка BOT_TOKEN, ADMIN_ID и FILEVPN_NAME ==="
read -p "Введите BOT_TOKEN (токен из BotFather): " BOT_TOKEN
BOT_TOKEN="$(echo "$BOT_TOKEN" | xargs)"
if [ -z "$BOT_TOKEN" ]; then
  echo "Ошибка: BOT_TOKEN не может быть пустым."
  exit 1
fi

read -p "Введите ADMIN_ID (ваш Telegram User ID): " ADMIN_ID
ADMIN_ID="$(echo "$ADMIN_ID" | xargs)"
if [ -z "$ADMIN_ID" ]; then
  echo "Ошибка: ADMIN_ID не может быть пустым."
  exit 1
fi

echo
read -p "Введите базовое имя для VPN-файлов (FILEVPN_NAME), например: БичиVPN или MyVPN: " FILEVPN_NAME
FILEVPN_NAME="$(echo "$FILEVPN_NAME" | xargs)"
if [ -z "$FILEVPN_NAME" ]; then
  echo "Ошибка: FILEVPN_NAME не может быть пустым."
  exit 1
fi

echo
echo "Вы ввели:"
echo "  BOT_TOKEN    = \"$BOT_TOKEN\""
echo "  ADMIN_ID     = \"$ADMIN_ID\""
echo "  FILEVPN_NAME = \"$FILEVPN_NAME\""
echo

### 3) Сохранение переменных в /root/.env
echo "=== Шаг 3: Запись переменных в /root/.env ==="
cat > "/root/.env" <<EOF
BOT_TOKEN="$BOT_TOKEN"
ADMIN_ID="$ADMIN_ID"
FILEVPN_NAME="$FILEVPN_NAME"
EOF
echo "  Файл /root/.env записан."
echo

### 4) Клонирование репозитория во временную папку
TMP_DIR="/tmp/antizapret-install"
GIT_URL="https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret.git"
BRANCH="main"

if [ -d "$TMP_DIR" ]; then
  echo "Удаляем старую временную папку $TMP_DIR"
  rm -rf "$TMP_DIR"
fi

echo "=== Шаг 4: Клонируем репозиторий в $TMP_DIR ==="
git clone "$GIT_URL" "$TMP_DIR"
cd "$TMP_DIR"
git checkout "$BRANCH"

echo
echo "Сбрасываем локальные изменения и подтягиваем origin/$BRANCH..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"
echo

### 5) Копирование подпапок в целевые директории (перезапись только файлов из репо)
echo "=== Шаг 5: Копирование файлов из временного клона ==="

# 5.1) antizapret → /root/antizapret
SRC_ANTIZAPRET="$TMP_DIR/antizapret"
DST_ANTIZAPRET="/root/antizapret"
if [ -d "$SRC_ANTIZAPRET" ]; then
  echo "  Копируем файлы из '$SRC_ANTIZAPRET' → '$DST_ANTIZAPRET' (перезапись без удаления остального)"
  mkdir -p "$DST_ANTIZAPRET"
  cp -r "$SRC_ANTIZAPRET/"* "$DST_ANTIZAPRET/"
else
  echo "  ⚠️  Папка '$SRC_ANTIZAPRET' не найдена — проверьте структуру репозитория."
fi

# 5.2) etc/openvpn → /etc/openvpn
SRC_OPENVPN="$TMP_DIR/etc/openvpn"
DST_OPENVPN="/etc/openvpn"
if [ -d "$SRC_OPENVPN" ]; then
  echo "  Копируем файлы из '$SRC_OPENVPN' → '$DST_OPENVPN' (перезапись без удаления остального)"
  mkdir -p "$DST_OPENVPN"
  cp -r "$SRC_OPENVPN/"* "$DST_OPENVPN/"
else
  echo "  ⚠️  Папка '$SRC_OPENVPN' не найдена — проверьте структуру."
fi

# 5.3) root → /root
SRC_ROOT="$TMP_DIR/root"
DST_ROOT="/root"
if [ -d "$SRC_ROOT" ]; then
  echo "  Копируем файлы из '$SRC_ROOT' → '$DST_ROOT' (перезапись без удаления остального)"
  cp -r "$SRC_ROOT/"* "$DST_ROOT/"
else
  echo "  ⚠️  Папка '$SRC_ROOT' не найдена — проверьте структуру репозитория."
fi

echo "Копирование завершено."
echo

### 6) Замена плейсхолдера "${FILEVPN_NAME}" и "$FILEVPN_NAME"
# Теперь заменяем только в:
#  • /root/antizapret/**, исключая /root/antizapret/client/openvpn/vpn/**
#  • /etc/openvpn/**
#  • /root/bot.py и /root/client.sh (если они есть)

echo "=== Шаг 6: Ищем и заменяем literal \"\${FILEVPN_NAME}\" и \"\$FILEVPN_NAME\" → \"$FILEVPN_NAME\" ==="

# 6.1) В /root/antizapret, исключая client/openvpn/vpn
find /root/antizapret -type f ! -path "/root/antizapret/client/openvpn/vpn/*" | while IFS= read -r f; do
  grep -q '\${FILEVPN_NAME}' "$f" && {
    sed -i "s|\${FILEVPN_NAME}|${FILEVPN_NAME}|g" "$f"
    echo "  Заменено \${FILEVPN_NAME} в: $f"
  }
  grep -q '\$FILEVPN_NAME' "$f" && {
    sed -i "s|\$FILEVPN_NAME|${FILEVPN_NAME}|g" "$f"
    echo "  Заменено \$FILEVPN_NAME в: $f"
  }
done || true

# 6.2) В /etc/openvpn
find /etc/openvpn -type f | while IFS= read -r f; do
  grep -q '\${FILEVPN_NAME}' "$f" && {
    sed -i "s|\${FILEVPN_NAME}|${FILEVPN_NAME}|g" "$f"
    echo "  Заменено \${FILEVPN_NAME} в: $f"
  }
  grep -q '\$FILEVPN_NAME' "$f" && {
    sed -i "s|\$FILEVPN_NAME|${FILEVPN_NAME}|g" "$f"
    echo "  Заменено \$FILEVPN_NAME в: $f"
  }
done || true

# 6.3) В /root/bot.py и /root/client.sh (если есть)
for f in /root/bot.py /root/client.sh; do
  if [ -f "$f" ]; then
    grep -q '\${FILEVPN_NAME}' "$f" && {
      sed -i "s|\${FILEVPN_NAME}|${FILEVPN_NAME}|g" "$f"
      echo "  Заменено \${FILEVPN_NAME} в: $f"
    }
    grep -q '\$FILEVPN_NAME' "$f" && {
      sed -i "s|\$FILEVPN_NAME|${FILEVPN_NAME}|g" "$f"
      echo "  Заменено \$FILEVPN_NAME в: $f"
    }
  fi
done

echo

### 7) Принудительное пересоздание виртуального окружения и установка зависимостей
echo "=== Шаг 7: (ПРИНУДИТЕЛЬНО) создание виртуального окружения и установка зависимостей ==="
VENV_DIR="/root/venv"

if [ -d "$VENV_DIR" ]; then
  echo "  Удаляем существующее виртуальное окружение: rm -rf $VENV_DIR"
  rm -rf "$VENV_DIR"
fi

echo "  Создаём виртуальное окружение: python3 -m venv $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo "  Активируем venv и устанавливаем зависимости из /root/requirements.txt"
source "$VENV_DIR/bin/activate"
if [ -f "/root/requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r /root/requirements.txt
else
  echo "  ⚠️  /root/requirements.txt не найден — зависимости не установлены!"
fi
deactivate

echo

### 8) Даем всем скопированным файлам права 777
echo "=== Шаг 8: Даем полные права (777) всем скопированным файлам ==="
# /root/antizapret
if [ -d "/root/antizapret" ]; then
  chmod -R 777 "/root/antizapret"
  echo "  Права 777 выставлены на /root/antizapret"
fi

# /etc/openvpn
if [ -d "/etc/openvpn" ]; then
  chmod -R 777 "/etc/openvpn"
  echo "  Права 777 выставлены на /etc/openvpn"
fi

# Файлы из СSRC_ROOT
if [ -d "$SRC_ROOT" ]; then
  find "$SRC_ROOT" -type f | while IFS= read -r srcf; do
    rel="${srcf#$SRC_ROOT/}"
    target="/root/$rel"
    if [ -e "$target" ]; then
      chmod 777 "$target"
      echo "  Права 777 выставлены на $target"
    fi
  done
fi

echo

### 9) Создание systemd-юнита vpnbot.service
echo "=== Шаг 9: Создание systemd-юнита /etc/systemd/system/vpnbot.service ==="
cat > /etc/systemd/system/vpnbot.service <<EOF
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
EnvironmentFile=/root/.env
ExecStart=/root/venv/bin/python /root/bot.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "  Юнит записан: /etc/systemd/system/vpnbot.service"
echo

### 10) Перезагрузка systemd, автозапуск, запуск службы
echo "=== Шаг 10: Перезагрузка systemd и запуск vpnbot.service ==="
systemctl daemon-reload
systemctl enable vpnbot.service
systemctl restart vpnbot.service

echo

### 11) Итоговое сообщение и инструкции
echo "=============================================="
echo "Установка завершена! Бот запущен как vpnbot.service."
echo
echo "Команды для управления ботом:"
echo "  ● Проверить статус:     systemctl status vpnbot.service"
echo "  ● Перезапустить бота:   systemctl restart vpnbot.service"
echo "  ● Смотреть логи:        journalctl -u vpnbot -f"
echo
echo "Основные пути и параметры:"
echo "  ● /root/antizapret  — скопировано из репозитория antizapret/"
echo "  ● /etc/openvpn     — скопировано из репозитория etc/openvpn/"
echo "  ● /root            — скопировано из репозитория root/ (bot.py, client.sh, requirements.txt и т. д.)"
echo "  ● Виртуальное окружение:  /root/venv"
echo "  ● Файл с переменными:     /root/.env"
echo "       • BOT_TOKEN    = $BOT_TOKEN"
echo "       • ADMIN_ID     = $ADMIN_ID"
echo "       • FILEVPN_NAME = $FILEVPN_NAME"
echo "=============================================="
