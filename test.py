import asyncio
import requests_html
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

properties = ['https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-konevova/907603548', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/3664895580', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-krc-/2703658588', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-hostavice-pilska/1719066204', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-kobylisy-strelnicna/1755766364', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-stodulky-okruhova/2744639068', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-stodulky-pod-viaduktem/4140949084', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-cerny-most-bobkova/1512300124', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-vinohrady-belehradska/1850072668', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-karlin-peckova/3676266844', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-hrdlorezy-mezitratova/1961549404', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-haje-stankova/2639134300', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-chodov-klirova/4216381020', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/1267392092', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-libus-zbudovska/3508919900', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/4201766492', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-hlubocepy-trnkovo-namesti/1843453532', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/4203404892', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-strasnice-u-hraze/273604188', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-karlin-/2899873372', 'https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-vinohrady-trebizskeho/887152220']

# ["https://www.sreality.cz/detail/pronajem/byt/pokoj/ostrava-moravska-ostrava-dr--smerala/2329996892",
# "https://www.sreality.cz/detail/pronajem/byt/pokoj/ostrava-zabreh-dolni/3135540828"]

async def get_data(async_session, url):
    # async with semaphore:
    response = await async_session.get(url)
    try:
        await response.html.arender(timeout=1000)
    except e:
        print(e)
        response = None
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
    # tasks = list()
    # # semaphore = asyncio.BoundedSemaphore(10)

    # for adv in properties:
    #     tasks.append(asyncio.ensure_future(get_data(asession, adv, semaphore)))
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
try:
    results = loop.run_until_complete(main())
except e:
    print(e)
    results = []
# results = asyncio.run(main())
print([result.html.url for result in results])