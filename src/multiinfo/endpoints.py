# coding=utf-8
from datetime import datetime
from enum import IntEnum

import six
from box import Box

from multiinfo import exceptions

from .base import BaseEndpoint, BaseModel


class DateTimeProperty(object):
    format = '%d%m%y%H%M%S'

    def __init__(self, name):
        self.name = name
        self.value = None

    def __get__(self, instance, owner):
        # noinspection PyProtectedMember
        value = instance._data.get(self.name)
        return datetime.strptime(value, self.format) if value and isinstance(value, six.string_types) else value

    def __set__(self, instance, value):
        if not isinstance(value, six.string_types):  # pragma: no cover
            value = value.strftime(self.format)
        # noinspection PyProtectedMember
        instance._data[self.name] = value


class Sms(BaseModel):
    _endpoint = 'sendsms.aspx'
    _data_wrap = 'invoice'

    #: okres ważności wiadomości, maksymalny okres czasu ważności to 72 godziny
    #: obowiązkowy: nie
    #: typ: data
    #: wartość: ciąg znaków w formacie ddMMyyHHmmss
    validTo = DateTimeProperty('validTo')

    #: Podczas wysyłki wiadomości w kodowaniu GSM (standardowy sposób) niektóre znaki
    #: liczone są jako dwa, dlatego też mają one wpływ na maksymalną długość wysyłanej
    #: wiadomości SMS.
    #:
    #: Uwaga ta nie dotyczy wysyłania wiadomości SMS z włączoną opcją kodowania
    #: rozszerzonego.
    #:
    #: Znaki liczone podwójnie to: [ ] { } | \\ ^
    #:
    #: Należy więc zwrócić uwagę, iż użycie tych znaków spowoduje skrócenie (ze 160 znaków)
    #: maksymalnej długości pojedynczej wiadomości.
    advancedEncoding = 'true'

    @property
    def text(self):
        return self._data['text']

    @text.setter
    def text(self, value):
        max_text_len = 160
        assert len(value) < max_text_len, "Maximum text length exceeded: {} > {}".format(len(value), max_text_len)
        self._data['text'] = value

    # noinspection PyAttributeOutsideInit
    def send(self):
        response = self._api_client.get(self.get_endpoint(), data=self._data)
        self.message_id = get_message_id(response)
        return self


class LongSms(Sms):
    _endpoint = 'sendsmslong.aspx'

    @property
    def text(self):
        return self._data['text']

    @text.setter
    def text(self, value):
        max_text_len = 1377
        assert len(value) < max_text_len, "Maximum text length exceeded: {} > {}".format(len(value), max_text_len)
        self._data['text'] = value


def get_message_id(response_text):
    status_code, message_id, status_reason = parse_response(response_text)

    if status_code >= 0:
        return message_id

    msg = "{}: {}".format(status_code, status_reason)
    raise exceptions.ClientException(msg)


def parse_response(content):
    lines = content.splitlines()
    line1 = int(lines[0])
    line2 = lines[1]
    if line1 >= 0:
        return line1, int(line2), "OK"
    return line1, None, line2


class SendSms(BaseEndpoint):
    model = Sms

    def send(self, **kwargs):
        return self.model(self.api_client, **kwargs).send()


class SendLongSms(BaseEndpoint):
    model = LongSms

    def send(self, **kwargs):
        return self.model(self.api_client, **kwargs).send()


STATUS_MAPPING = {
    "0": "Wiadomość przyjęta do przetwarzania",
    "1": "Wiadomość w trakcie przetwarzania",
    "3": "Wiadomość przekazana do SMSC, oczekiwanie potwierdzenie doręczenia wiadomości",
    "7": "Wiadomość wstrzymana z powodu przekroczenia limitu",
    "11": "Błąd fatalny, wysyłanie nieudane",
    "12": "Wiadomość przedawniona",
    "13": "Wiadomość usunięta",
    "21": "Wiadomość przesłana pomyślnie",
}


class BodyType(IntEnum):
    text = 1
    binary = 2


def parse_status_info(text):
    lines = text.splitlines()
    data = {
        'request_status': lines[0],
        'sms_id': lines[1],
        'body_type': BodyType(int(lines[2])),
        'text': lines[3],
        'protocol': int(lines[4]),
        'encoding': int(lines[5]),
        'service_id': int(lines[6]),
        'connector_id': int(lines[7]),
        'response_to_id': int(lines[8]),
        'priority': int(lines[9]),
        'send_date': datetime.strptime(lines[10], '%d%m%y%H%M%S'),
        'valid_to': datetime.strptime(lines[11], '%d%m%y%H%M%S'),
        'report_delivery': lines[12].lower() != 'false',
        'sender_name': lines[13],
        'dest': lines[14],
        'message_status': (int(lines[15]), STATUS_MAPPING[lines[15]]),
        'last_change_date': datetime.strptime(lines[16], '%Y-%m-%d %H:%M:%S'),
    }
    return Box(data)


class InfoSms(BaseEndpoint):

    def get(self, sms_id):
        text = self.api_client.get('infosms.aspx', data={"smsId": sms_id})
        return parse_status_info(text)
