# TG-Bot-OpenVPN-Antizapret

---
# Бот рабочий и юзабельный
---
Добавил Webpanel https://github.com/VATAKATru61/Open-VPN-WebPanel-for-Antizapret/

---
Что умеет бот
- Управлять пользователями (Удалять, добавлять, изменять)
- Смотреть кто онлайн
- Пересоздавать файлы
- Делать бэкап
- Создавать объявления
- Выдавать конфиги
- Изменять имя, которое меняет конфиг
- Когда новый юзер заходит в бот, в меню его не впускают, он отправляет запрос. Админу приходит сообщение что новый юзер хочет присоединиться. И после этого Админ Может его одобрить и отклонить. Одобренному пользователю выдается доступ к меню + 30 дней его использование. Конфиг может взять с меню. 
- Одобренные пользователи хранятся в папке root/approved_users.txt
---

Опыта ноль, делал через GPT 4.5. Ошибок нет.

Тут я опишу что и как и куда добавить

---
- Файл .env в папку root/   "ВСТАВЬ СВОЕ"
- Файл bot.py в папку root/ "ВСТАВЬ СВОЕ"
- Свое я там убрал и заменил текст на :exclamation::exclamation::exclamation:"ВСТАВЬ СВОЕ":exclamation::exclamation::exclamation: просто поиском можешь найти эти строки и вставить туда всё свое
- antizapret.conf в папку /etc/openvpn/client/templates :exclamation::exclamation::exclamation:"ВСТАВЬ СВОЕ":exclamation::exclamation::exclamation:
- Строка 15 Ваше навание в клиенте
- vpn.conf в папку /etc/openvpn/client/templates :exclamation::exclamation::exclamation:"ВСТАВЬ СВОЕ":exclamation::exclamation::exclamation:
- Строка 15 Ваше навание в клиенте
- client.sh в папку /root/antizapret/ замени :exclamation::exclamation::exclamation:"ВСТАВЬ СВОЕ":exclamation::exclamation::exclamation:
- db.py в папку /root/ Не нужно ние менять
- renew_cert.sh в папку /etc/openvpn/easyrsa3 Не нужно ниче менять
---



А теперь установка. Изменяете, скидываете все файлы куда я расписал. Далее


Устанавливаем EASY-RSA в папку cd /etc/openvpn/easyrsa3 и даем права
```
cd /etc/openvpn/easyrsa3
wget https://github.com/OpenVPN/easy-rsa/releases/download/v3.1.7/EasyRSA-3.1.7.tgz
tar xzf EasyRSA-3.1.7.tgz --strip-components=1
chmod +x ./easyrsa
```

Запуск бота. Будут скорее всего ошибки потому что у вас могут быть установленны не все компачи. Но там уже просто их доустановите 

Создаем сервисный файл
```
sudo nano /etc/systemd/system/vpnbot.service
```
Вставляем туда 
```
[Unit]
Description=VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/root/venv/bin/python /root/bot.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
Сохраняем

Презегрузи сервис и запускай
```
sudo systemctl daemon-reload
sudo systemctl enable vpnbot
sudo systemctl start vpnbot
sudo systemctl status vpnbot
```


Запуск бота
```
sudo systemctl start vpnbot
```
Перезапуск бота
```
sudo systemctl restart vpnbot
```

Просмотр статуса сервиса
```
sudo systemctl status vpnbot
```

Просмотр логов
```
journalctl -u vpnbot -f
```


Надеюсь ничего не забыл. Сорри если это так. После запуска должны создаться файлы в /root/
- approved_users.txt   Пользователи которые подтверждены и им есть дотуп к пользовательскому меню
- pending_users.json Это файл, в котором бот хранит заявки на доступ от пользователей, которые ещё не одобрены админом.
- users.txt — это файл, в котором просто хранятся user_id всех пользователей, которые уже когда-либо работали с ботом
- expiry_notified.json — это файл-флаг, чтобы бот не слал одному и тому же пользователю по нескольку раз уведомление о скором окончании срока действия VPN. То есть если тут есть чье то имя, значит бот ему уже отправлял уведомление об окончарии срока
- vpn.db Сама база данных
- База данных сохраняется в root/vpn.bd

  Им нужно будет дать права

  СКРИНЫ
  ![Иллюстрация к проекту](https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret/blob/main/img/main.jpg)
  ![Иллюстрация к проекту](https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret/blob/main/img/user.jpg)
  ![Иллюстрация к проекту](https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret/blob/main/img/profile.jpg)

