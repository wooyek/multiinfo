# coding=utf-8
import json
import logging
import os
import random

import envparse
import pytest
import six
from faker import Faker
from mock import MagicMock, mock
from pytest_lazyfixture import lazy_fixture

import multiinfo
from multiinfo import endpoints, factories
from multiinfo.core import ApiClient, get_api_client as get_actutal_api_client
from tests import test_data

if six.PY3:
    from pathlib import Path
else:
    from pathlib2 import Path

logging.basicConfig(format='%(asctime)s %(levelname)-7s %(thread)-5d %(filename)s:%(lineno)s | %(funcName)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.DEBUG)
logging.disable(logging.NOTSET)
logging.getLogger('environ').setLevel(logging.INFO)

log = logging.getLogger(__name__)
fake = Faker()


class MockedApiClient(ApiClient):

    def request(self, method, endpoint, params=None, payload=None, headers=None):
        assert method == 'GET'
        return "0\n{}".format(random.randint(1, 9999))

    @staticmethod
    def parse_endpoint(endpoint):
        logging.debug("endpoint: %s", endpoint)
        if "/" not in endpoint:
            return None, endpoint.replace('.json', '')

        endpoint, model_id = endpoint.split('/')
        model_id = int(model_id.replace('.json', ''))
        model_name = endpoint[:-1]
        return model_id, model_name

    def request_factory(self, *args, **kwargs):
        raise Exception('{} should not try to make requests'.format(self.__class__.__name__))

    # def __getattr__(self, key):
    #     if key not in self._storage:
    #         msg = '{} instance does not have {} key in _storage dictionary'
    #         raise AttributeError(msg.format(self.__class__.__name__, key))
    #     return self._storage[key]


def get_api_client(settings=None):
    return MockedApiClient()

# Monkeypatch get_api_client for doctest to work properly
multiinfo.get_api_client = get_api_client


@pytest.fixture
def mocked_api():
    return MockedApiClient()


@pytest.fixture
def offline_client():
    return ApiClient('fake-login', 'fake-pass', ('a.key', 'a.cert'), 999111888, 'fake-orig', 'https://multiinfo.example.com')


@pytest.fixture
def client_request(mocker):
    yield mocker.patch('conftest.MockedApiClient.request')


@pytest.fixture
def secrets():
    from multiinfo.core import MultiInfoSettings
    secrets_yml = str(Path(__file__).parent / '.confindential.yml')
    with mock.patch.dict('os.environ', {'MULTIINFO_SETTINGS_MODULE': secrets_yml}):
        yield MultiInfoSettings()


@pytest.fixture
def environment_settings():
    defaults = {
        'MULTIINFO_LOGIN': 'envlogin',
        'MULTIINFO_PASSWORD': 'envpass',
        'MULTIINFO_SERVICE_ID': '123',
        'MULTIINFO_CERT_PATH': 'etc/fake.cert',
        'MULTIINFO_KEY_PATH': 'etc/fake.key',
    }
    with mock.patch.dict('os.environ', defaults):
        yield




@pytest.fixture
def sandbox_api(request, secrets):
    sandbox_enabled = secrets.get('SANDBOX_ENABLED', None)
    if not sandbox_enabled:
        pytest.skip('Sandbox calls are disabled')
    return get_actutal_api_client(secrets)


@pytest.fixture(params=[
    lazy_fixture('mocked_api'),
    lazy_fixture('sandbox_api')
])
def api_client(request):
    return request.param


@pytest.fixture(params=[
    endpoints.Sms(None, **test_data.SMS),
    endpoints.Sms(None, **factories.SmsFactory().get_raw_data()),
    endpoints.LongSms(None, **test_data.LONG_SMS),
    endpoints.LongSms(None, **factories.LongSmsFactory().get_raw_data()),
])
def any_model(request):
    return request.param
