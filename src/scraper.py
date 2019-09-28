import requests
import logging
import requests_html
from time import time
from bs4 import BeautifulSoup

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

# def get_property_info(url):

property_url = "https://www.sreality.cz/detail/pronajem/byt/1+1/praha-nove-mesto-palackeho/2534137436"

# with requests_html.HTMLSession() as session:
#     response = session.get(property_url)
#     response.html.render()
#     ad_id = property_url.split("/")[-1:]
#     logging.info(ad_id)
#     soup = BeautifulSoup(str(response.html.element), "lxml")
#     logging.info(soup.find("div", class_="params_clear"))
#
#     logging.info(response.text)

with open("example.html") as file:
    soup = BeautifulSoup(file, "lxml")

logging.info(soup.find("div", class_="params clear"))

# url = createURL(ENDPOINT_URL, city="praha-1")
# logging.info(url)
# properties = get_properties(url, headers=HEADERS, params=PARAMS)
# logging.info(len(properties))
