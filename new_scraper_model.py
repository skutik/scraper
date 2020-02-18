import requests
import logging
from datetime import datetime as dt
import json
logging.getLogger().setLevel(logging.DEBUG)

logging.debug(dt.utcnow().timestamp())

current_timestamp = int(dt.utcnow().timestamp()*1000)

class ScraperV2():

    UNNEEDED_FILTERS = ["distance", "special_price_switch", "czk_price_summary_order2", "region", "estate_age", "floor_number", "usable_area", "estate_area"]

    def __init__(self, category_main: int, category_type: int):
        self.filters = self.parse_filters(self.fetch_filtes())
        logging.debug(self.filters)
        if str(category_main) in self.filters["category_main_cb"].values():
            self.category_main = category_main
        if str(category_main) in self.filters["category_type_cb"].values():
            self.category_type = category_type




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
            if filter_category not in self.UNNEEDED_FILTERS:
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

    def parse_property_list(self, property_list_dict):
        pass

    def _compose_list_url(self, url_type):
        if url_type == 'list':
            pass
        elif url_type == 'property_detail':
            pass
        else:
            raise(f"Unsupported type {url_type}")

    def fetch_properties(self, per_page=100):
        response = requests.get("https://www.sreality.cz/api/cs/v2/estates",
                                params={"category_main_cb": self.category_main,
                                        "category_type_cb": self.category_type,
                                        "per_page": per_page,
                                        "tms": self._current_timestamp})
        if response.status_code == 200:
            response = json.loads(response.text)
            total_resutls = response.get("result_size")
            logging.debug(total_resutls)
            for estate in response["_embedded"]["estates"]:
                logging.debug(estate.get("hash_id"))

    def




# response = requests.get(f"https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_sub_cb=2%7C3%7C7&category_type_cb=1&locality_region_id=10&page=3&per_page=20&tms={current_timestamp}")
# response = requests.get(f"https://www.sreality.cz/api/en/v2/estates/3252305500?tms={current_timestamp}")
# logging.debug(json.dumps(json.loads(response.content), indent=4))

s = ScraperV2(category_main=1, category_type=2)
s.fetch_properties()