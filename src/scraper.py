import requests_html
from bs4 import BeautifulSoup
import asyncio
import pymongo
from src.parser import Parser
from datetime import datetime
import logging
import pyppeteer


class Scraper():

    ENDPOINT_URL = "https://www.sreality.cz"
    HEADERS = {
        "Referer": "https://www.sreality.cz/hledani/pronajem/byty/praha?1%2Bkk",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }

    def __init__(self, city, size, search_type="pronajem", property_type="byty", headers=HEADERS):
        self.city = city
        self.headers = headers
        self.search_type = search_type
        self.property_type = property_type
        self.property_type = property_type
        if isinstance(size, str):
            size = [size]
        self.params = {"velikost": ",".join(size)}

    def _generate_url(self):
        if isinstance(self.city, list):
            self.city = ",".join([self.city])
        return f"{self.ENDPOINT_URL}/hledani/{self.search_type}/{self.property_type}/{self.city}"

    def _get_properties(self):
        url = self._generate_url()
        properties = set()
        counter = 1
        while True:
            with requests_html.HTMLSession() as session:
                self.params["strana"] = counter
                response = session.get(
                    url, headers=self.headers, params=self.params)
                if response.status_code == 200:
                    response.html.render()
                    page = BeautifulSoup(response.html.html, "html.parser")
                    if page.find_all("a", class_="title"):
                        [properties.add(a["href"])
                         for a in page.find_all("a", class_="title")]
                    if page.find_all("a", class_="btn-paging-pn icof icon-arr-right paging-next"):
                        counter += 1
                    else:
                        return properties

    def _upsert_properties(mongoCollection, record_dict):
        doc_id = record_dict["_id"]
        del page_dict["_id"]
        x = propsColection.update_one(
            {"_id": doc_id},
            {
                "$setOnInsert": {"created_at_utc": datetime.utcnow()},
                "$set": {**page_dict, **{"last_update": datetime.utcnow()}}
            },
            upsert=True)
        return x.raw_result
        

    async def _fetch_data(self, prop, semaphore):
        async with semaphore:
            asession = requests_html.AsyncHTMLSession()
            print(f"Processing {prop}")
            page = None
            response = await asession.get(prop)
            try:
                await response.html.arender(timeout=2)
                page = response
                response.close()
            except pyppeteer.errors.TimeoutError as error:
                print(f"During rendering {prop} occurred error {error}")
            finally:
                await asession.close()
                return page

    async def _run(self, propties_list):
        semaphore = asyncio.Semaphore(2)
        tasks = [asyncio.ensure_future(self._fetch_data(
            adv, semaphore)) for adv in propties_list]
        return await asyncio.gather(*tasks)

    def run(self):
        properties = self._get_properties()
        properties = [self.ENDPOINT_URL + url for url in properties]
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self._run(properties))
        results = loop.run_until_complete(future)
        with pymongo.MongoClient("mongodb://127.0.0.1:27017/") as mongoClient:
            propsColection = mongoClient["props_db"]["properties"]
            for result in results:
                print(type(result))
                if result:
                    page = Parser(result.html.html, result.html.url)
                    page_dict = page.get_dict()
                    print(page)
                    if isinstance(page_dict, dict):
                        doc_id = page_dict["_id"]
                        del page_dict["_id"]
                        propsColection.update_one(
                            {"_id": doc_id},
                            {
                                "$setOnInsert": {"created_at_utc": datetime.utcnow()},
                                "$set": {**page_dict, **{"last_update": datetime.utcnow()}}
                            },
                            upsert=True)
        return f"Scraper finished."
        # try:
        #     record = propsColection.insert_one(page_dict)
        #     print(f"ID of inserted record {record.inserted_id}")
        # except pymongo.errors.DuplicateKeyError:
