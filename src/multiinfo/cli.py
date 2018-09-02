# -*- coding: utf-8 -*-

"""Console script for multiinfo."""
import logging
from pprint import pprint

import click
import click_log
from dynaconf import default_settings
from dynaconf.base import Settings

from multiinfo import get_api_client

log = logging.getLogger(__name__)
click_log.basic_config(log)


class Context(object):

    def __init__(self) -> None:
        self.LOGIN = None
        self.PASSWORD = None
        self.KEY_PATH = None
        self.CERT_PATH = None
        self.settings = None

    def get_api(self):
        if not self.settings:
            return get_api_client()
        default_settings.DYNACONF_NAMESPACE = 'MULTIINFO'
        settings = Settings(settings_module=self.settings)
        return get_api_client(settings=settings)


context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option('-l', '--login', default='')
@click.option('-p', '--password', default='')
@click.option('-k', '--keyfile', type=click.Path())
@click.option('-c', '--certfile', type=click.Path())
@click.option('-s', '--settings', type=click.Path(), help="File with multiinfo configuration settings")
@click_log.simple_verbosity_option(logging.getLogger())
@context
def main(ctx, login, password, keyfile, certfile, settings):
    """Send SMS by Polkomtel's MultiInfo service."""
    logging.basicConfig(
        format='%(asctime)s %(levelname)-7s %(thread)-5d %(filename)s:%(lineno)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ctx.login = login
    ctx.password = password
    ctx.keyfile = keyfile
    ctx.certfile = certfile
    ctx.settings = settings


@main.command()
@click.argument('phone')
@click.argument('message', nargs=-1)
@context
def sms(ctx, phone, message):
    """Send one short SMS message max 160 chars"""
    try:
        message = " ".join(message)
        ctx.get_api().send_sms.send(dest=phone, text=message)
    except Exception as ex:
        click.echo(str(ex))
        logging.debug("", exc_info=ex)


@main.command()
@click.argument('phone')
@click.argument('message', nargs=-1)
@context
def longsms(ctx, phone, message):
    """Send multiple SMS messages up to 1377 chars"""
    try:
        message = " ".join(message)
        ctx.get_api().send_long_sms.send(dest=phone, text=message)
    except Exception as ex:
        click.echo(str(ex))
        logging.debug("", exc_info=ex)


@main.command()
@click.argument('sms_id')
@context
def info(ctx, sms_id):
    """Send multiple SMS messages up to 1377 chars"""
    try:
        info = ctx.get_api().info_sms.get(sms_id=sms_id)
        click.echo(pprint(info))
    except Exception as ex:
        click.echo(str(ex))
        logging.debug("", exc_info=ex)


if __name__ == "__main__":
    main()
