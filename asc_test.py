import asyncio
import random
from src.scraper import Scraper

scraper = Scraper(city=["praha"], size=["4+1"])

# async def delay_fce(sec, num, semaphore):
#     async with semaphore:
#         print(f"Run number {num} started! {sec}")
#         await asyncio.sleep(sec)
#         print(f"Run number {num} finished! {sec}")
#     return f"Function number {num} with wait time {sec} has finished successfully!"
#
# async def main(times):
#     semaphore = asyncio.Semaphore(5)
#     tasks = [asyncio.ensure_future(delay_fce(sec[1], sec[0], semaphore)) for sec in times]
#     return await asyncio.gather(*tasks)
#
# times = [(i, random.randint(1,10)) for i in range(10)]
# print(times)
# loop = asyncio.get_event_loop()
# loop.set_debug(True)
# results = loop.run_until_complete(main(times))
# print(results)
