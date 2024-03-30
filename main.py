import datetime
import os
import json
import httpx
from bs4 import BeautifulSoup as bs
from typing import Dict, Any
from fastapi import FastAPI

app = FastAPI()
end = ["armatura", "balka", "katanka_krug", "kvadrat", "list_goryachekatanyy", "list_prosechno_vytyazhnoy", "list_riflenyy", "list_kholodnokatannyy", "polosa", "truba_profilnaya", "truba_vgp_elektrosvarnaya", "ugolok", "shveller", "shveller_gnutyy"]
@app.get("/{name}/")
async def get_home(name: str):
    if end.__contains__(name):
        return await get(name)
    else:
        return {"error": "bad request"}


@app.get("/")
async def get_home():
    return {"error": "bad request"}

async def get(name: str) -> Dict[str, Any]:
    file_path = f"{name}.json"
    file_check = check_file(file_path)

    if file_check == 0:
        return get_data(file_path)
    elif file_check == 1:
        os.remove(file_path)
        await write_data(name)
        return get_data(file_path)
    else:
        await write_data(name)
        return get_data(file_path)

def get_data(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        transformed_data = {}
        for key, value in data.items():
            print(value['PROPERTIES']["KOEFFITSIENT_VOLKHONKA"]["VALUE"], "KOEFFITSIENT_VOLKHONKA")
            print(value['PROPERTIES']["KOEFFITSIENT_OKTYABRSKAYA"]["VALUE"], "KOEFFITSIENT_OKTYABRSKAYA")
            KOEFFITSIENT = float(value['PROPERTIES']["KOEFFITSIENT_VOLKHONKA"]["VALUE"] if
                value['PROPERTIES']["KOEFFITSIENT_OKTYABRSKAYA"]["VALUE"] == "0" or value['PROPERTIES']["KOEFFITSIENT_OKTYABRSKAYA"]["VALUE"] == "" else
                value['PROPERTIES']["KOEFFITSIENT_OKTYABRSKAYA"]["VALUE"])

            ITEM_PRICES = {x['PRICE']: round(KOEFFITSIENT / 1000 * x['PRICE'], 2) for x in value["ITEM_PRICES"]}

            ITEM_PRICES_METR = {x['PRICE']: round(KOEFFITSIENT / 1000 * x['PRICE'] / float(value['PROPERTIES']['DLINA']['VALUE']), 2) for x in
                                value["ITEM_PRICES"]}
            transformed_data[key] = {
                'FULL_NAME': value['FULL_NAME'],
                'ARTICLE': value['PROPERTIES']['ARTICLE']['VALUE'],
                'DLINA': value['PROPERTIES']['DLINA']['VALUE'],
                "KOEFFITSIENT": KOEFFITSIENT,
                "PRICES": {index: x['PRICE'] for index, x in enumerate(value["ITEM_PRICES"])},
                "ITEM_PRICES": ITEM_PRICES,
                'MAX_GOOD_FOR_ORDER': value['PROPERTIES']['MAX_GOOD_FOR_ORDER']["VALUE"],
                "ITEM_PRICES_METR": ITEM_PRICES_METR,
                'MAX_GOOD_FOR_ORDER': value['PROPERTIES']['MAX_GOOD_FOR_ORDER']["VALUE"]
            }
        return transformed_data
    except FileNotFoundError:
        return {"error": "not found"}
    except json.JSONDecodeError as e:
        return {"error": "Ошибка декодирования JSON"}

async def write_data(name: str):
    file_path = f"{name}.json"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://szmetal.ru/catalog/{name}/")
            resp.raise_for_status()  # Проверяем успешность запроса
            soup = bs(resp.text, "lxml")
            jsonData = json.loads(soup.find("div", class_="catalog-table js-products").attrs['data-items'])
            with open(file_path, "w") as json_file:
                json.dump(jsonData, json_file)
    except httpx.RequestError as e:
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
