import unittest
from src.parser import Parser

class ParserTest(unittest.TestCase):

    with open("tests/pages/advertisement_page.html") as html_file:
        html = html_file.read()

    parser = Parser(html, "www.testpage.com")

    def test_parser(self, parser):
        advert_dict = parser.get_dict()
        self.assertEqual(len(advert_dict), 15)
        self.assertEqual(advert_dict["url"],  "www.testpage.com")

if __name__ == "__main__":
    unittest.main()