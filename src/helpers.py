from lxml import html


def get_xpath_data(page_content: str, xpath_string: str, content_format: str = None):
    # if content_format == "xml" else etree.XMLParser()
    # page = etree.parse(page_content, parser=parser)
    page = html.fromstring(page_content)
    return page.xpath(xpath_string)


async def get_coordinates_by_address(session, address):
    async with session.get(
        "https://api.mapy.cz/geocode", params={"query": address}
    ) as response:
        if response.status == 200:
            response_payload = await response.read()
            locations = get_xpath_data(response_payload, "//item", content_format="xml")
            if locations:
                return locations[0].get("x"), locations[0].get("y")
        return None, None
