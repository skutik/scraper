import unittest
from src.parser import Parser
import hashlib

class ParserTest(unittest.TestCase):

    with open("tests/pages/advertisement_page.html") as html_file:
        html = html_file.read()

    with open("tests/pages/failed_parse_page.html") as html_file:
        expired_html = html_file.read()

    testParser = Parser(html, "www.testpage.com")
    emptyParser = Parser("", "")
    realUrlParser = Parser(html,"https://www.sreality.cz/detail/pronajem/byt/5+1/praha-vinor-uherska/142990940")
    expiredAdvert = Parser(expired_html, "https://www.sreality.cz/detail/pronajem/byt/pokoj/praha-zizkov-rehorova/1267392092")

    def _id_hash(self, url):
        hash_object = hashlib.sha1(url.encode())
        return hash_object.hexdigest()

    def test_parser(self):
        advert_dict = self.testParser.property_dict
        emptyPage = self.emptyParser.property_dict
        realUrl = self.realUrlParser.property_dict
        expiredAdvert_dict = self.expiredAdvert.property_dict
        self.assertEqual(len(advert_dict), 19)
        self.assertEqual(type(advert_dict["cena"]), int)
        self.assertEqual(advert_dict.get("id"), 223849)
        self.assertEqual(advert_dict.get("xyz"), None)
        self.assertEqual(advert_dict.get("typ_smlouvy"), None)
        self.assertEqual(realUrl.get("typ_smlouvy"), "pronajem")
        self.assertEqual(realUrl.get("typ_nemovitosti"), "byt")
        self.assertEqual(advert_dict["url"], "www.testpage.com")
        self.assertEqual(emptyPage,None)
        self.assertEqual(expiredAdvert_dict.get("aktivni"), False)
        with self.assertRaises(TypeError):
            emptyPage["url"]

if __name__ == "__main__":
    unittest.main()