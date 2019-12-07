import asyncio
import requests_html
import logging
import pymongo
from datetime import datetime
from os import getenv
import hashlib
from bs4 import BeautifulSoup

# with requests_html.HTMLSession() as session:
#     response = session.get("https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/1267392092")
#     response.html.render()
#     print(response.status_code)
#     print(response.html.html)
#     html = response.html.html

with open("tests/pages/list_of_adverts_war.html") as html_file:
    with requests_html.HTMLSession() as session:
        response = session.get("https://www.sreality.cz/hledani/pronajem/byty/praha?velikost=pokoj")
        print(response.text)
        # htm = response.html.html

# with open("tests/pages/failed_parse_page.html") as html_file:
#     expired_html = html_file.read()

# soup = BeautifulSoup(html, "html.parser")
# print(soup.petiffy())

# print(soup.find("div", {"class":"error-content without-button"}))

# page_dict = {'cena_text': '7 000 Kč', 'cena': 7000, 'lokace': 'U hráze, Praha 10 - Strašnice', 'url': 'https://www.sreality.cz/detail/pronajem/byt/5+1/praha-vinor-uherska/142990940', 'typ_smlouvy': 'pronajem', 'typ_nemovitosti': 'byt', 'celkova_cena': '7 000 Kč za měsíc', 'poznamka_k_cene': 'Služby 1000 Kč + provize RK',
#              '_id': 123, 'aktualizace': '16.10.2019', 'stavba': 'Cihlová', 'stav_objektu': 'Po rekonstrukci', 'vlastnictvi': 'Osobní', 'podlazi': '1. podlaží z celkem 4', 'uzitna_plocha': 18, 'plocha_podlahova': 18, 'energeticka_narocnost_budovy': 'Třída G - Mimořádně nehospodárná', 'vybaveni': 1}
# page_dict_new = {'cena_text': '7 000 Eur', 'cena': 7000, 'lokace': 'U hráze, Praha 10 - Strašnice', 'url': 'https://www.sreality.cz/detail/pronajem/byt/5+1/praha-vinor-uherska/142990940', 'typ_smlouvy': 'pronajem', 'typ_nemovitosti': 'byt', 'celkova_cena': '7 000 Kč za měsíc', 'poznamka_k_cene': 'Služby 1000 Kč + provize RK',
#                  '_id': 123, 'aktualizace': '16.10.2019', 'stavba': 'Cihlová', 'stav_objektu': 'Po rekonstrukci', 'vlastnictvi': 'Osobní', 'podlazi': '1. podlaží z celkem 4', 'uzitna_plocha': 18, 'plocha_podlahova': 18, 'energeticka_narocnost_budovy': 'Třída G - Mimořádně nehospodárná', 'vybaveni': 1}


# def compare_dicts(new_dict, original_dict):
#     values_to_update = {}
#     for key, value in new_dict.items():
#         # print(f"New dict: {key} : {value}")
#         if original_dict.get(key) != value:
#             values_to_update[key] = value
#     return values_to_update


# print(compare_dicts(page_dict_new, page_dict))


# with pymongo.MongoClient("mongodb://127.0.0.1:27017/") as mongoClient:
#     propsColection = mongoClient["props_db"]["properties"]
#     # for result in results:
#     # page = Parser(result.html.html, result.html.url)
#     # page_dict = page.get_dict()
#     if isinstance(page_dict_new, dict):
#         # x = propsColection.insert_one(page_dict)
#         # print(x.inserted_id)
#         # x = propsColection.find_one(page_dict)
#         # print(x)                                                                                                                    
#         doc_id = page_dict_new["_id"]
#         del page_dict_new["_id"]

#         # print({ **page_dict, **{"created_at_utc": datetime.utcnow()}})

#         x = propsColection.update_one(
#             {"_id": doc_id}, 
#             {
#                 "$setOnInsert": {"created_at_utc": datetime.utcnow()}, 
#                 "$set": { **page_dict_new, **{"updated_at_utc": datetime.utcnow()}}
#             }, 
#             upsert=True)
#         print(x.raw_result)
# if not isinstance(page_dict, None):
#     propsColection.find()
#     propsColection.update_one(
#         {"_id": page_dict["_id"]},
#         {"$setOnInsert": {"created_at_utc": datetime.utcnow()},
#         {"$set": {"updated_at_utc": datetime.utcnow()}}},
#         upsert=True)
