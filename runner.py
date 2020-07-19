from src.sreality import Scraper
import logging
import sys

print(sys.path)

logging.getLogger().setLevel(logging.DEBUG)

# scraper = Scraper(city=["praha-5"], size=["4+1"])
scraper = Scraper(
    category_main=1, category_type=2, locality_region=12, test_enviroment=True
)
scraper.runner()
