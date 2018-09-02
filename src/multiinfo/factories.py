# coding=utf-8

import factory

from . import endpoints
from .core import ApiClient

api_client = ApiClient(login='bad-username', password='bad-password')


class SmsFactory(factory.Factory):
    class Meta:
        model = endpoints.Sms

    api_client = api_client
    dest = factory.Faker('msisdn')
    text = factory.Faker('text', max_nb_chars=160)


class LongSmsFactory(SmsFactory):
    class Meta:
        model = endpoints.LongSms

    text = factory.Faker('text', max_nb_chars=1377)
