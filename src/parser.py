from bs4 import BeautifulSoup
import os
import logging
import unicodedata
import re
import unidecode

class Parser:
    def __init__(self, html, url, parser = "html.parser"):
        self.page = BeautifulSoup(html, parser)
        self.page_url = url

    def get_dict(self):
        page = self.page
        item = dict()
        if page.find("div", class_="params clear"):
            for ul in page.find("div", class_="params clear").findAll("ul"):
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
                    item[label] = value[0]
            item["adresa"] = page.find("span", class_="location-text ng-binding").text
            price_string = unicodedata.normalize("NFKD",page.find("span", class_="norm-price ng-binding").text)
            price = re.findall(r"\d+", price_string) # Convert page price s string to integer
            item["cena"] = int("".join(price))
            item["url"] = self.page_url
            # Change accents in keys to english letters and replace spaces e.g. "Celková cena" to "celkova_cena"
            item = {unidecode.unidecode(key).lower().replace(" ","_"): value  for key, value in item.items()} 
            return item
        else: 
            return None





