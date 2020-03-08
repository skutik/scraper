import requests_html
from bs4 import BeautifulSoup
import asyncio
import pymongo
from src.parser import Parser
from datetime import datetime
import logging
import pyppeteer
import os
import hashlib
import json
import collections.abc


class Scraper():
    ENDPOINT_URL = "https://www.sreality.cz"
    HEADERS = {
        "Referer": "https://www.sreality.cz/hledani/pronajem/byty/praha?1%2Bkk",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }

    MONGODB_CONN_STRING = f"mongodb+srv://rw_dave:{os.getenv('MONGODB_RW_PASS')}@cluster0-6lpd8.mongodb.net/test?retryWrites=true&w=majority"

    def __init__(self, city=None, size=None, search_type="pronajem", property_type="byty", headers=HEADERS):
        if city:
            if isinstance(city, str):
                city = [city]
            self.city = ",".join(city)
        else:
            self.city = city
        self.headers = headers
        self.search_type = search_type
        self.property_type = property_type
        self.property_type = property_type
        if size:
            if isinstance(size, str):
                size = [size]
            self.params = {"velikost": ",".join(size)}
        else:
            self.params = dict()

    @property
    def _generate_url(self):
        if isinstance(self.city, list):
            self.city = ",".join([self.city])
        return f"{self.ENDPOINT_URL}/hledani/{self.search_type}/{self.property_type}/{self.city}" if self.city else f"{self.ENDPOINT_URL}/hledani/{self.search_type}/{self.property_type}"

    def _get_properties(self):
        url = self._generate_url
        properties = set()
        counter = 1
        while True:
            with requests_html.HTMLSession() as session:
                self.params["strana"] = counter
                response = session.get(
                    url, headers=self.headers, params=self.params)
                logging.info(response.url)
                if response.status_code == 200:
                    response.html.render(timeout=30)
                    page = BeautifulSoup(response.html.html, "html.parser")
                    if page.find_all("a", class_="title"):
                        [properties.add(a["href"])
                         for a in page.find_all("a", class_="title")]
                    if page.find_all("a", class_="btn-paging-pn icof icon-arr-right paging-next"):
                        counter += 1
                    else:
                        return properties
                else:
                    return properties

    def _id_hash(self, input_string):
        hash_object = hashlib.sha1(input_string.encode())
        return hash_object.hexdigest()

    def _upsert_properties(self, mongoCollection, record_dict):
        doc_id = self._id_hash(record_dict["url"])
        x = mongoCollection.update_one(
            {"_id": doc_id},
            {
                "$setOnInsert": {"created_at_utc": datetime.utcnow(), "inserted_at_utc": datetime.utcnow()},
                "$set": {**record_dict, **{"last_update_utc": datetime.utcnow()}}
            },
            upsert=True)
        return x.raw_result

    # https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    def _update_dict(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self._update_dict(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _backup_properties(self, backup_file, record_dict):
        doc_id = self._id_hash(record_dict["url"])
        if "/" in backup_file:
            directory = backup_file.split("/")[0] + "/"
            if not os.path.exists(directory):
                os.mkdir(directory)
        if not os.path.isfile(backup_file):
            open(backup_file, "w").close()  # Touch file if not exists

        with open(backup_file, "r+") as backup_file:
            try:
                current_backup = json.loads(backup_file.read())
            except json.decoder.JSONDecodeError:
                current_backup = dict()
            doc_id = self._id_hash(record_dict["url"])
            if doc_id in current_backup:
                updated_backup = self._update_dict(current_backup, {doc_id: record_dict})
            else:
                updated_backup = current_backup
                updated_backup[doc_id] = record_dict
                updated_backup[doc_id]["created_at_utc"] = str(datetime.utcnow())
            updated_backup[doc_id]["last_update_utc"] = str(datetime.utcnow())
            backup_file.seek(0)
            backup_file.write(json.dumps(updated_backup))
            backup_file.truncate()

    async def _fetch_data(self, prop, semaphore, timeout):
        async with semaphore:
            asession = requests_html.AsyncHTMLSession()
            logging.info(f"Processing {prop}")
            page = None
            url = prop
            response = await asession.get(prop)
            try:
                await response.html.arender(timeout=timeout)
                page = response
                response.close()
            except pyppeteer.errors.TimeoutError as error:
                print(error)
                logging.info(f"During rendering {prop} occurred error {error}")
               finally:
                await asession.close()
                return url, page

    async def _run(self, propties_list, timeout=20):
        semaphore = asyncio.Semaphore(2)
        tasks = [asyncio.ensure_future(self._fetch_data(
            adv, semaphore, timeout)) for adv in propties_list]
        return await asyncio.gather(*tasks)

    def run(self):
        properties = self._get_properties()
        properties = [self.ENDPOINT_URL + url for url in properties]
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self._run(properties))
        results = loop.run_until_complete(future)
        with pymongo.MongoClient(self.MONGODB_CONN_STRING) as mongoClient:
            propsColection = mongoClient["test_db"]["props"]
            for url, page in results:
                if page:
                    parser = Parser(page.html.html, page.html.url)
                    page = parser.property_dict
                else:
                    page = {"aktivni": False, "url": url}
                try:
                    status = self._upsert_properties(propsColection, page)
                    logging.info(status)
                except pymongo.errors.ServerSelectionTimeoutError as timeout:
                    logging.info(f"Error has occurred: {timeout}")
                    self._backup_properties("backup/props_backup.json", page)
                    logging.info(f"Property added to backup file.")
                except pymongo.errors.OperationFailure as error:
                    logging.info(f"Error has occurred: {error}")
                    self._backup_properties("backup/props_backup.json", page)
                    logging.info(f"Property added to backup file.")

        # try:
        #     record = propsColection.insert_one(page_dict)
        #     print(f"ID of inserted record {record.inserted_id}")
        # except pymongo.errors.DuplicateKeyError:
