import unittest
from src.parser import Parser

class ParserTest(unittest.TestCase):

    with open("tests/pages/advertisement_page.html") as html_file:
        html = html_file.read()

    testParser = Parser(html, "www.testpage.com")
    emptyParser = Parser("", "")

    def test_parser(self):
        advert_dict = self.testParser.get_dict()
        emptyPage = self.emptyParser.get_dict()
        print(advert_dict)
        self.assertEqual(len(advert_dict), 15)
        self.assertEqual(type(advert_dict["cena"]), int)
        self.assertEqual(advert_dict["poznamka_k_cene"], "Služby 1000 Kč + provize RK")
        self.assertEqual(advert_dict["url"],  "www.testpage.com")
        self.assertEqual(emptyPage,None)
        with self.assertRaises(TypeError):
            emptyPage["url"]

if __name__ == "__main__":
    unittest.main()