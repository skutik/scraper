from src.scraper import Scraper
import logging

scraper = Scraper(city=["ostrava"], size=["4+1"])
scraper.run()
