import requests
import logging
from datetime import datetime as dt
from math import ceil
import json
import asyncio
import aiohttp
logging.getLogger().setLevel(logging.DEBUG)

class ScraperV2():

    FILTERS_TO_IGNORE = ["distance", "special_price_switch", "czk_price_summary_order2", "region", "estate_age", "floor_number", "usable_area", "estate_area"]

    def __init__(self, category_main: int, category_type: int, category_sub=None, location_id=None, per_page=100, semaphore_limit=5):
        self.filters = self.parse_filters(self.fetch_filtes())
        logging.debug(self.filters)
        if str(category_main) in self.filters["category_main_cb"].values():
            self.category_main = category_main
        if str(category_main) in self.filters["category_type_cb"].values():
            self.category_type = category_type
        self.per_page = per_page
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(semaphore_limit)
        self.session = aiohttp.ClientSession()
        self.category_sub = category_sub
        self.location_id = location_id

    @property
    def _current_timestamp(self):
        return int(dt.utcnow().timestamp()*1000)

    def fetch_filtes(self):
        response = requests.get(f"https://www.sreality.cz/api/cz/v2/filters?tms={self._current_timestamp}")
        if response.status_code == 200:
            return json.loads(response.text, encoding="utf-8")

    def find_values(self, values_list):
        output_dict = {}
        for filter_dict in values_list:
            if filter_dict.get("values", []):
                output_dict.update(self.find_values(filter_dict["values"]))
            elif filter_dict.get("value", ""):
                output_dict[filter_dict["name"]] = filter_dict.get("value")
        return output_dict

    def parse_filters(self, categories_dict=dict):
        filters = dict()
        for filter_category, values in categories_dict.get("linked_filters",{}).items():
            if filter_category not in self.FILTERS_TO_IGNORE:
                filters[filter_category] = {}
                filters[filter_category].update(self.find_values(values.get("values", [])))
        for item in categories_dict.get("filters", {}).values():
            for values in item.values():
                for value_dict in values:
                    if value_dict.get("values"):
                        if not filters.get(value_dict["key"]):
                            filters[value_dict["key"]] = {}
                        filters[value_dict["key"]].update(self.find_values(value_dict["values"]))
        return filters

    # def get_filters(self):
    #     return self.parse_filters(categories_dict=self.fetch_filtes())

    @staticmethod
    def _parse_property_list(property_list_dict: dict):
        return [estate["hash_id"] for estate in property_list_dict["_embedded"]["estates"]], property_list_dict.get("result_size", 0)

    @staticmethod
    def _parse_estate(property_dict: dict):
        property = {
            "lon": property_dict["map"].get("lon", 0),
            "lat": property_dict["map"].get("lat", 0),
            "price_czk": property_dict["price_czk"].get("value_raw", 0),
            "price_czk_unit": property_dict["price_czk"].get("unit", ""),
            "category_main_cb": property_dict["seo"]["category_main_cb"],
            "category_sub_cb": property_dict["seo"]["category_sub_cb"],
            "category_type_cb": property_dict["seo"]["category_type_cb"],
            "locality": property_dict["seo"]["locality"]
        }
        logging.debug(property)
        return property

    async def _fetch_property_list(self, session, page=None):
        params = {"category_main_cb": self.category_main,
                  "category_type_cb": self.category_type,
                  "per_page": self.per_page,
                  "tms": self._current_timestamp}
        if page:
            params.update({"page": page})
        if self.location_id:
            params.update({"locality_region_id": self.location_id})
        if self.category_sub:
            params.update({"category_sub_cb": self.category_sub})
        async with self.session.get("https://www.sreality.cz/api/cs/v2/estates", params=params) as response:
            logging.debug(f"Processing URL {response.url}")
            if response.status == 200:
                response_payload = await response.text()
                return json.loads(response_payload, encoding="utf-8"), response.url
            else:
                raise Exception(f"{response.url} ended with status code {response.status}")

    async def _fetch_estate(self, hash_id):
        params = {"tms": self._current_timestamp}
        async with self.session.get("https://www.sreality.cz/api/cs/v2/estates/" + str(hash_id), params=params) as response:
            logging.debug(f"Processing URL {response.url}")
            if response.status == 200:
                response_payload = await response.text()
                return json.loads(response_payload, encoding="utf-8"), response.url
            else:
                raise Exception(f"{response.url} ended with status code {response.status}")

    async def _process_estate(self, hash_id):
        response_dict, _ = await self._fetch_estate(hash_id)
        self._parse_estate(response_dict)


    async def _process_estates_list(self, page=None, generate_list_producers=False):
        reposne_dict, _ = await self._fetch_property_list(self.session, page=page)
        estates, result_size = self._parse_property_list(reposne_dict)
        if generate_list_producers:
            logging.debug(f"Result size {result_size}")
            if result_size > self.per_page:
                [await self.produce_estates_list(func=self._process_estates_list, page=page_number) for page_number in range(2, ceil(result_size/self.per_page))]
        if estates:
            for estate in estates:
                await self.produce_estate(func=self._process_estate, hash_id=estate)

    async def produce_estates_list(self, func, **kwargs):
        logging.debug(f"{func} with kwargs {kwargs} adding to queue.")
        await self.queue.put((func, kwargs,))

    async def produce_estate(self, func, **kwargs):
        logging.debug(f"{func} with hash id {kwargs}")
        await self.queue.put((func, kwargs))

    async def _process_queue_item(self, item: tuple):
        logging.debug(f"Item {item} has been processed.")
        fnc, kwargs = item[0], item[1]
        await fnc(**kwargs)

    async def _consumer(self):
        while not self.queue.empty():
            item = await self.queue.get()
            logging.debug(f"Got item {item}")
            await self._process_queue_item(item)
            await asyncio.sleep(2)
            logging.debug(f"Processing of item {item} has finished.")

    async def _worker(self):
        await self.produce_estates_list(func=self._process_estates_list, generate_list_producers=True)
        await self._consumer()
        await self.session.close()

    def runner(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._worker())
        loop.close()


# response = requests.get(f"https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_sub_cb=2%7C3%7C7&category_type_cb=1&locality_region_id=10&page=3&per_page=20&tms={current_timestamp}")
# response = requests.get(f"https://www.sreality.cz/api/en/v2/estates/3252305500?tms={current_timestamp}")
# logging.debug(json.dumps(json.loads(response.content), indent=4))

s = ScraperV2(category_main=1, category_type=2, category_sub=47, location_id=12, semaphore_limit=3)
s.runner()