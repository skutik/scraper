from src.scraper import Scraper
import unittest
from unittest.mock import patch
from requests_html import HTML
import asyncio

with open("tests/pages/list_of_adverts.html") as html_file:
    html = html_file.read()

HTML_script = """
<!DOCTYPE html>
<html>
<body>
<h1>Test links!</h1>
<script>
links = ["/property1", "/property2", "/property3"];
links.forEach(function(item) {
  var a = document.createElement('a');
  var p = document.createElement('P');
  var linkText = document.createTextNode("my title");
  a.appendChild(linkText);
  a.title = "my title text";
  a.href = item;
  a.className ="title";
  p.appendChild(a);
  document.body.appendChild(p);
})
</script>
</body>
</html>
"""

script_render_links = """<p><a title="my title text" href="/property1" class="title">my title</a></p><p><a title="my title text" href="/property2" class="title">my title</a></p><p><a title="my title text" href="/property3" class="title">my title</a></p>"""

HTML_delay = """
<!DOCTYPE html>
<html>
<body>
<h1>Test links!</h1>
<script>
var delayInSeconds = 10;
setTimeout(function() {
links = ["/property1", "/property2", "/property3"];
links.forEach(function(item) {
  var a = document.createElement('a');
  var p = document.createElement('P');
  var linkText = document.createTextNode("my title");
  a.appendChild(linkText);
  a.title = "my title text";
  a.href = item;
  a.className ="title";
  p.appendChild(a);
  document.body.appendChild(p);
})
}, delayInSeconds*1000);
</script>
</body>
</html>
"""

#https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, html, status_code):
            self.html = html
            self.status_code = status_code
            self.url = "mock.test.page"

    params = ",".join(["1+1", "1+kk", "2+kk"])
    if args[0] == "https://www.sreality.cz/hledani/prodej/byty/ostrava,liberec" and kwargs["headers"]==Scraper.HEADERS and kwargs["params"]["velikost"]==params: 
        return MockResponse(HTML(html=html), 200)
    elif args[0] == "https://www.sreality.cz/hledani/pronajem/byty/test":
        return MockResponse(HTML(html=HTML_script), 200)
    return MockResponse(None, 404)

async def mocked_async_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, html, status_code):
            self.html = html
            self.status_code = status_code
            self.url = "mock.async_test.page"

    if args[0] == "/timeout_test":
        return MockResponse(HTML(html=HTML_delay, async_=True), 200)
    elif args[0] == "/test":
        return MockResponse(HTML(html=HTML_script, async_=True), 200)
    return MockResponse(None, 404)

class ScraperTest(unittest.TestCase):
    praha_pokoj = Scraper("praha", "pokoj")
    praha_pokoj_url = "https://www.sreality.cz/hledani/pronajem/byty/praha"
    ostrava_liberec_small = Scraper(["ostrava", "liberec"], ["1+1", "1+kk", "2+kk"], search_type="prodej")
    ostrava_liberec_small_url = "https://www.sreality.cz/hledani/prodej/byty/ostrava,liberec" 
    render_test = Scraper("test", "pokoj")
    timeout_render_render = Scraper("timeout_test", "pokoj")

    def test_scraper(self):
        self.assertEqual(self.praha_pokoj._generate_url, self.praha_pokoj_url)
        self.assertEqual(self.ostrava_liberec_small._generate_url, self.ostrava_liberec_small_url)

    def test_mock_get_page(self):
        with patch("src.scraper.requests_html.HTMLSession.get", side_effect=mocked_requests_get):
            properties_ostrava_liberec = self.ostrava_liberec_small._get_properties()
            properties_render = self.render_test._get_properties()
            self.assertEqual(len(properties_ostrava_liberec), 20)
            self.assertEqual(len(properties_render), 3)
            self.assertEqual(properties_render, {"/property1", "/property2", "/property3"})
    
    def test_mock_async_rendering(self):
        with patch("src.scraper.requests_html.AsyncHTMLSession.get", side_effect=mocked_async_requests_get):
            loop_test = asyncio.get_event_loop()
            future_test = asyncio.ensure_future(self.render_test._run(["/test"]))
            results_test = loop_test.run_until_complete(future_test)
            self.assertEqual(script_render_links in results_test[0][1].html.html, True)

            loop_delay = asyncio.get_event_loop()
            future_delay = asyncio.ensure_future(self.render_test._run(["/non_ok_reposnse"], timeout=5))
            results_delay = loop_delay.run_until_complete(future_delay) 
            self.assertEqual(results_delay[0][1], None)
            self.assertEqual(results_delay[0][0],"/non_ok_reposnse")

if __name__ == "__main__":
    unittest.main()