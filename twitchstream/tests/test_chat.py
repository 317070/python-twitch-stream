#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Tests for chat.py
"""


def test_logged_in_successful():
    """
    Test TwitchChatStream._logged_in_successful
    """
    from twitchstream.chat import TwitchChatStream
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv NOTICE * :Error logging in")
    assert res is False
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv NOTICE * :Error logging in\n")
    assert res is False
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv NOTICE * :Error logging in\r\n")
    assert res is False
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv 001 sdsd :Welcome, GLHF!")
    assert res is True
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv 001 sdsd :Your host is tmi.twitch.tv")
    assert res is True
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv 001 sdsd :This server is rather new")
    assert res is True
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv 001 sdsd :-!")
    assert res is True
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv 001 sdsd :You are in a maze of twisty passages,"
        " all alike.")
    assert res is True
    res = TwitchChatStream._logged_in_successful(
        ":tmi.twitch.tv 001 sdsd :>")
    assert res is True
