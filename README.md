## testShop python server
### Описание
RESP API сервис, который позволяет нанимать курьеров на работу. Запускается на порте 8080
### Зависимости
Для реализации сервера использовалась библиотека aiohttp, тесты используют pytest, в качестве базы данных используется sqlite3.
Все зависимости можно посмотреть в requirements.txt
### Гайд по установке
1. Установить git(`apt-get install git`), python3.9(`apt install python3.9` и `apt-get install python3.9-dev`), pip, gcc(`apt install build-essential`)
2. Скачать репозиторий приложения(`git clone https://github.com/VerstakGit/testShop.git`)
3. Установить зависимости(`pip3.9 install -r requirements.txt`)
4. Запуск приложения осуществляется командой`python3.9 main.py`
5. Для запуска приложения в качестве демона надо:
* Сделать файл
* Вставить код
```
[Unit]
Description=Python testShop service
[Service]
WorkingDirectory=/home/entrant/testShop/testShop/
User=user
Restart=always
ExecStart=python3.9 /home/entrant/testShop/testShop/main.py
[Install]
WantedBy=multi-user.target
```
* Добавить сервис `systemctl enable testShop.service`
* Запустить `systemctl start testShop`
### Запуск тестов
`pytest -v`