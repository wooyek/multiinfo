#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `multiinfo` package."""
import logging

from click.testing import CliRunner

from multiinfo import cli


# noinspection PyMethodMayBeStatic
class CliTests(object):
    def test_no_arguments(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert "Send SMS by Polkomtel's MultiInfo service" in result.output
        assert 'Usage: main [OPTIONS] COMMAND [ARGS]' in result.output

    def test_help(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main, ['--help'])
        assert result.exit_code == 0
        assert "Send SMS by Polkomtel's MultiInfo service" in result.output
        assert 'Usage: main [OPTIONS] COMMAND [ARGS]' in result.output

    def test_with_settings(self, mocker):
        mocker.patch('dynaconf.loaders.yaml_loader.load')
        get_api_client = mocker.patch('multiinfo.cli.get_api_client')
        runner = CliRunner()
        result = runner.invoke(cli.main, ['-s', 'missing.yml', 'sms', '123', 'lorem', 'ipsum'])
        assert result.exit_code == 0
        assert get_api_client.called


# noinspection PyMethodMayBeStatic
class SmsCommandTests(object):
    # noinspection PyUnusedLocal
    def test_send(self, mocker, environment_settings):
        request = mocker.patch('conftest.MockedApiClient.request')
        runner = CliRunner()
        result = runner.invoke(cli.main, ['sms', '123', 'lorem', 'ipsum'])
        logging.debug("result.output: %s", result.output)
        assert result.exit_code == 0
        assert request.called
        params = request.call_args[1]['params']
        assert 'lorem ipsum' == params['text']
        assert '123' == params['dest']

    def test_missing_settings(self):
        runner = CliRunner()
        result = runner.invoke(cli.main, ['-s', 'missing.yml', 'sms', '123', 'lorem', 'ipsum'])
        assert result.exit_code == 0
        assert "No such file or directory: 'missing.yml'" in result.output


# noinspection PyMethodMayBeStatic
class LongSmsCommandTests(object):
    # noinspection PyUnusedLocal
    def test_send(self, mocker, environment_settings):
        request = mocker.patch('conftest.MockedApiClient.request')
        runner = CliRunner()
        result = runner.invoke(cli.main, ['longsms', '123', 'lorem', 'ipsum'])
        logging.debug("result.output: %s", result.output)
        assert result.exit_code == 0
        assert request.called
        params = request.call_args[1]['params']
        assert 'lorem ipsum' == params['text']
        assert '123' == params['dest']

    def test_missing_settings(self):
        runner = CliRunner()
        result = runner.invoke(cli.main, ['-s', 'missing.yml', 'longsms', '123', 'lorem', 'ipsum'])
        assert result.exit_code == 0
        assert "No such file or directory: 'missing.yml'" in result.output
