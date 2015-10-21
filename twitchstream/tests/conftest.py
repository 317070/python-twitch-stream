#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Configuration of the testing
"""
import pytest


def pytest_addoption(parser):
    """
    Add options for testing
    :param parser:
    :return:
    """
    parser.addoption("--runslow",
                     action="store_true",
                     help="run slow tests")


def pytest_runtest_setup(item):
    """
    Skip the slow tests when running with --runslow
    :param item:
    :return:
    """
    if 'slow' in item.keywords and \
            not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run")
