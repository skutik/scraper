import logging
import re
import yarl

from src.base import ScraperBase
from src.helpers import get_xpath_data, get_coordinates_by_address


class Scraper(ScraperBase):
    name = "IdnesReality"
    base_url = "https://reality.idnes.cz/"
    ESTATE_ATTRIBUTES_MAP = {
        "Číslo zakázky": "id",
        "Užitná plocha": "usable_area",
        "Cena": "price_string",
        "Konstrukce budovy": "building",
        "Stav bytu": "property_status",
        "Vlastnictví": "ownership",
        "Podlaží": "floor",
        "Počet podlaží budovy": "number_of_floors",
        "Plyn": "gas",
        "Topení": "heating",
        "Elektřina": "electricity",
        "Vybavení": "furnished",
        "PENB": "penb",
    }

    async def _fetch_property_list(self, page=None):
        params = {"page": page} if page else None

        async with self.session.get(
            "https://reality.idnes.cz/s/prodej/byty/okres-karvina/", params=params
        ) as response:
            if response.status == 200:
                return await response.text(), response.url
            else:
                raise Exception(
                    f"Fetching of {response.url} failed with status error {response.status}"
                )

    async def _parse_estate(self, estate_page, map_dict=None, url=None, **kwargs):
        map_dict = map_dict or {}
        logging.debug(f"Parsing estate with url {url}")
        address = get_xpath_data(estate_page, '//p[@class="b-detail__info"]')[0].text

        estate = {}
        lat, lon = await get_coordinates_by_address(self.session, address.strip())
        estate["provider"] = self.name
        estate["lon"] = float(lon) if lon else lon
        estate["lat"] = float(lat) if lat else lat
        price_info = get_xpath_data(
            estate_page,
            '//div[@class="wrapper-price-notes color-grey mb-5"]/span[last()]/strong',
        )
        estate["total_price_notes"] = price_info[0].text.strip() if price_info else None
        price_string = get_xpath_data(
            estate_page, '//p[@class="b-detail__price"]/strong'
        )[0].text.strip()
        estate["price_czk"] = (
            int("".join(re.findall(r"\d+", price_string.split("Kč")[0])))
            if price_string != "Cena na vyžádání"
            else None
        )
        estate["price_czk_unit"] = (
            price_string.split("/")[-1]
            if len(price_string.split("/")) > 1 and price_string != " Cena na vyžádání"
            else None
        )
        estate["seller_name"] = get_xpath_data(
            estate_page, '//h2[@class="b-author__title"]/a'
        )[0].get("text")
        company_name = get_xpath_data(
            estate_page, '//div[@class="b-author__content"]/p/a'
        )
        estate["seller_compapny_name"] = (
            company_name[0].get("text") if company_name else None
        )
        mail = get_xpath_data(estate_page, '//a[starts-with(@href, "mailto:")]')[0].get(
            "text"
        )
        estate["mail"] = mail[0].get("text") if mail else None
        phone = get_xpath_data(estate_page, '//a[starts-with(@href, "tel:")]')
        estate["phone"] = phone[0].get("text", "").replace(" ", "") if phone else None
        for attribute_name, value in zip(
            get_xpath_data(
                estate_page, '//div[@class="b-definition-columns mb-0"]/dl/dt'
            ),
            get_xpath_data(
                estate_page, '//div[@class="b-definition-columns mb-0"]/dl/dd'
            ),
        ):
            raw_attribute_name = attribute_name.text
            attribute_name = map_dict.get(raw_attribute_name, raw_attribute_name)
            self.unique_attributes.add(attribute_name)
            value = value.text
            estate[attribute_name] = value.strip()
        # logging.debug([element.text for element in get_xpath_data(estate_page, "//div[@class=\"b-definition-columns mb-0\"]/dl/dt")])
        return estate
        # exit(1)

    async def _fetch_estate(self, url):
        final_url = self.base_url + url
        async with self.session.get(url=final_url) as response:
            logging.debug(f"Processing URL {final_url}")
            if response.status == 200:
                return await response.text(), response.url
            else:
                return None, response.url

    async def _process_estate(self, url):
        response, estate_url = await self._fetch_estate(url=url)
        if not response:
            return
        estate_dict = await self._parse_estate(
            response, map_dict=self.ESTATE_ATTRIBUTES_MAP, url=estate_url
        )
        if estate_dict:
            estate_dict["url"] = (
                estate_url if not isinstance(estate_url, yarl.URL) else str(estate_url)
            )
        logging.debug(estate_dict)
        await self.mongo_client.upsert_property(str(estate_dict["id"]), estate_dict)

    async def _parse_property_list(self, list_html: str):
        property_links = get_xpath_data(
            list_html, '//a[@class="c-list-products__link"]'
        )
        last_page_element = get_xpath_data(
            list_html, '//a[@class="btn btn--border paging__item"][last()]/span'
        )
        last_page = int(last_page_element[0].text) if last_page_element else 0
        return [link_element.get("href") for link_element in property_links], last_page

    async def _process_estates_list(self, page=None, generate_list_producers=False):
        logging.debug(f"Page: {page}")
        response, _ = await self._fetch_property_list(page=page)
        estates_links, max_page = await self._parse_property_list(response)
        print(estates_links, max_page)
        if all([generate_list_producers, max_page]):
            [
                await self._produce_estates_list(
                    func=self._process_estates_list, page=page_number
                )
                for page_number in range(1, max_page)
            ]

        if estates_links:
            for link in estates_links:
                await self.produce_estate(func=self._process_estate, url=link)


if __name__ == "__main__":
    Scraper().runner()
