import pytest
import json
import pytest_aiohttp
from asynctest import patch, CoroutineMock
import datetime
from unittest import mock

from src.scraper import Scraper

scraper = Scraper(category_main=1, category_type=2, test_enviroment=True)


@patch("aiohttp.ClientSession.get")
async def test_fetch_estate_existing(mock_get):
    mock_get.return_value.__aenter__.return_value.status = 200
    mock_get.return_value.__aenter__.return_value.text = CoroutineMock(
        side_effect=[json.dumps({"x": "y"})]
    )
    property_dict, status_code = await scraper._fetch_estate(123)
    assert property_dict == {"x": "y"}
    assert status_code == 200


@patch("aiohttp.ClientSession.get")
async def test_fetch_estate_deleted(mock_get):
    mock_get.return_value.__aenter__.return_value.status = 410
    property_dict, status_code = await scraper._fetch_estate(123)
    assert property_dict == {"available": False}
    assert status_code == 410


@patch("aiohttp.ClientSession.get")
async def test_fetch_estate_not_found(mock_get):
    mock_get.return_value.__aenter__.return_value.status = 404
    property_dict, status_code = await scraper._fetch_estate(123)
    assert property_dict is None
    assert status_code == 404


# @freeze_time("2020-02-01")
# def test_timestamp_generator():
#     s = Scraper(category_main=1, category_type=2, mongo_database="test_db", mongo_collection="props")
#     date_time = s._current_timestamp
#     print(date_time)
#     assert date_time == int(datetime.datetime(2020, 2, 1).timestamp()*1000)


def test_timestamp_generator():
    with mock.patch("src.scraper.dt") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime.datetime(2020, 2, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime.datetime(
            *args, **kwargs
        )
        assert scraper._current_timestamp == int(
            datetime.datetime(2020, 2, 1).timestamp() * 1000
        )
