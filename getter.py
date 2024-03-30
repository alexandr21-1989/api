import datetime
import os

import requests
from bs4 import BeautifulSoup as bs
import json


def get(name: str) -> str:
    file_path = f"{name}.json"
    file_check = check_file(file_path)

    if file_check == 0:
        data = get_data(file_path)
    elif file_check == 1:
        os.remove(file_path)
        write_data(name)
        data = get_data(file_path)
    else:
        write_data(name)
        data = get_data(file_path)
    return data


def get_data(file_path: str) -> str:
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        transformed_data = {}
        for key, value in data.items():
            transformed_data[key] = {
                'FULL_NAME': value['FULL_NAME'],
                'ARTICLE': value['PROPERTIES']['ARTICLE']['VALUE'],
                "KOEFFITSIENT": value['PROPERTIES']["KOEFFITSIENT_VOLKHONKA"]["VALUE"] if
                value['PROPERTIES']["KOEFFITSIENT_OKTYABRSKAYA"]["VALUE"] == 0 else
                value['PROPERTIES']["KOEFFITSIENT_OKTYABRSKAYA"]["VALUE"],
                "ITEM_PRICES": {index: x['PRICE'] for index, x in enumerate(value["ITEM_PRICES"])},
                'MAX_GOOD_FOR_ORDER': value['PROPERTIES']['MAX_GOOD_FOR_ORDER']
            }
        return json.dumps(transformed_data, ensure_ascii=False)
    except FileNotFoundError:
        return json.dumps({"error": "not found"})
    except json.JSONDecodeError as e:
        return json.dumps({"error": "Ошибка декодирования JSON"})


def write_data(name: str):
    file_path = f"{name}.json"
    try:
        resp = requests.get(f"https://szmetal.ru/catalog/{name}/")
        resp.raise_for_status()  # Проверяем успешность запроса
        soup = bs(resp.text, "lxml")
        jsonData = json.loads(soup.find("div", class_="catalog-table js-products").attrs['data-items'])
        with open(file_path, "w") as json_file:
            json.dump(jsonData, json_file)
    except requests.RequestException as e:
        print(f"Request error: {e}")
    except (AttributeError, KeyError) as e:
        print(f"Parsing error: {e}")


def check_file(file_path: str) -> int:
    if os.path.exists(file_path):
        creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
        current_time = datetime.datetime.now()
        time_difference = current_time - creation_time
        if time_difference.total_seconds() > 2 * 60 * 60:
            return 1  # Файл был создан более 2 часов назад
        else:
            return 0  # Файл был создан менее 2 часов назад
    else:
        return 2  # Файл не найден



