# coding=utf-8
import logging
from datetime import datetime

import pytest
import requests
from mock import MagicMock, PropertyMock

from multiinfo import base, core, endpoints, factories
from multiinfo.endpoints import parse_status_info

from .test_data import LONG_SMS, SMS

log = logging.getLogger(__name__)


@pytest.fixture(params=["send_sms", "send_long_sms"])
def endpoint(request, offline_client):
    return getattr(offline_client, request.param)


@pytest.fixture
def test_msisdn(secrets):
    if 'TEST_MSISDN' not in secrets:
        pytest.skip('Requires an environment TEST_MSISDN setting')
    return secrets['TEST_MSISDN']


# noinspection PyShadowingNames
def test_send_to_request(endpoint, mocker):
    request = mocker.patch('requests.request')
    response = MagicMock(requests.Response)
    type(response).text = PropertyMock(return_value="0\n33")
    request.return_value = response
    endpoint.send()
    assert request.called


@pytest.mark.parametrize("data", [
    LONG_SMS,
    factories.LongSmsFactory(dest='533005790').get_raw_data(),
])
def test_send_long_sms(api_client, data):
    item = api_client.send_long_sms.send(**data)
    assert item
    assert item.message_id
    assert isinstance(item.message_id, int)


@pytest.mark.parametrize("data", [
    SMS,
    factories.SmsFactory(dest='533005790').get_raw_data(),
])
def test_send_sms(api_client, data):
    item = api_client.send_sms.send(**data)
    assert item
    assert item.message_id
    assert isinstance(item.message_id, int)


# noinspection PyMethodMayBeStatic
class BaseModelTests(object):
    def test_get(self, offline_client, mocker):
        client_get = mocker.patch('multiinfo.core.ApiClient.get')
        client_get.return_value = "0\n1234"
        item = endpoints.Sms(offline_client, _endpoint='api')
        item.send()
        assert client_get.called
        assert item.message_id == 1234

    def test_missing_attribute(self):
        item = base.BaseModel(None)
        with pytest.raises(AttributeError, match='BaseModel instance does not have foo_bar key in data dictionary'):
            # noinspection PyStatementEffect
            item.foo_bar

    def test_private_update_data(self):
        item = base.BaseModel(None, id=333)
        with pytest.raises(AssertionError, match='Existing id does not match update data 333!=777'):
            # noinspection PyProtectedMember
            item._update_data({'id': 777})

    def test_update_data(self):
        item = base.BaseModel('adios/pomidory')
        item.update_data(tanie='dranie')
        assert item.tanie == 'dranie'

    def test_send_params(self, mocker, offline_client):
        request = mocker.patch('multiinfo.core.ApiClient.request')
        item = endpoints.Sms(offline_client)
        item.update_data(tanie='dranie')
        item._endpoint = 'fake'
        item.send()
        assert request.called
        args, kwargs = request.call_args
        assert kwargs['params']['tanie'] == 'dranie'


def test_valid():
    ts = datetime(2018, 3, 28, 19, 15)
    message = endpoints.Sms(None, validTo=ts)
    assert "280318191500" == message.get_raw_data()['validTo']
    assert ts == message.validTo


class SmsTests(object):

    def test_text(self):
        text = 'Dynda, dynda stryczka cień więc póki czas się zmień.'
        message = endpoints.Sms(None, text=text)
        assert text == message.text
        assert text == message.get_raw_data()['text']

    def test_text_validation(self):
        text = 'Dynda, dynda stryczka cień więc póki czas się zmień.' * 10
        with pytest.raises(AssertionError, match="Maximum text length exceeded: 520 > 160"):
            endpoints.Sms(None, text=text)


class LongSmsTests(object):
    def test_text(self):
        text = 'Dynda, dynda stryczka cień więc póki czas się zmień.'
        message = endpoints.LongSms(None, text=text)
        assert text == message.text
        assert text == message.get_raw_data()['text']

    def test_text_validation(self):
        text = 'Dynda, dynda stryczka cień więc póki czas się zmień.' * 30
        with pytest.raises(AssertionError, match="Maximum text length exceeded: 1560 > 1377"):
            endpoints.LongSms(None, text=text)


TEST_INFO_1 = """0
2322549673
1
foobar%0a
0
0
3290
662000123
-1
0
270418074906
300418074906
False
FABRIKAM
48197927123
21
2018-02-27 07:58:06"""

TEST_INFO_2 = """0
2322590614
1
foobar
0
0
3290
662000123
-1
0
270418092727
300418092728
False
CONTOSO
48121662123
7
2018-02-27 08:17:28"""


def test_sms_info(mocker):
    request = mocker.patch("multiinfo.core.ApiClient.request")
    request.return_value = 'foo'
    api_client = core.ApiClient()
    parse = mocker.patch("multiinfo.endpoints.parse_status_info")
    api_client.info_sms.get(123)
    parse.called_with('foo')


@pytest.mark.parametrize("text, status, status_message", [
    (TEST_INFO_1, 21, "Wiadomość przesłana pomyślnie"),
    (TEST_INFO_2, 7, "Wiadomość wstrzymana z powodu przekroczenia limitu"),
])
def test_parse_status_info(text, status, status_message):
    item = parse_status_info(text)
    assert item.message_status[0] == status
    assert item.message_status[1] == status_message
