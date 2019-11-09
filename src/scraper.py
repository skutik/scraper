import requests
import logging
import requests_html
from time import time
import unicodedata
from bs4 import BeautifulSoup
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import os

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

ENDPOINT_URL = "https://www.sreality.cz"
CITY = "praha"
SIZE = ["pokoj"]

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
                # logging.info(links)
                if links:
                    for link in links:
                        link = str(link)
                        if " href='/detail/" in link:
                            property_link = [element.split("=")[1].replace("'", "") for element in link.split() if element.startswith("href='/detail/")][0]
                            properties.add(property_link)
                            # logging.info(property_link)
                        elif "ng-class='{disabled: !pagingData.nextUrl}'" in link and "href='/hledani" in link:
                            nextPage = True
            else:
                raise(f"Got status code {response.status_code}")
            counter += 1
            if not nextPage:
                return properties

def parse_property_page(soupObject):
    item = dict()
    soup = soupObject
    if not None:
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

        # item["ad_id"] = url.split("/")[-1:][0]
        item["adress"] = soup.find("span", class_="location-text ng-binding").text
        price_string = unicodedata.normalize("NFKD",soup.find("span", class_="norm-price ng-binding").text)
        logging.info(price_string)
        price = re.findall(r"\d+", price_string)
        item["price_value"] = "".join(price)
    else:
        return None

    return item

# await def test_as_get(pro):
#     with requests_html.AsyncHTMLSession() as assesion:
#         for prop in properties:
#             logging.info(f"Logging currently processed propperty: {prop}")
#             aresponse = await assesion.get(prop)
#             await aresponse.html.arender()
#             return aresponse.html.text

async def get_property(assesion, prop):
    logging.info(f"Processing page of property: {prop}")
    response = await assesion.get(prop)
    await response.html.arender(timeout=2000)
    return response

# async def get_data(properties):
#     with ThreadPoolExecutor(max_workers=2) as executor:
#         with requests_html.AsyncHTMLSession() as assesion:
#             loop = asyncio.get_event_loop()
#             tasks = [await loop.run_in_executor(executor, get_property, *(assesion, prop)) for prop in properties]

#             return await asyncio.gather(*tasks)
            
                # soup = BeautifulSoup(str(response), "html.parser")
                # logging.info(parse_property_page(soup))
                # parsed_page parse_property_page(soup, prop)
                # logging.info(response)
                # return

async def main():
    asession = requests_html.AsyncHTMLSession()
    tasks = [get_property(asession, adv) for adv in properties]
    # return await asyncio.gather(*tasks)
    for advert in await asyncio.gather(*tasks):
        logging.info(f"Parsing URL {advert.html.url}")
        if advert.status_code != 200:
            logging.warning(f"URL {advert.html.status_code} return with status code {advert.html.status_code}")
            # break
        else:
            # return advert.html.text
            # soup = BeautifulSoup(str(advert.html.text), "html.parser")
            # return parse_property_page(soup)
            # with open()
            file_name = "pages/{}.html".format(advert.html.url.split("/")[-1])
            logging.info(file_name)
            if os.path.exists("pages/"):
                with open(file_name, 'w') as file:
                    file.write(advert.html.html)
                    file.close()
            else:
                os.mkdir("pages/")
                with open(file_name, 'w') as file:
                    file.write(advert.html.html)
                    file.close()
            # advert.html.url

url = createURL(ENDPOINT_URL, city="praha")
logging.info(url)
properties = get_properties(url, headers=HEADERS, params=PARAMS)
logging.info(f"Found adverts: {len(properties)}")
properties = [ENDPOINT_URL + ad for ad in properties]
loop = asyncio.get_event_loop()
results = loop.run_until_complete(main())
print(results)
# results = asyncio.run(main())
# for result in results:
#     logging.info(f"Parsing URL {result.html.url}")
#     if result.status_code != 200:
#         logging.warning(f"URL {result.html.url} return with status code {result.html.status_code}")
#     else:
#         # return advert.html.text
#         soup = BeautifulSoup(str(result.html.text), "html.parser")
#         print(soup)

# async def main(properties):
#     asession = requests_html.AsyncHTMLSession()
#     tasks = [get_property(asession, prop) for prop in properties]
#     results = await asyncio.gather(*tasks)
#     return list(chain(*(res for res in results)))

# async def get_url_response(session, url, headers):
#     response = await session.get(url, headers=headers)
#     await response.html.arender()
#     return response

# async def get_properties_dict(properties):
#     properties_dict = dict()
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         with requests_html.AsyncHTMLSession() as assesion:
#             loop = asyncio.get_event_loop()
#             tasks = [await loop.run_in_executor(executor, get_url_response, *(assesion, ENDPOINT_URL + ad, HEADERS)) for ad in properties]
#             for response in await asyncio.gather(*tasks):
#                 logging.info(response)
#                 soup = BeautifulSoup(str(response.html.element), "html.parser")
#                 proterty_dict = parse_property_page(soup, url)
#                 properties_dict[proterty_dict.get("ad_id")] = proterty_dict
#     logging.info(properties_dict)

# def main(properties):
#     loop = asyncio.get_event_loop()
#     furure = asyncio.ensure_future(get_properties_dict(properties))
#     loop.run_until_complete(furure)
#     return 

# async def get_data_a_test(properties):
#     responses = []
#     asession = requests_html.AsyncHTMLSession()

#     for prop in properties:
#         response = asession.get(prop, headers=HEADERS) 
#         response.html.arender()
#         responses.append(response)

#     return responses


    # for prop in properties:
    #     with requests_html.AsyncHTMLSession() as asession:
    #             response = asession.get(prop, headers=HEADERS)
    #             response.html.arender()
    #             responses.append(response)
    # logging.info(responses)
    # return responses


# def get_properties_dict(properties):
#     properties_dict = dict()
#     for property in properties:
#         url = ENDPOINT_URL + property
#         logging.info(url)
#         with requests_html.HTMLSession() as session:
#             response = session.get(url, headers=HEADERS)
#             response.html.render()
#             soup = BeautifulSoup(str(response.html.element), "html.parser")
#         proterty_dict = parse_property_page(soup, url)
#         properties_dict[proterty_dict.get("ad_id")] = proterty_dict
#     return properties_dict

# async def get_properties_dict(properties):
#     properties_dict = dict()
#     for property in properties:
#         url = ENDPOINT_URL + property
#         logging.info(url)
#         with requests_html.AsyncHTMLSession() as asession:
#             response = await asession.get(url, headers=HEADERS)
#             response.html.render()
#             soup = BeautifulSoup(str(response.html.element), "html.parser")
#         proterty_dict = parse_property_page(soup, url)
#         properties_dict[proterty_dict.get("ad_id")] = proterty_dict
#     return properties_dict

# url = createURL(ENDPOINT_URL, city="praha")
# logging.info(url)
# properties = get_properties(url, headers=HEADERS, params=PARAMS)
# logging.info(properties)
# properties = [ENDPOINT_URL + ad for ad in properties]
# pages  = asyncio.run(main(properties))
# print(pages)
# loop = asyncio.get_event_loop()
# x = loop.ensure_future(test_as_get(properties))
# pool = Pool(processes=3)
# output = pool.map(test_as_get, properties)
# pool.close()
# pool.join()
# print(output)
# logging.info(f"Test:{x}")



# pool = Pool(processes=3)
# output = pool.map(get_data_a_test, properties)
# pool.close()
# pool.join()
# print(output)

# asyncio.run(get_data_a_test(properties))

# async def main():
#     await get_data_a_test(properties)

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())

# properties = get_properties_dict(properties)

# pool = Pool(processes=1)
# properties = pool.map(get_properties_dict, properties)
# pool.close()
# pool.join()

# fails while processing https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-hrdlorezy-mezitratova/1961549404

# properties = get_properties_dict(["/detail/pronajem/byt/1+kk/praha-nove-mesto-na-struze/3262574172"])
# print(properties)