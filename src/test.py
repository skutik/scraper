import asyncio
import requests_html
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

properties = ["https://www.sreality.cz/detail/pronajem/byt/pokoj/ostrava-moravska-ostrava-dr--smerala/2329996892",
"https://www.sreality.cz/detail/pronajem/byt/pokoj/ostrava-zabreh-dolni/3135540828"]

async def get_data(async_session, url):
    response = await async_session.get(url)
    await response.html.arender()
    return response

async def process_adverts(properties):
    with requests_html.AsyncHTMLSession() as asession:

        tasks = [get_data(asession, adv) for adv in properties]
        results = await asyncio.gather(*tasks)

        return results

        # loop = asyncio.get_event_loop()
        # pages = loop.run_until_complete(asyncio.gather(*tasks))
        # for page in pages:
        #     print(page.html.url)

async def main():
    asession = requests_html.AsyncHTMLSession()
    tasks = [get_data(asession, adv) for adv in properties]
    return await asyncio.gather(*tasks)
    # return await asyncio.gather(*tasks)
    
    # for result in results:
    #     print(result.html.text)
    # loop = asyncio.get_event_loop()
    # future = asyncio.ensure_future(process_adverts(properties))
    # loop.run_until_complete(future)
    # loop.close

# asession = requests_html.AsyncHTMLSession()
# asyncio.run(process_adverts(properties))

loop = asyncio.get_event_loop()
results = loop.run_until_complete(main())
# results = asyncio.run(main())
print([result.html.url for result in results])