#!/bin/bash
# renew_cert.sh <client_name> <days>
CLIENT_NAME="$1"
DAYS="$2"

EASYRSA_DIR="/etc/openvpn/easyrsa3"
PKI_DIR="$EASYRSA_DIR/pki"
BACKUP_DIR="$EASYRSA_DIR/backup-renew-$(date +%F_%H-%M-%S)"


if [[ -z "$CLIENT_NAME" || -z "$DAYS" ]]; then
    echo "Usage: $0 <client_name> <days>"
    exit 1
fi

cd "$EASYRSA_DIR" || exit 1

if [ ! -f "$PKI_DIR/issued/${CLIENT_NAME}.crt" ] || [ ! -f "$PKI_DIR/private/${CLIENT_NAME}.key" ]; then
    echo "Клиент $CLIENT_NAME не найден."
    exit 1
fi

# Backup
mkdir -p "$BACKUP_DIR"
cp "$PKI_DIR/issued/${CLIENT_NAME}.crt" "$BACKUP_DIR/"
cp "$PKI_DIR/private/${CLIENT_NAME}.key" "$BACKUP_DIR/"
cp "$PKI_DIR/reqs/${CLIENT_NAME}.req" "$BACKUP_DIR/" 2>/dev/null || true

# (Опционально) Ревокация старого сертификата — если нужен строгий аудит
# ./easyrsa revoke "$CLIENT_NAME" || true

# Удаляем старый сертификат (но ключ не трогаем!)
rm -f "$PKI_DIR/issued/${CLIENT_NAME}.crt"

# Генерируем новый CSR на тот же ключ
openssl req -new -key "$PKI_DIR/private/${CLIENT_NAME}.key" \
    -out "$PKI_DIR/reqs/${CLIENT_NAME}.req" -subj "/CN=${CLIENT_NAME}"

# Подписываем новый сертификат у CA с нужным сроком
./easyrsa --batch --days="$DAYS" sign client "$CLIENT_NAME"

if [ $? -eq 0 ]; then
    echo "Сертификат клиента $CLIENT_NAME успешно продлён на $DAYS дней!"
    exit 0
else
    echo "Ошибка продления сертификата $CLIENT_NAME"
    exit 1
fi
