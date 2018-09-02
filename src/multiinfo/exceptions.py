# coding=utf-8
import logging

log = logging.getLogger(__name__)


class MultiInfoException(Exception):
    pass


class MultiInfoConfigurationException(Exception):
    pass


class ClientException(MultiInfoException):
    """Base client exception with data attribute"""

    def __init__(self, message, data=None, *args):
        super(ClientException, self).__init__(message, *args)
        self.data = data
