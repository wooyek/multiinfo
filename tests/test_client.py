# coding=utf-8

import pytest
import requests
from requests import HTTPError

from multiinfo import core
from multiinfo.endpoints import get_message_id
from multiinfo.exceptions import ClientException


def test_default_headers(offline_client):
    headers = offline_client.build_headers()
    assert headers['Accept'] == 'application/json'
    assert headers['Content-Type'] == 'application/json'
    assert set(headers.keys()) == {'accept', 'user-agent', 'content-type'}


def test_get_additional_headers(offline_client):
    headers = offline_client.build_headers({'foo': 'bar'})
    assert headers['foo'] == 'bar'


def test_override_headers(offline_client):
    headers = offline_client.build_headers({'Accept': 'bar'})
    assert headers['Accept'] == 'bar'
    assert headers['accept'] == 'bar'


FAKE_PAYLOAD = {
    'login': 'fake-login',
    'password': 'fake-pass',
    'orig': 'fake-orig',
    'serviceId': 999111888,
}


def test_default_payload(offline_client):
    payload = offline_client.build_payload()
    assert payload == FAKE_PAYLOAD


def test_build_payload(offline_client):
    data = {'foo': 'bar'}
    payload = offline_client.build_payload(data)
    assert payload['foo'] == 'bar'


def test_base_url_validation():
    with pytest.raises(ValueError, match='Invalid url: foo'):
        core.ApiClient(base_url='foo')


def test_get(offline_client, mocker):
    request = mocker.patch('multiinfo.core.ApiClient.request')
    offline_client.get('foo')
    request.assert_called_with('GET', 'foo', headers=None, params=FAKE_PAYLOAD)


class GetMessageIdTests(object):

    @pytest.mark.parametrize("text, message_id", [("0\n33", 33), ("123\n88", 88), ("123\n1609850641\n1609850642", 1609850641)])
    def test_valid(self, text, message_id):
        assert message_id == get_message_id(text)

    @pytest.mark.parametrize("text, reason", [("-123\nŚciąć ją", "Ściąć ją"), ("-5\nNatychmiast", "Natychmiast")])
    def test_errors(self, text, reason):
        with pytest.raises(ClientException, match=reason):
            get_message_id(text)

    @pytest.mark.parametrize("status_code, reason", [(400, "Bad request"), (500, "Server error")])
    def test_http_errors(self, status_code, reason, mocker):
        response = requests.Response()
        response.status_code = status_code
        response.reason = reason
        api = core.ApiClient()
        request_factory = mocker.patch("multiinfo.core.ApiClient.request_factory")
        request_factory.return_value = response
        with pytest.raises(HTTPError, match=reason):
            api.request('bar', 'foo')
