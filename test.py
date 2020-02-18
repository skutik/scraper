import asyncio
import json
import collections.abc
import requests_html
import logging
import pymongo
from datetime import datetime
import os
import hashlib
from bs4 import BeautifulSoup
from src.parser import Parser
from src.scraper import Scraper
from multiprocessing import Manager
from math import ceil
import pyppeteer
import concurrent.futures

logging.getLogger().setLevel(logging.DEBUG)

"""
Test Queue
"""
async def _fetch_data(url, semaphore, page_type, timeout, queue):
    async with semaphore:
        url, page = _get_page(url=url, timeout=timeout)
        if page:
            pass
        else:
            queue.put()

async def _generate_items_pages(url, timeout=30):
    x = await _get_page(url, timeout)
    logging.info(x)
    return x

async def _generate_items_pages_run(default_url, queue, params={}, timeout=30):
    url, page = await _get_page(default_url, timeout, params)
    if page:
        parser = Parser(url=url, html=page.html.html)
        [queue.put_nowait(url+f"strana={n}") for n in range(2, parser.get_total_properties_count() + 1)]
        logging.info(f"Generated pages with items. Current count {queue.qsize()}")
        [queue.put_nowait("https://www.sreality.cz"+f"{prop}") for prop in parser.get_properties_links()]
        logging.info(f"Added {len(parser.get_properties_links())} links from first page. Current count {queue.qsize()}")

async def _get_page(url, timeout=30, params={}):
    asession = requests_html.AsyncHTMLSession()
    logging.info(f"Processing {url}")
    page = None
    url = url
    response = await asession.get(url, params=params)
    # try:
    await response.html.arender(timeout=timeout)
    page = response
    url = page.url
    logging.info(url)
    response.close()
    # except pyppeteer.errors.TimeoutError as error:
    # logging.info(f"During rendering {url} occurred error {error}")
    # finally:
    await asession.close()
    return url, page

async def worker(id, queue):
    while not queue.empty():
        item = queue.get_nowait()
        logging.info(f"Taks {id} processing {item}")
        if isinstance(item, tuple):
            url, page = await _get_page(item[0], params=item[1])
        else:
            url, page = await _get_page(item)
        if page:
            if "hledani" in url:
                parser = Parser(page.html.html, url)
                logging.info(f"Get URL: {url}")
                if "strana=1" in url:
                    [queue.put_nowait((url, {"velikost": ",".join(["1+1", "1+kk"]), "strana": n})) for n in range(2, parser.get_total_properties_count() + 1)]
                links = parser.get_properties_links()
                [queue.put_nowait("https://www.sreality.cz"+f"{link}") for link in links]
                logging.info(links)
                logging.info(f"{id} - Added {len(links)} to queue, total count {queue.qsize()}")
            else:
                parser = Parser(page.html.html, url)
                prop = parser.property_dict
                logging.info(f"{id} got property {prop}")


#
def runner():
    queue = asyncio.Queue()
    logging.info("Start main!")
    url, page = asyncio.run(_generate_items_pages("https://www.sreality.cz/hledani/prodej/byty/praha"))
    _generate_items_pages_run("https://www.sreality.cz/hledani/pronajem/byty/praha-6?velikost=1%2B1,1%2Bkk", queue)

    determine the first page


    logging.info(f"Queue count of itmes: {queue.qsize()}")

    links = ['/detail/pronajem/byt/1+kk/praha-brevnov-patockova/1664409180',
                '/detail/pronajem/byt/1+kk/praha-brevnov-belohorska/2047069788',
                '/detail/pronajem/byt/1+kk/praha-vokovice-k-lanu/1564528220',
                '/detail/pronajem/byt/1+kk/praha-vokovice-kratky-lan/2988432988',
                '/detail/pronajem/byt/1+kk/praha-repy-karlovarska/2819214940',
                '/detail/pronajem/byt/1+1/praha-praha-6-na-petynce/3725053532',
                '/detail/pronajem/byt/1+kk/praha-brevnov-patockova/134536796',
                '/detail/pronajem/byt/1+kk/praha-brevnov-talichova/3073429084',
                '/detail/pronajem/byt/1+kk/praha-ruzyne-kralupska/2457325148',
                '/detail/pronajem/byt/1+kk/praha-dejvice-v-sareckem-udoli/2414464604',
                '/detail/pronajem/byt/1+kk/praha-dejvice-koulova/3972255324',
                '/detail/pronajem/byt/1+kk/praha-brevnov-slikova/3129003612',
                '/detail/pronajem/byt/1+1/praha-dejvice-komornicka/1511509596',
                '/detail/pronajem/byt/1+1/praha-praha-6-na-petynce/3830959708',
                '/detail/pronajem/byt/1+1/praha-ruzyne-kralupska/607047260',
                '/detail/pronajem/byt/1+kk/praha-ruzyne-kralupska/183357020',
                '/detail/pronajem/byt/1+kk/praha-dejvice-zemedelska/550686300',
                '/detail/pronajem/byt/1+kk/praha-vokovice-vokovicka/3907505756',
                '/detail/pronajem/byt/1+kk/praha-dejvice-lindleyova/2362560092',
                '/detail/pronajem/byt/1+1/praha-bubenec-ve-struhach/2085670492']

    [queue.put_nowait("https://www.sreality.cz"+f"{link}")for link in links]

    put default value
    queue.put_nowait(("https://www.sreality.cz/hledani/pronajem/byty/praha-6", {"velikost": ",".join(["1+1", "1+kk"]),
                                                                                "strana": 1}))

    w = worker(queue)

    asyncio.run(worker(queue))

    loop = asyncio.get_event_loop()
    logging.info("Started loop.")
    loop.run_until_complete(_generate_items_pages_run("https://www.sreality.cz/hledani/pronajem/byty/praha-6", queue, {"velikost": ",".join(["1+1", "1+kk"]),
                                                                                "strana": 1}))
    loop.run_until_complete(asyncio.wait([worker(f"worker{n_worker}", queue) for n_worker in range(1, 4)]))
    loop.close()
    oop = asyncio.set_event_loop(asyncio.get_event_loop())
    loop.run_until_complete(_generate_items_pages("https://www.sreality.cz/hledani/prodej/byty/praha"))
    loop.close()
    l

runner()

"""
Test Asyncio vs Multiprocessing
"""
# def get_property_pages(url, timeout=30, params=None, headers=None):
#     if headers is None:
#         headers = {}
#     if params is None:
#         params = {}
#     with requests_html.HTMLSession() as session:
#         response = session.get(url, params=params, headers=headers)
#         logging.info(response.url)
#         if response.status_code == 200:
#             response.html.render(timeout=timeout)
#             page = BeautifulSoup(response.html.html, "html.parser")
#             if not page.find("p", class_="status-text ng-binding"):
#                 props_count = page.findAll("span", class_="numero ng-binding")
#                 if props_count:
#                     try:
#                         props_count = int(props_count[-1:][0].text.replace(u"\xa0", ""))
#                         return ceil(props_count / 20)
#                     except TypeError:
#                         raise ("Value cannot be converted to string")
#                 else:
#                     return 1
#             else:
#                 return 0
#
# async def async_get_property_pages(url, timeout=30, params=None, headers=None):
#     if headers is None:
#         headers = {}
#     if params is None:
#         params = {}
#     if params is None:
#         params = {}
#     asession = requests_html.AsyncHTMLSession()
#     logging.info(f"Processing {url}")
#     page = None
#     url = url
#     response = await asession.get(url, params=params)
#     # try:
#     await response.html.arender(timeout=timeout)
#     page = BeautifulSoup(response.html.html, "html.parser")
#     await asession.close()
#     if not page.find("p", class_="status-text ng-binding"):
#         props_count = page.findAll("span", class_="numero ng-binding")
#         if props_count:
#             try:
#                 props_count = int(props_count[-1:][0].text.replace(u"\xa0", ""))
#                 return ceil(props_count / 20)
#             except TypeError:
#                 raise ("Value cannot be converted to string")
#         else:
#             return 1
#     else:
#         return 0
#
#
#
# def fetch_data(url, params=None):
#     if params is None:
#         params = {}
#     with requests_html.HTMLSession() as session:
#         logging.info(f"Processing {url}")
#         page = None
#         url = url
#         response = session.get(url, params=params)
#         logging.info(f"Response URL {response.url}")
#         # try:
#         logging.info("Start rendering")
#         response.html.render()
#         logging.info("End rendering")
#         page = response.html.html
#         url = response.html.url
#         logging.info("Rendering end successfully!")
#         # except pyppeteer.errors.TimeoutError as error:
#         #     print(error)
#         #     logging.info(f"During rendering {url} occurred error {error}")
#         # finally:
#         logging.info("Finally section!")
#         return url, page
#
# async def async_fetch_data(url, timeout=30, params=None):
#     if params is None:
#         params = {}
#     asession = requests_html.AsyncHTMLSession()
#     logging.info(f"Processing {url}")
#     page = None
#     url = url
#     response = await asession.get(url, params=params)
#     # try:
#     await response.html.arender(timeout=timeout)
#     page = response.html.html
#     url = response.html.url
#     response.close()
#     # except pyppeteer.errors.TimeoutError as error:
#     # print(error)
#     # logging.info(f"During rendering {prop} occurred error {error}")
#     # finally:
#     await asession.close()
#     return url, page
#
# def process_list_pages(url, params=None):
#     if params is None:
#         params = {}
#     pages_count = get_property_pages(url, timeout=60, params=params)
#     logging.info(f"Pages count: {pages_count}")
#     # pages_to_parse = ["https://www.sreality.cz/hledani/pronajem/byty"for page_number in range(pages_count)]
#     with concurrent.futures.ProcessPoolExecutor() as executor:
#         # result = run_in_executor(executor, async_fetch_data, url, 30, params)
#         # logging.info(result)
#         # return result
#         # tasks = [loop.run_in_executor(executor, async_fetch_data, url, 60, {**params, **{"strana": page_number}}) for page_number in range(1, pages_count + 1)]
#         # logging.info(tasks)
#         # results = await loop.run_in_executor(executor, )
#         results = [executor.submit(fetch_data, url, params={**params, **{"strana": page_number}}) for page_number in
#                    range(1, pages_count + 1)]
#
#         # results = await asyncio.gather(*tasks)
#
#         # return results
#         for result in concurrent.futures.as_completed(results):
#             logging.info(f"operation result {result.result()}")
#
#
# # process_list_pages("https://www.sreality.cz/hledani/pronajem/byty/praha-5", {"velikost": "4+1"})
#
# def main(url, params=None):
#     if params is None:
#         params = {}
#     loop = asyncio.get_event_loop()
#     return loop.run_until_complete(process_list_pages(url, params))
#
# print(process_list_pages("https://www.sreality.cz/hledani/pronajem/byty/praha-5", {"velikost": "4+1"}))

"""
Other tests
"""

# print(fetch_data("https://www.sreality.cz/hledani/pronajem/byty/praha-5?velikost=4%2B1&strana=2"))

# pages_count = get_property_pages("https://www.sreality.cz/hledani/pronajem/byty/praha-5?velikost=4%2B1")
# if pages_count > 0:
#     queue = asyncio.Queue()
#     [queue.put(url + "") for page_number in range(pages_count)]
#     logging.info(queue)


# prop = {
#     "cena_text": "54 000 Kc\u030c za me\u030csi\u0301c",
#     "cena": 54000,
#     "lokace": "Jana\u0301c\u030ckovo na\u0301br\u030cez\u030ci\u0301, Praha 5 - Smi\u0301chov",
#     "url": "https://www.sreality.cz/detail/pronajem/byt/4+1/praha-smichov-janackovo-nabrezi/3021536860",
#     "typ_smlouvy": "pronajem",
#     "typ_nemovitosti": "byt",
#     "aktivni": True,
#     "celkova_cena": "54 000 Kc\u030c za me\u030csi\u0301c, bez poplatku\u030a",
#     "poznamka_k_cene": "+ sluz\u030cby 4.000,- Kc\u030c/me\u030csi\u0301c + poplatky (elektr\u030cina a plyn)",
#     "id": "A09618",
#     "aktualizace": "19.12.2019",
#     "stavba": "Cihlova\u0301",
#     "stav_objektu": "Velmi dobry\u0301",
#     "vlastnictvi": "Osobni\u0301",
#     "podlazi": "4. podlaz\u030ci\u0301",
#     "uzitna_plocha": 21312313132,
#     "plocha_podlahova": 181,
#     "sklep": 1,
#     "energeticka_narocnost_budovy": "Tr\u030ci\u0301da G - Mimor\u030ca\u0301dne\u030c nehospoda\u0301rna\u0301 c\u030c. 78/2013 Sb. podle vyhla\u0301s\u030cky",
#     "vybaveni": 0,
#     "vytah": 1,
#     "typ_bytu": "Mezonet",
#     "created_at_utc": "2020-01-01 15:45:48.591887",
#     "last_update_utc": "2020-01-01 15:45:48.591905"
#   }
#
# def id_hash(input_string):
#     hash_object = hashlib.sha1(input_string.encode())
#     return hash_object.hexdigest()
#
# def compare_dicts(new_dict, original_dict):
#     values_to_update = {}
#     for key, value in new_dict.items():
#         if original_dict.get(key) != value:
#             values_to_update[key] = value
#     return values_to_update
#
# def update_dict(d, u):
#     for k, v in u.items():
#         if isinstance(v, collections.abc.Mapping):
#             d[k] = update_dict(d.get(k, {}), v)
#         else:
#             d[k] = v
#     return d
#
#
#
# org = {"a": 1, "b":True, "c": {"x":1}}
# new = {"c": {"x":2}}
#
# print(compare_dicts(new, org))
# print({**org, **compare_dicts(new, org)})
#
# with open("backup/props_backup.json", "r+") as backup_file:
#     doc_id = id_hash(prop["url"])
#     try:
#         current_backup = json.loads(backup_file.read())
#     except json.decoder.JSONDecodeError:
#         current_backup = dict()
#     updated_backup = dict()
#     print(current_backup.keys())
#     if doc_id in current_backup:
#         updated_backup = update_dict(current_backup, {doc_id:prop})
#     else:
#         updated_backup = current_backup
#         print(updated_backup)
#         updated_backup[doc_id] = prop
#         print(updated_backup)
#         updated_backup[doc_id]["created_at_utc"] = str(datetime.utcnow())
#     updated_backup[doc_id]["last_update_utc"] = str(datetime.utcnow())
#     print(updated_backup)
#     backup_file.seek(0)
#     backup_file.write(json.dumps(updated_backup))
#     backup_file.truncate()


#
# def upsert_properties(mongoCollection, record_dict):
#     doc_id = id_hash(record_dict["url"])
#     x = mongoCollection.update_one(
#         {"_id": doc_id},
#         {
#             "$setOnInsert": {"created_at_utc": datetime.utcnow(), "inserted_at_utc": datetime.utcnow()},
#             "$set": {**record_dict, **{"last_update_utc": datetime.utcnow()}}
#         },
#         upsert=True)
#     return x.raw_result
#
# with requests_html.HTMLSession() as session:
#     response = session.get("https://www.sreality.cz/detail/pronajem/byt/4+1/praha-smichov-horejsi-nabrezi/3946573404")
#     if response.status_code == 200:
#         response.html.render(timeout=30)
#         parser = Parser(response.html.html, "https://www.sreality.cz/detail/pronajem/byt/4+1/praha-smichov-horejsi-nabrezi/3946573404")
#         print(parser.property_dict)

# HTML = """
# <!DOCTYPE html>
# <html>
# <body>
# <h1>Test links!</h1>
# <script>
# links = ["/proprery1", "/property2", "/property3"];
# links.forEach(function(item) {
#   var a = document.createElement('a');
#   var p = document.createElement('P');
#   var linkText = document.createTextNode("my title");
#   a.appendChild(linkText);
#   a.title = "my title text";
#   a.href = item;
#   a.className ="title";
#   p.appendChild(a);
#   document.body.appendChild(p);
# })
# </script>
# </body>
# </html>
# """

# page = requests_html.HTML(html=HTML)
# print(page.html)
# page.render()
# print(page.html)

# bs = BeautifulSoup(page.html, "html.parser")
# if bs.find_all("a", class_="title"):
#     [print(a["href"]) for a in bs.find_all("a", class_="title")]

# with open("tests/pages/list_of_adverts_raw.html", "r") as html_file:

#     html = requests_html.HTML(html=html_file.read())
#     html.render()
#     print(html.html)
# with requests_html.HTMLSession() as session:
#     response = session.get("https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/1267392092")
#     response.html.render()
#     print(response.status_code)
#     print(response.html.html)
#     html = response.html.html

# with open("tests/pages/list_of_adverts_raw.html", "w") as html_file:
#     with requests_html.HTMLSession() as session:
#         response = session.get("https://www.sreality.cz/hledani/pronajem/byty/praha?velikost=pokoj")
#         html_file.write(response.text)
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
