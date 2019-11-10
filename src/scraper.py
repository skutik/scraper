import requests_html
from bs4 import BeautifulSoup

class Scraper():

    ENDPOINT_URL = "https://www.sreality.cz"
    HEADERS = {
        "Referer": "https://www.sreality.cz/hledani/pronajem/byty/praha?1%2Bkk",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }

    def __init__(self, city, size, search_type="pronajem", property_type = "byty", headers=HEADERS):
        self.city = city
        self.headers = headers
        self.search_type = search_type
        self.property_type = property_type
        self.property_type = property_type
        if isinstance(size, str):
            size = [size]
        self.params = {"velikost": ",".join(size)}


    def _generate_url(self):
        if isinstance(self.city, list):
            self.city = ",".join([self.city])
        return f"{self.ENDPOINT_URL}/hledani/{self.search_type}/{self.property_type}/{self.city}"


    def get_properties(self):
        url = self._generate_url()
        properties = set()
        counter = 1
        while True:
            with requests_html.HTMLSession() as session:
                self.params["strana"] = counter
                response = session.get(url, headers=self.headers, params=self.params)
                if response.status_code == 200:
                    response.html.render()
                    page = BeautifulSoup(response.html.html, "html.parser")
                    if page.find_all("a", class_="title"):
                        [properties.add(a["href"]) for a in page.find_all("a", class_="title")]
                    if page.find_all("a", class_="btn-paging-pn icof icon-arr-right paging-next"):
                        counter += 1
                    else:
                        return properties