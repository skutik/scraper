from src.scraper import Scraper
import logging

logging.getLogger().setLevel(logging.INFO)

# scraper = Scraper(city=["praha-5"], size=["4+1"])
scraper = Scraper()
scraper.run()
