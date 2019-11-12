from bs4 import BeautifulSoup
import os
import logging
import unicodedata
import re
import unidecode
from datetime import date

class Parser:
    def __init__(self, html, url, parser = "html.parser"):
        self.page = BeautifulSoup(html, parser)
        self.page_url = url

    def get_dict(self):
        page = self.page
        item = dict()
        if page.find("div", {"ng-show":"showedEntity.detail"}):
            item["nadpis"] = page.find("span", {"class":"ng-binding"}).text
            item["cena_text"] = page.find("span", {"class":"norm-price ng-binding"}).text
            item["cena"] = int("".join([char for char in page.find("span", {"class":"norm-price ng-binding"}).text if char.isdigit()]))
            item["lokace"] = page.find("span", {"class":"location-text ng-binding"}).text
            item["url"] = self.page_url
            item["typ_smlouvy"] = self.page_url.split("/")[4] if self.page_url.count("/") > 4 else None
            item["typ_nemovitosti"] = self.page_url.split("/")[5] if self.page_url.count("/") > 5 else None 
            for ul in page.find("div", class_="params clear").findAll("ul"):
                for li in ul.findAll("li", {"ng-repeat":"item in group.params"}):
                    label = li.find("label", {"class":"param-label ng-binding"}).text[:-1]
                    if li.find("span", {"class":"icof icon-ok ng-scope", "ng-if":"item.type == 'boolean-true'"}):
                        value = True
                    elif li.find("span", {"class":"icof icon-ok ng-scope", "ng-if":"item.type == 'boolean-false'"}):
                        value = False
                    elif li.find("span", {"class":"ng-binding ng-scope"}).text != "":
                        value = li.find("span", {"class":"ng-binding ng-scope"}).text
                        if label == "Aktualizace" and value == "Dnes":
                            value = date.today().strftime("%d.%m.%Y")
                    else:
                        value = str()
                    try:
                        item[label] = int(value)
                    except ValueError:
                        item[label] = value
            #Repalce accents with english letter, unicode values and replace spaces with underscores
            item = {unidecode.unidecode(key).lower().replace(" ","_"):(unicodedata.normalize("NFKD",value) if isinstance(value, str) else value) 
                        for key, value in item.items()}     
            return item
        else: 
            return None





