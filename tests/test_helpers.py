from src.helpers import get_xpath_data

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Page Title</title>
</head>
<body>
<div class="cl1">TextClass1</div>
<div name="Content">
<p class="important">Imp1</p>
<p class="testing">Imp2</p>
<p class="important">Imp3</p>
<p class="important">Imp4</p>
</div>
</body>
</html>
"""


def test_xpath_text():
    xpath = '//div[@class="cl1"]'
    data = get_xpath_data(HTML, xpath)
    assert len(data) == 1
    assert data[0].text == "TextClass1"


def test_xpath_multiple_results():
    xpath = '//div[@name="Content"]/p[@class="important"]'
    data = get_xpath_data(HTML, xpath)
    assert len(data) == 3
    assert [element.text for element in data] == ["Imp1", "Imp3", "Imp4"]
