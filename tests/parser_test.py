import unittest
from src.parser import Parser

class ParserTest(unittest.TestCase):

    with open("tests/pages/advertisement_page.html") as html_file:
        html = html_file.read()

    testParser = Parser(html, "www.testpage.com")
    emptyParser = Parser("", "")
    realUrlParser = Parser(html,"https://www.sreality.cz/detail/pronajem/byt/5+1/praha-vinor-uherska/142990940#img=0&fullscreen=false")

    def test_parser(self):
        advert_dict = self.testParser.get_dict()
        emptyPage = self.emptyParser.get_dict()
        realUrl = self.realUrlParser.get_dict()
        self.assertEqual(len(advert_dict), 19)
        self.assertEqual(type(advert_dict["cena"]), int)
        self.assertEqual(advert_dict.get("id_zakazky"), 223849)
        self.assertEqual(advert_dict.get("xyz"), None)
        self.assertEqual(advert_dict.get("typ_smlouvy"), None)
        self.assertEqual(realUrl.get("typ_smlouvy"), "pronajem")
        self.assertEqual(realUrl.get("typ_nemovitosti"), "byt")
        self.assertEqual(advert_dict["url"], "www.testpage.com")
        self.assertEqual(emptyPage,None)
        with self.assertRaises(TypeError):
            emptyPage["url"]

if __name__ == "__main__":
    unittest.main()