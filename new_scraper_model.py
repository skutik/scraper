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

    def __init__(self, category_main: int, category_type: int, category_sub=None, location_id=None, per_page=100, max_workers=5, semaphore_limit=5):
        self.filters = self.parse_filters(self.fetch_filtes())
        logging.debug(self.filters)
        if str(category_main) in self.filters["category_main_cb"].values():
            self.category_main = category_main
        if str(category_main) in self.filters["category_type_cb"].values():
            self.category_type = category_type
        self.per_page = per_page
        self.queue = asyncio.Queue()
        # self.semaphore = asyncio.Semaphore(semaphore_limit)
        self.session = aiohttp.ClientSession()
        self.category_sub = category_sub
        self.location_id = location_id
        self.max_workers = max_workers
        # self.tasks =

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

    async def _fetch_property_list(self, page=None):
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

    # async def _process_estates_list(self, page=None, generate_list_producers=False):
    #     reposne_dict, _ = await self._fetch_property_list(self.session, page=page)
    #     estates, result_size = self._parse_property_list(reposne_dict)
    #     logging.debug(estates)
    #     if generate_list_producers:
    #         logging.debug(f"Result size {result_size}")
    #         if result_size > self.per_page:
    #             [await self.produce_estates_list(func=self._process_estates_list, page=page_number) for page_number in range(2, ceil(result_size/self.per_page))]
    #     if estates:
    #         for estate in estates:
    #             await self.produce_estate(func=self._process_estate, hash_id=estate)

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

    async def test_fetch_estate(self, hash_id):
        params = {"tms": self._current_timestamp}
        async with self.session.get("https://www.sreality.cz/api/cs/v2/estates/" + str(hash_id), params=params) as response:
            logging.debug(f"Processing URL {response.url}")
            if response.status == 200:
                response_payload = await response.text()
                await asyncio.sleep(3)
                return json.loads(response_payload, encoding="utf-8"), response.url
            else:
                raise Exception(f"{response.url} ended with status code {response.status}")

    async def test_process_estate(self, hash_id):
        response_dict, _ = await self.test_fetch_estate(hash_id)
        self._parse_estate(response_dict)

    async def test_consumer(self, name, queue):
        logging.debug(queue.qsize())
        while not queue.empty():
            # async with self.semaphore:
            item = queue.get_nowait()
            fnc, kwargs = item[0], item[1]
            logging.debug(f"{name} processing function {fnc} with arguments: {kwargs}")
            await fnc(**kwargs)
            # self._process_queue_item(item)
            # await self.test_process_estate(item)
            await asyncio.sleep(3)
            logging.debug(f"{name} has finished processing of item {item}.")

    # async def test_process_estates_list(self, queue, page=None, generate_list_producers=False):
    #     reposne_dict, _ = await self._fetch_property_list(page=page)
    #     estates, result_size = self._parse_property_list(reposne_dict)
    #     logging.debug(estates)
    #     if generate_list_producers:
    #         logging.debug(f"Result size {result_size}")
    #         if result_size > self.per_page:
    #             [await self.produce_estates_list(func=self.test_produce_estates_list, queue=queue, page=page_number) for page_number in range(2, ceil(result_size/self.per_page))]
    #     if estates:
    #         for estate in estates:
    #             await self.produce_estate(func=self.test_process_estate, hash_id=estate)

    async def test_produce_estates_list(self, queue, func, **kwargs):
        logging.debug(f"{func} with kwargs {kwargs} adding to queue.")
        await queue.put((func, kwargs,))

    async def test_producer(self, ids, queue):
        for hash_id in ids:
            # await queue.put(hash_id)
            # await queue.put((self.test_process_estate, hash_id))
            await self.test_produce_estate(self.test_process_estate, hash_id=hash_id)

    async def test_produce_estate(self, func, queue, **kwargs):
        async with self.semaphore:
            logging.debug(f"{func} with hash id {kwargs}")
            await queue.put((func, kwargs))
            # await asyncio.sleep(2)

    def test_produce_estate_now_wait(self, func, queue, **kwargs):
            logging.debug(f"{func} with hash id {kwargs}")
            queue.put_nowait((func, kwargs))

    async def test_worker(self, id_list, queue):
        for id in id_list:
            self.test_produce_estate_now_wait(func=self.test_process_estate, queue=queue, hash_id=id)

        tasks = [asyncio.create_task(self.test_consumer(f"consumer-{i}", queue)) for i in range(1, self.max_workers + 1)]

        # await self.test_producer(id_list)
        # await self.test_process_estates_list(queue, generate_list_producers=True)
        # await self.test_producer(id_list, queue)
        # await self.test_consumer(queue)
        await asyncio.gather(*tasks)
        # tasks = [self.test_process_estate(hash_id) for hash_id in id_list]
        # await asyncio.gather(*tasks)
        # await self.test_consumer()
        # await self.session.close()

        # tasks = [self.test_process_estate(hash_id) for hash_id in id_list]
        # await asyncio.gather(*tasks)

    def runner(self):
        # logging.debug(self.semaphore)
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        test_estates = [3695627868, 2825797212, 4050570844, 2331233884, 1078148700, 2420325980, 3473817180, 945307228, 2151890524, 3762503260, 3263225436, 2179874396, 4143726172, 1383022172, 1241333340, 3703955036, 438685276, 548290140, 3422502492, 289619548, 2973974108, 3730652764, 2437103196, 1475165788, 4029169244, 2267270748, 4047715932, 3779280476, 3510845020, 105070172, 4002467420, 3797630556, 2407284316, 1701789276, 3162259036, 1447247452, 1178811996, 3218030172, 350477916, 927153756, 3326295644, 658718300, 121847388, 2319830620, 3176451676, 208354908, 3074637404, 2537766492, 3879943772, 1505611356, 3329179228, 2469150300, 1378631260, 608386652, 593677916, 509988444, 1950563932, 3842522716, 2802110044, 1145257564, 2374581852, 3024305756, 2755870300, 1827421788, 3850686044, 984075868, 2218999388, 3519626844, 893599324, 30162524, 104611420, 164380252, 1021918812, 1653919324, 1708445276, 2191343196, 2885566044, 3232579164, 3305848412, 3091648092, 356728412, 88292956, 1162034780, 746536540, 2772647516, 2504212060, 2235776604, 4114824796, 1684880988, 443760220, 2054372956, 1517502044, 3660631644, 3128114780, 2859679324, 2322808412, 4201856604, 440024668, 3664985692, 997408348]
        loop.run_until_complete(self.test_worker(test_estates, queue))
        # tasks = [asyncio.ensure_future(self._process_estate() for hash_id in propties_list]
        # loop.run_until_complete(self._worker())
        # loop.run_until_complete(self.test_worker(test_estates))
        loop.close()


# response = requests.get(f"https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_sub_cb=2%7C3%7C7&category_type_cb=1&locality_region_id=10&page=3&per_page=20&tms={current_timestamp}")
# response = requests.get(f"https://www.sreality.cz/api/en/v2/estates/3252305500?tms={current_timestamp}")
# logging.debug(json.dumps(json.loads(response.content), indent=4))

# s = ScraperV2(category_main=1, category_type=2)
s = ScraperV2(category_main=1, category_type=2, category_sub=47, location_id=12, semaphore_limit=5)
s.runner()