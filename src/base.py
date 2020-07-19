import requests
import logging
from datetime import datetime as dt
from math import ceil
import json
import asyncio
import aiohttp
from src.mongo_interface import MongoInterface
from src.redis_interface import RedisInterface
from abc import ABC, abstractmethod
from src.request_parser import RequestParser

logging.getLogger().setLevel(logging.DEBUG)


class ScraperBase(object):
    def __init__(self):
        self.queue = asyncio.Queue()
        self.session = aiohttp.ClientSession()
        self.redis_cache = RedisInterface(host="localhost", port=6379)

        request_parser = RequestParser()
        args = request_parser.get_args()
        self.max_workers = args.workers
        self.test_env = args.debug
        self.mongo_client = MongoInterface(test_enviroment=self.test_env)
        self.filters = args.filters
        if args.filters:
            return
        if not all([args.cat_main, args.cat_type]):
            raise ValueError(
                "Missing one or more required params (`cat_main`, `cat_type`)"
            )
        self.category_main = args.cat_main
        self.category_type = args.cat_type
        self.category_sub = args.cat_sub
        self.location_id = args.loc_id
        self.locality_region = args.loc_region

    @staticmethod
    @abstractmethod
    def _parse_property_list(property_list_dict: dict) -> list:
        pass

    @abstractmethod
    def _generate_estate_url(self, **kwargs) -> str:
        pass

    @abstractmethod
    def _parse_estate(self, property_dict: dict, map_dict=None, **kwargs) -> dict:
        pass

    @abstractmethod
    async def _fetch_property_list(self, page=None, **kwargs):
        pass

    @abstractmethod
    async def _fetch_estate(self, estate_id):
        pass

    async def _process_estate(self, hash_id):
        response_dict, status_code = await self._fetch_estate(hash_id)
        estate_dict = (
            self._parse_estate(response_dict, self.PROPERTY_ATTRIBUTES_MAP)
            if status_code == 200
            else response_dict
        )
        if estate_dict:
            if estate_dict.get("seo_params"):
                estate_dict["estate_url"] = self._generate_estate_url(
                    self.redis_cache.get_dict("filters"),
                    estate_dict["seo_params"],
                    self.URL_MAP,
                    hash_id,
                )
                # logging.debug(estate_dict["estate_url"])
            response = await self.mongo_client.upsert_property(
                str(hash_id), estate_dict
            )
            # logging.debug(response)

    @abstractmethod
    async def _process_estates_list(self, page=None, generate_list_producers=False):
        reposne_dict, _ = await self._fetch_property_list(page=page)
        estates, result_size = self._parse_property_list(reposne_dict)
        # logging.debug(estates)
        if generate_list_producers:
            logging.debug(f"Result size {result_size}")
            if result_size > self.per_page:
                [
                    await self._produce_estates_list(
                        func=self._process_estates_list, page=page_number
                    )
                    for page_number in range(2, (ceil(result_size / self.per_page)) + 1)
                ]
        if estates:
            for estate in estates:
                await self.produce_estate(func=self._process_estate, hash_id=estate)

    async def _produce_estates_list(self, func, **kwargs):
        logging.debug(f"{func} with kwargs {kwargs} adding to queue.")
        await self.queue.put((func, kwargs,))

    async def produce_estate(self, func, **kwargs):
        # logging.debug(f"{func} with hash id {kwargs}")
        await self.queue.put((func, kwargs))

    async def _consumer(self, consumer_id):
        while not self.queue.empty():
            item = await self.queue.get()
            logging.debug(f"Consumer {consumer_id} has got item {item} for processing")
            fnc, kwargs = item[0], item[1]
            await fnc(**kwargs)
            logging.debug(f"Consumer {consumer_id} has finished of item {item}.")

    async def _worker(self) -> None:
        # await self._update_filters()
        await self._process_estates_list(
            generate_list_producers=True
        )  # Gather information about other lists
        tasks = [
            asyncio.create_task(self._consumer(consumer_id))
            for consumer_id in range(1, self.max_workers + 1)
        ]
        await asyncio.gather(*tasks)
        self.mongo_client.close()
        await self.session.close()

    def runner(self) -> None:
        loop = asyncio.get_event_loop()
        if self.filters:
            self._update_filters_cache()
            loop.run_until_complete(self._update_filters())
            return
        loop.run_until_complete(self._worker())
        loop.close()
