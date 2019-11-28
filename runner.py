from src.scraper import Scraper

scraper = Scraper(city=["liberec", "ostrava"], size=["1+kk", "2+kk", "2+1", "4+1"])
scraper.run()
