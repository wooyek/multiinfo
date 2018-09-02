# coding=utf-8
"""
Top-level package for MultiInfo SMS API project.

Python wrapper for Polkomtel's MultiInfo SMS service

"""
from __future__ import absolute_import

from .core import get_api_client  # noqa F401
from .endpoints import LongSms, Sms  # noqa F401

__author__ = """Janusz Skonieczny"""
__email__ = 'js+pypi@bravelabs.pl'
__version__ = '0.4.0'
