import json

class Parser():
    FILTERS_TO_IGNORE = [
        "distance",
        "special_price_switch",
        "czk_price_summary_order2",
        "region",
        "estate_age",
        "floor_number",
        "usable_area",
        "estate_area",
    ]
    def __init__(self):
        self.filters = self._parse_filters(self.get_filters())
        print(type(self.filters))

    def get_filters(self):
        with open("test_filters_file.json") as file:
            return json.loads(file.read())

    def _find_values(self, values_list):
        output_dict = {}
        for filter_dict in values_list:
            if filter_dict.get("values", []):
                output_dict.update(self._find_values(filter_dict["values"]))
            elif filter_dict.get("value", ""):
                output_dict[filter_dict["value"]] = {"name": filter_dict.get("name")}
                if filter_dict.get("key"):
                    output_dict[filter_dict["value"]].update({"key": filter_dict.get("key")})
        return output_dict

    def _parse_filters(self, categories_dict=dict):
        filters = dict()
        for filter_category, values in categories_dict.get(
                "linked_filters", dict()
        ).items():
            if filter_category not in self.FILTERS_TO_IGNORE:
                filters[filter_category] = {}
                filters[filter_category].update(
                    self._find_values(values.get("values", []))
                )
        for item in categories_dict.get("filters", {}).values():
            for values in item.values():
                for value_dict in values:
                    if value_dict.get("values"):
                        if not filters.get(value_dict["key"]):
                            filters[value_dict["key"]] = {}
                        filters[value_dict["key"]].update(
                            self._find_values(value_dict["values"])
                        )
        return filters

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

    @staticmethod
    def _parse_estate(property_dict: dict, map_dict=None):
        if not map_dict:
            map_dict = dict()
        property = {
            "available": True,
            "lon": property_dict["map"].get("lon", 0),
            "lat": property_dict["map"].get("lat", 0),
            "price_czk": property_dict["price_czk"].get("value_raw", 0),
            "price_czk_unit": property_dict["price_czk"].get("unit", ""),
            "category_main_cb": property_dict["seo"]["category_main_cb"],
            "category_sub_cb": property_dict["seo"]["category_sub_cb"],
            "category_type_cb": property_dict["seo"]["category_type_cb"],
            "seo_locality": property_dict["seo"]["locality"],
            "seo_params": property_dict["seo"],
            "locality": property_dict["locality"]["value"],
        }
        if property_dict.get("contact"):
            property["phone"] = (
                [
                    f"+{phone.get('code')}{phone.get('number')}"
                    for phone in property_dict["contact"]["phones"]
                ],
            )
            property["email"] = property_dict["contact"].get("email")
            property["seller_name"] = property_dict["contact"].get("user_name")
        else:
            property["seller_id"] = property_dict["_embedded"]["seller"]["user_id"]
            property["phone"] = [
                f"+{phone.get('code')}{phone.get('number')}"
                for phone in property_dict["_embedded"]["seller"]["phones"]
            ]
            property["seller_name"] = property_dict["_embedded"].get("user_name")
            property["email"] = property_dict["_embedded"].get("email")

        for item in property_dict["items"]:
            name = map_dict.get(item["name"], item["name"])
            if isinstance(item["value"], list):
                property[name] = [value["value"] for value in item["value"]]
            else:
                property[name] = item["value"]
            if item.get("currency"):
                property[f"{name}_currency"] = item["currency"]
            if item.get("unit"):
                property[f"{name}_unit"] = item["unit"]
            if item.get("notes"):
                property[f"{name}_notes"] = [note for note in item["notes"]]
        return property



if __name__ == "__main__":
    parser = Parser()
    print(json.dumps(parser.filters, indent=5))
    attributes = ['Stav objektu', 'Dražební vyhláška', 'Lodžie', 'ID', 'Náklady na bydlení', 'Aukční jistina', 'Termín 2. prohlídky', 'Telekomunikace', 'Stavba', 'Datum nastěhování', 'Podlaží', 'Doprava', 'Typ bytu', 'Stav', 'Poznámka k ceně', 'Původní cena', 'Datum konání dražby', 'Ukazatel energetické náročnosti budovy', 'Parkování', 'Bazén', 'Celková cena', 'Užitná plocha', 'Výtah', 'Zlevněno', 'Provize', 'Rok rekonstrukce', 'Druh dražby', 'Energetická náročnost budovy', 'Voda', 'Odpad', 'Vybavení', 'Výška stropu', 'Vlastnictví', 'ID zakázky', 'Komunikace', 'Cena', 'Umístění objektu', 'Bezbariérový', 'Garáž', 'Datum ukončení výstavby', 'Plocha podlahová', 'Elektřina', 'Plyn', 'Převod do OV', 'Posudek znalce', 'Sklep', 'Datum prohlídky', 'Terasa', 'Minimální příhoz', 'Aktualizace', 'Plocha zahrady', 'Balkón', 'Vyvolávací cena', 'Anuita', 'Termín 1. prohlídky', 'Znalecký posudek', 'Datum zahájení prodeje', 'Plocha zastavěná', 'Půdní vestavba', 'Místo konání dražby', 'Rok kolaudace', 'Průkaz energetické náročnosti budovy', 'Datum prohlídky do', 'Topení','Plocha zahrady', 'Zlevněno', 'Doprava', 'Aktualizace', 'Převod do OV', 'Průkaz energetické náročnosti budovy', 'Typ bytu', 'Odpad', 'Sklep', 'Podlaží', 'Plyn', 'Stavba', 'Plocha zastavěná', 'Datum ukončení výstavby', 'ID', 'Náklady na bydlení', 'Elektřina', 'Lodžie', 'Výška stropu', 'Celková cena', 'Topení', 'Voda', 'ID zakázky', 'Původní cena', 'Bezbariérový', 'Umístění objektu', 'Garáž', 'Stav', 'Půdní vestavba', 'Terasa', 'Komunikace', 'Užitná plocha', 'Parkování', 'Počet bytů', 'Provize', 'Telekomunikace', 'Vlastnictví', 'Ukazatel energetické náročnosti budovy', 'Energetická náročnost budovy', 'Balkón', 'Vybavení', 'Datum nastěhování', 'Stav objektu', 'Cena', 'Rok rekonstrukce', 'Výtah', 'Plocha podlahová', 'Poznámka k ceně', 'Rok kolaudace','Stav objektu', 'Znalecký posudek', 'Odpad', 'Telekomunikace', 'Umístění objektu', 'Původní cena', 'Parkování', 'Poloha domu', 'Podlaží', 'Náklady na bydlení', 'Termín 2. prohlídky', 'Minimální příhoz', 'Voda', 'ID zakázky', 'Počet bytů', 'Elektřina', 'Datum ukončení výstavby', 'Sklep', 'Cena', 'Provize', 'Plocha zahrady', 'Bazén', 'Topení', 'Stavba', 'Datum zahájení prodeje', 'Doprava', 'Rok kolaudace', 'Aktualizace', 'Plyn', 'Bezbariérový', 'Datum nastěhování', 'Místo konání dražby', 'Rok rekonstrukce', 'Plocha bazénu', 'Výtah', 'Průkaz energetické náročnosti budovy', 'Plocha pozemku', 'Ukazatel energetické náročnosti budovy', 'Dražební vyhláška', 'Celková cena', 'Vybavení', 'Aukční jistina', 'Druh dražby', 'Stav', 'Posudek znalce', 'Plocha zastavěná', 'Užitná plocha', 'Výška stropu', 'Komunikace', 'Garáž', 'Termín 1. prohlídky', 'Energetická náročnost budovy', 'Datum prohlídky', 'Poznámka k ceně', 'Plocha podlahová', 'Půdní vestavba', 'Zlevněno', 'Typ domu', 'ID', 'Datum konání dražby', 'Vyvolávací cena', 'Provize', 'Plocha zastavěná', 'Celková cena', 'Cena', 'Podlaží', 'Plocha podlahová', 'Rok rekonstrukce', 'Počet bytů', 'Garáž', 'Rok kolaudace', 'Stav objektu', 'Datum nastěhování', 'Stavba', 'Plocha zahrady', 'Voda', 'Ukazatel energetické náročnosti budovy', 'Odpad', 'Výtah', 'Typ domu', 'Bazén', 'Parkování', 'Aktualizace', 'Poznámka k ceně', 'ID zakázky', 'Náklady na bydlení', 'Bezbariérový', 'Doprava', 'Poloha domu', 'Datum prohlídky', 'Komunikace', 'Sklep', 'Plyn', 'Datum prohlídky do', 'Půdní vestavba', 'Plocha pozemku', 'Telekomunikace', 'Topení', 'Energetická náročnost budovy', 'Vybavení', 'Elektřina', 'Užitná plocha', 'Plocha bazénu', 'Umístění objektu', 'ID']
    attributes = set(attributes)
    print(len(attributes))
    print(attributes)