#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `multiinfo` package."""
import logging

import pytest
from mock import mock

import multiinfo
from conftest import get_actutal_api_client as get_api_client
from multiinfo.endpoints import parse_response
from multiinfo.exceptions import MultiInfoConfigurationException

log = logging.getLogger(__file__)


def test_version_exists():
    """This is a stupid test dummy validating import of multiinfo"""
    assert multiinfo.__version__


# noinspection PyUnusedLocal
def test_client_factory(environment_settings):
    api_client = get_api_client()
    assert api_client is not None
    assert api_client.login == 'envlogin'
    assert api_client.password == 'envpass'
    assert api_client.cert == ('etc/fake.cert', 'etc/fake.key')
    assert api_client.service_id == 123
    log.debug("api_client.base_url: %s", api_client.base_url)
    assert api_client.base_url


def test_client_factory_no_environment():
    with pytest.raises(MultiInfoConfigurationException, match='Missing configuration setting: MULTIINFO_LOGIN'):
        with mock.patch.dict('os.environ', clear=True):
            get_api_client()


def test_client_factory_timeout(mocker, environment_settings):
    mocker.patch.dict('os.environ', {'MULTIINFO_TIMEOUT': '0.1'})
    api = get_api_client()
    assert 0.1 == api.request_timeout


def test_client_factory_default_timeout(environment_settings):
    api = get_api_client()
    assert api.request_timeout is None


def test_parse_error():
    assert (-432, None, 'Bad santa!') == parse_response("-432\nBad santa!")


def test_parse_ok():
    assert (0, 3243, 'OK') == parse_response("0\n3243")
