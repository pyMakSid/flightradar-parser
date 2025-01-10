import time
from datetime import date, datetime
import json

import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By


def db_connect(config_path='config.json'):
    with open(config_path) as json_data:
        config = json.load(json_data)
    
    connection = psycopg2.connect(
        host = config['database']['host'],
        user = config['database']['username'],
        password = config['database']['password'],
        database = config['database']['dbname']
    )
    connection.autocommit = True
    
    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS flights (
               id SERIAL PRIMARY KEY,
               flight_number VARCHAR(50) NOT NULL,
               date DATE NOT NULL,
               from_city VARCHAR(100),
               airport_out_code VARCHAR(100),
               to_city VARCHAR(100),
               airport_to_code VARCHAR(50),
               scheduled_time_of_departure VARCHAR(50),
               actual_time_of_departure VARCHAR(50),
               flight_time VARCHAR(50),
               landed_time VARCHAR(50),
               scheduled_time_of_arrival VARCHAR(50),
               aircraft_code VARCHAR(50),
               aircraft_model VARCHAR(100),
               date_of_load TIMESTAMP NOT NULL,
               UNIQUE (flight_number, date));"""
        )
    print('DB is connected!')
    return connection


def db_insert(connection, data):
    with connection.cursor() as cursor:
        cursor.execute(
        f"""INSERT INTO flights (
        flight_number, date, from_city, airport_out_code, 
        to_city, airport_to_code, scheduled_time_of_departure,
        actual_time_of_departure, flight_time, landed_time,
        scheduled_time_of_arrival, aircraft_code, aircraft_model,
        date_of_load
    ) VALUES ({', '.join(data)})
        ON CONFLICT (flight_number, date) 
        DO UPDATE SET
            actual_time_of_departure = EXCLUDED.actual_time_of_departure,
            flight_time = EXCLUDED.flight_time,
            landed_time = EXCLUDED.landed_time,
            aircraft_code = EXCLUDED.aircraft_code,
            aircraft_model = EXCLUDED.aircraft_model,
            date_of_load = EXCLUDED.date_of_load;
    """
        )


def _load_airplane_list(browser: webdriver.Chrome) -> list:
    airplans_list = []
    time.sleep(3)
    airplanes_list_web = browser.find_elements(By.CSS_SELECTOR, 'a[class="regLinks"]')
    for airplane in airplanes_list_web:
        if airplane.text:
            airplans_list.append(airplane.text)
    return airplans_list


def _load_flight_data(browser: webdriver.Chrome, connection, airplane, airplane_code):
    information_list = []
    information = browser.find_elements(By.CSS_SELECTOR, 'tr[class=" data-row"]')
    for info in information:
        information_list.append(info.text)
    
    for el in information_list:
        flight_data = [item for item in el.split('\n') if item]

        if '—' in flight_data or '-' in flight_data:
            continue
        else:                                                     
            city_out = flight_data[-3]
            city_to = flight_data[-1]

            data_row = {
                'Flight Number': flight_data[0],
                'Date': datetime.strptime(flight_data[1], '%d %b %Y').date(),
                'From City': city_out[:-5],
                'Airport out Code': city_out[-4:-1],
                'To City': city_to[:-5],
                'Airport to code': city_to[-4:-1],
                'Scheduled Time of Departure (STD)': flight_data[5],
                'Actual Time of Departure (ATD)': flight_data[7],
                'Flight Time': flight_data[2],
                'Landed Time': flight_data[3].split()[1],
                'Scheduled Time of Arrival (STA)':flight_data[9],
                'Aircraft code': airplane,
                'Aircraft model': airplane_code,
                'Date of load': date.today()
            }
            db_insert(connection, ["'" + str(item) + "'" for item in list(data_row.values())])


def load_aircompany_data(aircompany_fleet_link):
    try:
        connection = db_connect()

        options = webdriver.EdgeOptions()
        options.add_argument('log-level=3')
        options.add_argument("--headless")

        with webdriver.Edge(options=options) as browser:
            browser.get(aircompany_fleet_link)
            time.sleep(1)
            browser.find_element(By.ID, "onetrust-accept-btn-handler").click()
            time.sleep(1)

            button_list = browser.find_elements(By.CSS_SELECTOR, 'i[class="pull-right fa fa-angle-down"]')
            for i in range(len(button_list)):
                button_list = browser.find_elements(By.CSS_SELECTOR, 'i[class="pull-right fa fa-angle-down"]')
                time.sleep(1)
                button_list[i].click()
                airplanes_list = _load_airplane_list(browser)
                
                for airplane in airplanes_list:
                    link = browser.find_element(By.PARTIAL_LINK_TEXT, airplane)
                    browser.execute_script("arguments[0].click();", link)
                    time.sleep(2)
                    airplane_code = browser.find_element(By.CLASS_NAME, 'details').text
                    elements = browser.find_elements(By.CSS_SELECTOR, 'td[class="text-center"]')

                    if elements and elements[0].text == "Sorry, but we could not find data for specified flight":
                        pass
                    else:
                        _load_flight_data(browser, connection, airplane, airplane_code)

                    last_elem = airplanes_list[-1]
                    browser.back()
                    if  airplane != last_elem:
                        new_button_list = browser.find_elements(By.CSS_SELECTOR, 'i[class="pull-right fa fa-angle-down"]')
                        time.sleep(1)
                        new_button_list[i].click()
    except Exception as _ex:
        print('Error:', _ex)
    finally:
        if connection:
            connection.close()
            print('Connection is closed!')


if __name__ == '__main__':
    load_aircompany_data('https://www.flightradar24.com/data/airlines/ek-uae/fleet')