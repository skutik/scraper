from src.scraper import Scraper
import unittest
from unittest.mock import patch

class ScraperTest(unittest.TestCase):

    with open("tests/pages/list_of_adverts.html") as html_file:
        html = html_file.read()

    praha_pokoj = Scraper("praha", "pokoj")
    praha_pokoj_url = "https://www.sreality.cz/hledani/pronajem/byty/praha"
    ostrava_liberec_small = Scraper(["ostrava", "liberec"], ["1+1", "1+kk", "2+kk"], search_type="prodej")
    ostrava_liberec_small_url = "https://www.sreality.cz/hledani/prodej/byty/ostrava,liberec"    

    def test_scraper(self):
        self.assertEqual(self.praha_pokoj._generate_url, self.praha_pokoj_url)
        self.assertEqual(self.ostrava_liberec_small._generate_url, self.ostrava_liberec_small_url)

    def test_mock_get_page(self):
        with patch("src.scraper.requests.get") as mocked_get:
            mocked_get.return_value.status_code = 200
            mocked_get.return_value.html.html = self.html

            prop_set = self.praha_pokoj._get_properties()
            mocked_get.assert_called_with("https://www.sreality.cz/hledani/pronajem/byty/praha?velikost=pokoj&strana=1")
            self.assertEqual(len(prop_set), 20)

if __name__ == "__main__":
    unittest.main()