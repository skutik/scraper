import requests
import logging
from datetime import datetime as dt
from math import ceil
import json
import asyncio
import aiohttp
from src.mongo_interface import MongoInterface

logging.getLogger().setLevel(logging.DEBUG)


class Scraper:

    FILTERS_TO_IGNORE = [
        "distance",
        "special_price_switch",
        "czk_price_summary_order2",
        "region",
        "estate_age",
        "floor_number",
        "usable_area",
        "estate_area",
        "pois_in_place_distance"
    ]
    PROPERTY_ATTRIBUTES_MAP = {
        "Celková cena": "Total price",
        "ID zakázky": "Order ID",
        "Aktualizace": "Update",
        "Stavba": "Building",
        "Stav objektu": "Property status",
        "Vlastnictví": "Ownership",
        "Podlaží": "Floor",
        "Užitná plocha": "Usable area",
        "Plocha podlahová": "Floorage",
        "Balkón": "Balcony",
        "Energetická náročnost budovy": "Energy Performance Rating",
        "Vybavení": "Furnished",
        "Náklady na bydlení": "Cost of living",
        "Plyn": "Gas",
        "Odpad": "Waste",
        "Telekomunikace": "Telecommunications",
        "Elektřina": "Electricity",
        "Doprava": "Transportation",
        "Komunikace": "Road",
        "Topení": "Heating",
        "Voda": "Water",
        "Datum nastěhování": "Movein date",
        "Parkování": "Parking",
        "Terasa": "Terrase",
        "Anuita": "Annuity",
        "Termín 2. prohlídky": "2nd site visit date",
        "Druh dražby": "Type of auction",
        "Převod do OV": "Acquisition of title",
        "Datum prohlídky do": "Visit site date to",
        "Počet bytů": "Number of flats",
        "Lodžie": "Loggia",
        "Původní cena": "Original cost",
        "Zlevněno": "Discounted",
        "Posudek znalce": "Expert judgement",
        "Garáž": "Garage",
        "Datum prohlídky": "Visit site date",
        "Místo konání dražby": "Venue auction",
        "Půdní vestavba": "Loft",
        "Aukční jistina": "Auction principal",
        "Plocha zahrady": "Garden area",
        "Typ bytu": "Flat type",
        "Dražební vyhláška": "Advertisement of auction",
        "Rok rekonstrukce": "Reconstruction year",
        "Plocha bazénu": "Basin area",
        "Provize": "Commission",
        "Průkaz energetické náročnosti budovy": "Energy Performance Certificate",
        "Výtah":"Elevator",
        "Znalecký posudek":"Expert judgement",
        "Poloha domu":"Building situation",
        "Minimální příhoz":"Minimum Bid",
        "Umístění objektu":"Property location",
        "Termín 1. prohlídky":"1st site visit date",
        "Typ domu": "House type",
        "Rok kolaudace": "Final building approval year",
        "Datum zahájení prodeje":"Sales commencement date",
        "Datum konání dražby":"Auction sale date",
        "Bezbariérový":"Barrier-free access",
        "Sklep":"Cellar",
        "Vyvolávací cena":"Starting price",
        "Bazén":"Basin",
        "Poznámka k ceně":"Note on the price",
        "Výška stropu":"Ceiling height",
        "Plocha pozemku":"Land area",
        "Datum ukončení výstavby":"Construction completion date",
        "Stav":"Status",
        "Plocha zastavěná":"Built up area",
        "Cena":"Price",
        "Ukazatel energetické náročnosti budovy":"Energy Performance Indicator",
}
    URL_MAP = {
        "Prodej": "prodej",
        "Pronájem": "pronajem",
        "Dražby": "drazby",
        "6 a více": "6-a-vice",
        "Byty": "byt",
        "Domy": "dum",
        "Pozemky": "pozemek",
    }

    def __init__(
        self,
        category_main: int,
        category_type: int,
        category_sub=None,
        location_id=None,
        locality_region=None,
        per_page=100,
        test_enviroment=True,
        max_workers=5,
    ):
        self.filters = self._parse_filters(self._fetch_filtes())
        logging.debug(self.filters)
        if str(category_main) in self.filters["category_main_cb"].values():
            self.category_main = category_main
        if str(category_type) in self.filters["category_type_cb"].values():
            self.category_type = category_type
        if str(locality_region) in self.filters["locality_region_id"].values():
            self.locality_region = locality_region
        self.per_page = per_page
        self.queue = asyncio.Queue()
        self.session = aiohttp.ClientSession()
        self.category_sub = category_sub
        self.location_id = location_id
        self.max_workers = max_workers
        self.mongo_client = MongoInterface(test_enviroment=test_enviroment)

    #TODO: change for staticmethod
    @property
    def _current_timestamp(self):
        """
        Function takes current timestamp (in seconds) and convert it to milliseconds format.
        :return: Timestamp in milliseconds.
        """
        return int(dt.utcnow().timestamp() * 1000)

    def _fetch_filtes(self):
        """
        Function fetch available filters.
        :return: Dict with server response if status code is 200 (Success) else None.
        """
        response = requests.get(
            f"https://www.sreality.cz/api/cz/v2/filters?tms={self._current_timestamp}"
        )
        if response.status_code == 200:
            return json.loads(response.text, encoding="utf-8")

    @staticmethod
    def _convert_to_int(number):
        try:
            return int(number)
        except ValueError:
            return number

    def _find_values(self, values_list):
        output_dict = {}

        for filter_dict in values_list:
            if filter_dict.get("values", []):
                output_dict.update(self._find_values(filter_dict["values"]))
            elif filter_dict.get("value", ""):
                key = filter_dict["value"]
                if not isinstance(filter_dict["value"], str):
                    key = str(key)

                output_dict[key] = filter_dict.get("name")

        return output_dict

    def _parse_filters(self, categories_dict=dict):
        filters = dict()

        for filter_category, values in categories_dict.get(
            "linked_filters", {}
        ).items():

            if filter_category not in self.FILTERS_TO_IGNORE:
                filters[filter_category] = {}
                filters[filter_category].update(
                    self._find_values(values.get("values", []))
                )

        for item in categories_dict.get("filters", {}).values():
            for values in item.values():
                for value_dict in values:

                    if value_dict.get("values") and filters.get(value_dict["key"]) not in self.FILTERS_TO_IGNORE:

                        if not filters.get(value_dict["key"]):
                            filters[value_dict["key"]] = {}
                        filters[value_dict["key"]].update(
                            self._find_values(value_dict["values"])
                        )

        for filter in self.FILTERS_TO_IGNORE:
            if filter in filters:
                del filters[filter]

        return filters

    async def _update_filters(self):
        await self.mongo_client.upsert_filters(self.filters)

    @staticmethod
    def _parse_property_list(property_list_dict: dict):
        return (
            [
                estate["hash_id"]
                for estate in property_list_dict["_embedded"]["estates"]
            ],
            property_list_dict.get("result_size", 0),
        )

    def _generate_estate_url(self, filters_dict, seo_dict, values_map, hash_id):
        # logging.debug(filters_dict.get("category_main_cb"))
        # logging.debug([key for key, value in filters_dict.get("category_main_cb").items() if int(value) == seo_dict.get("category_main_cb")])
        cat_main = [
            key
            for key, value in filters_dict.get("category_main_cb").items()
            if value == str(seo_dict.get("category_main_cb"))
        ][0]
        cat_sub = [
            key
            for key, value in filters_dict.get("category_sub_cb").items()
            if value == str(seo_dict.get("category_sub_cb"))
        ][0]
        cat_type = [
            key
            for key, value in filters_dict.get("category_type_cb").items()
            if value == str(seo_dict.get("category_type_cb"))
        ][0]

        return f"https://www.sreality.cz/detail/{values_map.get(cat_type, cat_type)}/{values_map.get(cat_main, cat_main)}/{values_map.get(cat_sub, cat_sub).lower()}/{seo_dict.get('locality')}/{hash_id}"

    # @staticmethod
    def _parse_estate(self, property_dict: dict, map_dict=None):
        if not map_dict:
            map_dict = dict()
        property = {
            "available": True,
            "lon": property_dict.get("map", {}).get("lon", 0),
            "lat": property_dict.get("map", {}).get("lat", 0),
            "price_czk": property_dict["price_czk"].get("value_raw", 0),
            "price_czk_unit": property_dict["price_czk"].get("unit", ""),
            "category_main_cb": property_dict["seo"]["category_main_cb"],
            "category_sub_cb": property_dict["seo"]["category_sub_cb"],
            "category_type_cb": property_dict["seo"]["category_type_cb"],
            "seo_locality": property_dict["seo"]["locality"],
            "seo_params": property_dict["seo"],
            "locality": property_dict["locality"]["value"],
            "locality_district_id": property_dict["locality_district_id"]
        }
        if property_dict.get("contact"):
            if property_dict["contact"].get("phones"):
                property["phone"] = (
                    [
                        f"""{"+" + phone.get("code", "") if len(phone.get("code", "")) > 0 else phone.get("code", "")}{phone.get("number")}"""
                        for phone in property_dict["contact"]["phones"]
                    ],
                )
            property["email"] = property_dict["contact"].get("email")
            property["seller_name"] = property_dict["contact"].get("name")
        else:
            if property_dict["_embedded"].get("seller"):
                property["seller_id"] = property_dict["_embedded"]["seller"].get("user_id")
                property["phone"] = [
                    f"""{"+" + phone.get("code", "") if len(phone.get("code", "")) > 0 else phone.get("code", "")}{phone.get("number")}"""
                    for phone in property_dict["_embedded"]["seller"].get("phones", [])
                ]
                property["seller_name"] = property_dict["_embedded"]["seller"].get("user_name")
                property["email"] = property_dict["_embedded"]["seller"].get("email")
                if property_dict["_embedded"]["seller"].get("_embedded", {}).get("premise"):
                    premise_dict = property_dict["_embedded"]["seller"]["_embedded"]["premise"]
                    property["seller_website"] = premise_dict.get("www")
                    property["seller_company_id"] = premise_dict.get("company_id")
                    property["seller_company_name"] = premise_dict.get("name")
                    property["seller_company_email"] = premise_dict.get("email")
                    if property_dict.get("ask"):
                        property["seller_company_address"] = premise_dict["ask"].get("address")
                        property["seller_company_phones"] = [
                            f"""{"+" + phone.get("country_code", "") if len(phone.get("country_code", "")) > 0 else phone.get("country_code", "")}{phone.get("number")}"""
                            for phone in premise_dict["ask"].get("phones", [])
                        ]

        for item in property_dict["items"]:
            name = map_dict.get(item["name"], item["name"])
            if isinstance(item["value"], list):
                property[name] = [self._convert_to_int(value["value"]) for value in item["value"]]
            else:
                property[name] = self._convert_to_int(item["value"])
            if item.get("currency"):
                property[f"{name}_currency"] = item["currency"]
            if item.get("unit"):
                property[f"{name}_unit"] = item["unit"]
            if item.get("notes"):
                property[f"{name}_notes"] = [note for note in item["notes"]]
        logging.debug(property)
        return {key.replace(" ", "_").lower(): value for key, value in property.items()}

    async def _fetch_property_list(self, page=None):
        params = {
            "category_main_cb": self.category_main,
            "category_type_cb": self.category_type,
            "per_page": self.per_page,
            "tms": self._current_timestamp
        }
        if page:
            params.update({"page": page})
        if self.location_id:
            params.update({"locality_region_id": self.location_id})
        if self.category_sub:
            params.update({"category_sub_cb": self.category_sub})
        if self.locality_region:
            params.update({"locality_region_id": self.locality_region})
        async with self.session.get(
            "https://www.sreality.cz/api/cs/v2/estates", params=params
        ) as response:
            logging.debug(f"Processing URL {response.url}")
            if response.status == 200:
                response_payload = await response.text()
                return json.loads(response_payload, encoding="utf-8"), response.url
            else:
                raise Exception(
                    f"{response.url} ended with status code {response.status}"
                )

    async def _fetch_estate(self, hash_id):
        params = {"tms": self._current_timestamp}
        async with self.session.get(
            "https://www.sreality.cz/api/cs/v2/estates/" + str(hash_id), params=params
        ) as response:
            logging.debug(f"Processing URL {response.url}")
            if response.status == 200:
                response_payload = await response.text()
                print(response_payload)
                return json.loads(response_payload, encoding="utf-8"), response.status
            elif response.status == 410:
                logging.debug(f"Estate with id {hash_id} no longer exists.")
                return {"available": False}, response.status
            else:
                # raise Exception(f"{response.url} ended with status code {response.status}")
                return None, response.status

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
                    self.filters, estate_dict["seo_params"], self.URL_MAP, hash_id
                )
                logging.debug(estate_dict["estate_url"])
            response = await self.mongo_client.upsert_property(str(hash_id), estate_dict)
            logging.debug(response)

    async def _process_estates_list(self, page=None, generate_list_producers=False):
        reposne_dict, _ = await self._fetch_property_list(page=page)
        estates, result_size = self._parse_property_list(reposne_dict)
        logging.debug(estates)
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
        logging.debug(f"{func} with hash id {kwargs}")
        await self.queue.put((func, kwargs))

    async def _consumer(self, consumer_id):
        while not self.queue.empty():
            item = await self.queue.get()
            logging.debug(f"Consumer {consumer_id} has got item {item} for processing")
            fnc, kwargs = item[0], item[1]
            await fnc(**kwargs)
            logging.debug(f"Consumer {consumer_id} has finished of item {item}.")

    async def _worker(self):
        await self._update_filters()
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

    def runner(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._worker())
        loop.close()


# s = ScraperV2(category_main=1, category_type=2)
# s = Scraper(category_main=1, category_type=2, category_sub=47, max_workers=5, mongo_database="test_db", mongo_collection="props")
# print(s._fetch_filtes())
# s.runner()
