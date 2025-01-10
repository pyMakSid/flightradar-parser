# flightradar-parser

Модуль парсинга данных авиакоманий по ссылке на рейсы (напр. https://www.flightradar24.com/data/airlines/ek-uae/fleet)

* requirements.txt - файл для создания окружения с помощью conda
* flightradar_parser.py - модуль парсера данных
    * load_aircompany_data(path_to_aircompany_fleet) - функция парсинга данных, принимающая как аргумент ссылку на полёты авиакомпании
* config.json - конфиг файл для подключения к базе данных PostgreSQL
* results\data-emirates.csv - результатиы парсинга данных для авиакомании Emirates