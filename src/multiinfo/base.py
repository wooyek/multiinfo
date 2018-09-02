# coding=utf-8
import logging
from itertools import chain

log = logging.getLogger(__name__)


class BaseEndpoint(object):
    def __init__(self, api_client):
        self.api_client = api_client


class BaseModel(object):
    def __init__(self, api_client, **kwargs):
        super(BaseModel, self).__setattr__('_api_client', kwargs.pop('api_client', api_client))
        super(BaseModel, self).__setattr__('_data', {'id': None})
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_raw_data(self):
        return self._data

    def update_data(self, **kwargs):
        self._update_data(kwargs)

    def _update_data(self, data):
        new_id = data.get('id', None)
        if self.id and new_id:
            assert self.id == new_id, 'Existing id does not match update data {}!={}'.format(self.id, new_id)
        self._data.update(data)

    def __setattr__(self, name, value):
        if name in chain(self.__dict__.keys(), self.__class__.__dict__.keys()):
            return super(BaseModel, self).__setattr__(name, value)
        self._data[name] = value

    def __getattr__(self, key):
        if key not in self._data:
            msg = '{} instance does not have {} key in data dictionary, you may have to call get to fetch full data dict.'
            raise AttributeError(msg.format(self.__class__.__name__, key))
        return self._data[key]

    __getitem__ = __getattr__

    def get_endpoint(self):
        return self._endpoint
