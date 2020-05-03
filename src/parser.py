from bs4 import BeautifulSoup
import os
import logging
import unicodedata
import re
import unidecode
from datetime import date
from math import ceil


class Parser:
    def __init__(self, html, url, parser="html.parser"):
        self.page = BeautifulSoup(html, parser)
        self.page_url = url

    @property
    def property_dict(self):
        page = self.page
        item = dict()
        if page.find("div", {"ng-show": "showedEntity.detail"}):
            logging.info(self.page_url)
            item["cena_text"] = page.find(
                "span", {"class": "norm-price ng-binding"}
            ).text
            price = "".join(
                [
                    char
                    for char in page.find(
                        "span", {"class": "norm-price ng-binding"}
                    ).text
                    if char.isdigit()
                ]
            )
            item["cena"] = int(price) if price != "" else 0
            item["lokace"] = page.find(
                "span", {"class": "location-text ng-binding"}
            ).text
            item["url"] = self.page_url
            item["typ_smlouvy"] = (
                self.page_url.split("/")[4] if self.page_url.count("/") > 4 else None
            )
            item["typ_nemovitosti"] = (
                self.page_url.split("/")[5] if self.page_url.count("/") > 5 else None
            )
            item["aktivni"] = True
            for ul in page.find("div", class_="params clear").findAll("ul"):
                for li in ul.findAll("li", {"ng-repeat": "item in group.params"}):
                    label = li.find("label", {"class": "param-label ng-binding"}).text[
                        :-1
                    ]  # Takes attribute name without ':' at the end
                    if label.startswith("ID ") or label == "ID":
                        label = "id"  # Convert id of advertisement to "_id" used in Mongo DB as record PK
                    if li.find(
                        "span",
                        {
                            "class": "icof icon-ok ng-scope",
                            "ng-if": "item.type == 'boolean-true'",
                        },
                    ):  # Parse True value represented as check mark
                        value = True
                    elif li.find(
                        "span",
                        {
                            "class": "icof icon-cross ng-scope",
                            "ng-if": "item.type == 'boolean-false'",
                        },
                    ):  # Parse False value represented as X mark
                        value = False
                    elif (
                        label == "Aktualizace"
                        and li.find("span", {"class": "ng-binding ng-scope"}).text
                        == "Dnes"
                    ):
                        value = date.today().strftime(
                            "%d.%m.%Y"
                        )  # Convert current date represented by "Today" to current date
                    else:
                        try:
                            value = li.find(
                                "span", {"class": "ng-binding ng-scope"}
                            ).text
                        except AttributeError:
                            value = None
                    try:
                        item[label] = int(value)
                    except Exception:
                        item[label] = value
                    except TypeError:
                        item[label] = value
            # Repalce accents with english letter, unicode values and replace spaces with underscores
            item = {
                unidecode.unidecode(key)
                .lower()
                .replace(" ", "_"): (
                    unicodedata.normalize("NFKD", value)
                    if isinstance(value, str)
                    else value
                )
                for key, value in item.items()
            }
            return item
        elif page.find("div", {"class": "error-content without-button"}):
            item["url"] = self.page_url
            item["aktivni"] = False
            return item
        else:
            None

    def get_total_properties_count(self):
        if not self.page.find("p", class_="status-text ng-binding"):
            props_count = self.page.findAll("span", class_="numero ng-binding")
            if props_count:
                try:
                    props_count = int(props_count[-1:][0].text.replace(u"\xa0", ""))
                    return ceil(props_count / 20)
                except TypeError:
                    raise ("Value cannot be converted to string")
        else:
            return 1

    def get_properties_links(self):
        links = set()
        if self.page.find_all("a", class_="title"):
            for link in self.page.find_all("a", class_="title"):
                links.add(link["href"])
        return links
