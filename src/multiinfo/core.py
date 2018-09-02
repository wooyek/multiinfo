# coding=utf-8
# Copyright (c) 2018 Janusz Skonieczny

import logging
import sys
from pathlib import Path

import requests
import six
from dynaconf import LazySettings
from dynaconf.utils.functional import SimpleLazyObject
from requests.structures import CaseInsensitiveDict
from urllib3.util import parse_url

from multiinfo import endpoints
from multiinfo.exceptions import MultiInfoConfigurationException

log = logging.getLogger(__name__)


class ApiClient(object):
    """ MultiInfo API client

    Here is an example of how to send an sms.

    >>> from multiinfo import get_api_client
    >>> api = get_api_client()
    >>> message = api.send_sms.send(
    ...     dest=601333444,
    ...     text='Ojciec Wirgiliusz uczył dzieci swoje. Na głowie przy tym stojąc wiele lat.',
    ... )

    Message instance will have id and status information.

    >>> message.message_id  # doctest: +SKIP
    123
    """

    def __init__(self, login=None, password=None, cert=None, service_id=None, orig=None, base_url=None, request_timeout=10):
        self.request_timeout = request_timeout
        self.login = login
        self.password = password
        self.service_id = service_id
        self.orig = orig
        self.cert = cert
        if base_url is not None:
            self.base_url = base_url
        else:
            self.base_url = 'https://api1.multiinfo.plus.pl/'
        from . import __version__ as version
        self.default_headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'user-agent': "MultiInfo Python/" + version
        }

        log.info("MultiInfo: base_url: %s %s:***", self.base_url, self.login)
        self.send_sms = endpoints.SendSms(self)
        self.send_long_sms = endpoints.SendLongSms(self)
        self.info_sms = endpoints.InfoSms(self)

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, url):
        log.debug("url: %s", url)
        parsed = parse_url(url)
        if parsed.scheme is None or parsed.hostname is None:
            raise ValueError("Invalid url: {}".format(url))
        # noinspection PyAttributeOutsideInit
        self._base_url = url

    # noinspection PyMethodMayBeStatic
    def request_factory(self, *args, **kwargs):
        return requests.request(*args, **kwargs)

    def get(self, endpoint, data=None, headers=None):
        params = self.build_payload(data)
        return self.request('GET', endpoint, params=params, headers=headers)

    def request(self, method, endpoint, params=None, payload=None, headers=None):
        url = self.base_url + endpoint
        log.debug("url: %s", url)
        log.debug("payload: %s", payload)
        resp = self.request_factory(
            method=method,
            url=url,
            headers=self.build_headers(headers),
            data=payload,
            params=params,
            timeout=self.request_timeout,
            cert=self.cert,
        )
        log.debug("response: %s", resp)
        log.debug("response: %s", resp.text)
        resp.raise_for_status()
        return resp.text

    def build_payload(self, data=None):
        payload = {
            'login': self.login,
            'password': self.password,
            'serviceId': self.service_id,
            'orig': self.orig,
        }
        if data:
            payload.update(data)
        return payload

    def build_headers(self, items=None):
        headers = CaseInsensitiveDict(self.default_headers)
        if items:
            headers.update(items)
        return headers


class MultiInfoSettings(LazySettings):
    def __init__(self, **kwargs):
        kwargs.setdefault('ENVVAR_FOR_DYNACONF', "MULTIINFO_SETTINGS_MODULE"),
        kwargs.setdefault('DYNACONF_NAMESPACE', "MULTIINFO"),
        import os
        print(os.environ)
        print(dir(self))
        super(MultiInfoSettings, self).__init__(**kwargs)
        print(dir(self))
        print(self._loaded_by_loaders)

    def __getattr__(self, name):
        try:
            return super(MultiInfoSettings, self).__getattr__(name)
        except AttributeError as ex:
            msg = "Missing configuration setting: MULTIINFO_" + name
            if six.PY2:  # pragma: no cover
                six.reraise(AttributeError, AttributeError(msg), sys.exc_info()[2])
            raise MultiInfoConfigurationException(msg) from ex


def get_api_client(settings=None):
    """
    Factory function for MultiInfo API client with configuration options
    taken from environment

    :return: ApiClient instance
    """
    settings = settings or MultiInfoSettings()
    request_timeout = settings.get('TIMEOUT')
    if request_timeout:
        request_timeout = float(request_timeout)
    service_id = settings.get('SERVICE_ID')
    if service_id:
        service_id = int(service_id)

    cert_path = settings.get('CERT_PATH')
    key_path = settings.get('KEY_PATH')
    if cert_path:
        assert Path(cert_path).exists(), "Cert file does not exist: %s" % settings.CERT_PATH
    if key_path:
        assert Path(key_path).exists(), "Key file not exist: %s" % settings.KEY_PATH

    cfg = {
        'request_timeout': request_timeout,
        'login': settings.LOGIN,
        'password': settings.PASSWORD,
        'service_id': service_id,
        'orig': settings.get('ORIG'),
        'cert': (cert_path, key_path),
        'base_url': settings.get('BASE_URL', 'https://api1.multiinfo.plus.pl/')
    }
    return ApiClient(**cfg)


multiinfo_api = SimpleLazyObject(get_api_client)
