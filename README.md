# TG-Bot-OpenVPN-Antizapret

---
# Бот рабочий и юзабельный, но для идеала нужно допиливать
---


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
1. Файл .env в папку root/    Измените там значения на свои
2. Файл bot.py в папку root/ Измените там значения на свои
2.1  Свое я там убрал и заменил текст на "ВСТАВЬ СВОЕ" просто поиском можешь найти эти строки и вставить туда всё свое

   
|  СТРОКА | Что изменить                                                |
|---------|-------------------------------------------------------------|   
|  1138   |Ссылка на сайт                                               |
|  1374   |Ссылка на сайт                                               |
|  1876   |Название файла для обычного VPN(режим авто)                  |
|  1869   |Название файла для Antizapret (Режим авто)                   |
|  1886   |Название файла при скачивании для обычного VPN(режим авто)   |
|  1889   |Название файла при скачивании для Antizapret (Режим авто)    |
|  1918   |Ссылка на сайт                                               |

UPD. ВОЗМОЖНО ИНФА УЖЕ СЪЕХАЛА, НЕТ ВРЕМЕНИ КАЖДЫЙ РАЗ ПЕРЕПИСЫВАТЬ, КОД МЕНЯЮ ЧАСТО

4. antizapret.conf в папку /etc/openvpn/client/templates Измени значения на свои
3.1   Строка 15 Ваше навание в клиенте
5.  vpn.conf в папку /etc/openvpn/client/templates Измени значения на свои
4.1   Строка 15 Ваше навание в клиенте
6.  client.sh в папку /root/antizapret/ Не нужно ниче менять
7.  db.py в папку /root/ Не нужно ние менять
8.  renew_cert.sh в папку /etc/openvpn/easyrsa3 Не нужно ниче менять
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
- approved_users.txt
- pending_users.json
- users.txt
- vpn.db
- База данных сохраняется в root/vpn.bd

  Им нужно будет дать права

  СКРИНЫ
  ![Иллюстрация к проекту](https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret/blob/main/main.jpg)
  ![Иллюстрация к проекту](https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret/blob/main/user.jpg)
  ![Иллюстрация к проекту](https://github.com/VATAKATru61/TG-Bot-OpenVPN-Antizapret/blob/main/config.jpg)

