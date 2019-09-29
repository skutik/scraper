import requests
import logging
import requests_html
from time import time
import unicodedata
from bs4 import BeautifulSoup
import re

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

ENDPOINT_URL = "https://www.sreality.cz"
CITY = "praha"
SIZE = ["1+kk", "1+1", "pokoj"]

HEADERS = {
    "Referer": "https://www.sreality.cz/hledani/pronajem/byty/praha?1%2Bkk",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
}

PARAMS = {
    "velikost": ",".join(SIZE)
}

def createURL(endpoint, city="praha", ad_type="pronajem", property_type="byty"):
    if isinstance(city, list):
        city = ",".join([city])
    url = f"{endpoint}/hledani/{ad_type}/{property_type}/{city}"
    return url

def get_properties(url, headers, params={}):
    properties = set()
    counter = 1
    logging.info(params)
    while True:
        with requests_html.HTMLSession() as session:
            params["strana"] = counter
            response = session.get(url,
                                   headers=headers,
                                   params=params)
            logging.info(response.url)
            nextPage = False
            if response.status_code == 200:
                response.html.render()
                links = response.html.find("a")
                logging.info(links)
                if links:
                    for link in links:
                        link = str(link)
                        if " href='/detail/" in link:
                            property_link = [element.split("=")[1].replace("'", "") for element in link.split() if element.startswith("href='/detail/")][0]
                            properties.add(property_link)
                            logging.info(property_link)
                        elif "ng-class='{disabled: !pagingData.nextUrl}'" in link and "href='/hledani" in link:
                            nextPage = True
            else:
                raise(f"Got status code {response.status_code}")
            counter += 1
            if not nextPage:
                return properties
                break

def parse_property_page(soupObject, url):
    item = dict()
    soup = soupObject
    for ul in soup.find("div", class_="params clear").findAll("ul"):
        for li in ul.findAll("li"): 
            label = li.find("label").text[:-1]
            value = list()
            for span in li.findAll("span"):
                if span.get("ng-if") == "item.type == 'boolean-false'":
                    value = False
                elif span.get("ng-if") == "item.type == 'boolean-true'":
                    value = True
                elif span.text == 'm2':
                    pass
                else: 
                    value.append(unicodedata.normalize("NFKD",span.text))
            if isinstance(value, list):
                item[label] = " ".join(value)
            else:
                item[label] = value

    item["ad_id"] = url.split("/")[-1:][0]
    item["adress"] = soup.find("span", class_="location-text ng-binding").text
    price_string = unicodedata.normalize("NFKD",soup.find("span", class_="norm-price ng-binding").text)
    logging.info(price_string)
    price = re.findall(r"\d+", price_string)
    item["price_value"] = "".join(price)

    return item

async def get_properties_dict(properties):
    properties_dict = dict()
    for property in properties:
        url = ENDPOINT_URL + property
        logging.info(url)
        async with requests_html.AsyncHTMLSession() as asession:
            response = await asession.get(url, headers=HEADERS)
            response.html.render()
            soup = BeautifulSoup(str(response.html.element), "html.parser")
        proterty_dict = parse_property_page(soup, url)
        properties_dict[proterty_dict.get("ad_id")] = proterty_dict
    return properties_dict

url = createURL(ENDPOINT_URL, city="praha-1")
logging.info(url)
properties = get_properties(url, headers=HEADERS, params=PARAMS)
properties = get_properties_dict(properties)
# properties = get_properties_dict(["/detail/pronajem/byt/1+kk/praha-nove-mesto-na-struze/3262574172"])
print(properties)