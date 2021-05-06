#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This file contains the python code used to interface with the Twitch
chat. Twitch chat is IRC-based, so it is basically an IRC-bot, but with
special features for Twitch, such as congestion control built in.
"""
from __future__ import print_function
import time
import socket
import re
import fcntl
import os
import errno


class TwitchChatStream(object):
    """
    The TwitchChatStream is used for interfacing with the Twitch chat of
    a channel. To use this, an oauth-account (of the user chatting)
    should be created. At the moment of writing, this can be done here:
    https://twitchapps.com/tmi/

    :param username: Twitch username
    :type username: string
    :param oauth: oauth for logging in (see https://twitchapps.com/tmi/)
    :type oauth: string
    :param verbose: show all stream messages on stdout (for debugging)
    :type verbose: boolean
    """

    def __init__(self, username, oauth, verbose=False):
        """Create a new stream object, and try to connect."""
        self.username = username
        self.oauth = oauth
        self.verbose = verbose
        self.current_channel = ""
        self.last_sent_time = time.time()
        self.buffer = []
        self.s = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.s.close()

    @staticmethod
    def _logged_in_successful(data):
        """
        Test the login status from the returned communication of the
        server.

        :param data: bytes received from server during login
        :type data: list of bytes

        :return boolean, True when you are logged in.
        """
        if re.match(r'^:(testserver\.local|tmi\.twitch\.tv)'
                    r' NOTICE \* :'
                    r'(Login unsuccessful|Error logging in)*$',
                    data.strip()):
            return False
        else:
            return True

    @staticmethod
    def _check_has_ping(data):
        """
        Check if the data from the server contains a request to ping.

        :param data: the byte string from the server
        :type data: list of bytes
        :return: True when there is a request to ping, False otherwise
        """
        return re.match(
            r'^PING :tmi\.twitch\.tv$', data)

    @staticmethod
    def _check_has_channel(data):
        """
        Check if the data from the server contains a channel switch.

        :param data: the byte string from the server
        :type data: list of bytes
        :return: Name of channel when new channel, False otherwise
        """
        return re.findall(
            r'^:[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+'
            r'\.tmi\.twitch\.tv '
            r'JOIN #([a-zA-Z0-9_]+)$', data)

    @staticmethod
    def _check_has_message(data):
        """
        Check if the data from the server contains a message a user
        typed in the chat.

        :param data: the byte string from the server
        :type data: list of bytes
        :return: returns iterator over these messages
        """
        return re.match(r'^:[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+'
                        r'\.tmi\.twitch\.tv '
                        r'PRIVMSG #[a-zA-Z0-9_]+ :.+$', data)

    def connect(self):
        """
        Connect to Twitch
        """

        # Do not use non-blocking stream, they are not reliably
        # non-blocking
        # s.setblocking(False)
        # s.settimeout(1.0)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect_host = "irc.twitch.tv"
        connect_port = 6667
        try:
            s.connect((connect_host, connect_port))
        except (Exception, IOError):
            print("Unable to create a socket to %s:%s" % (
                connect_host,
                connect_port))
            raise  # unexpected, because it is a blocking socket

        # Connected to twitch
        # Sending our details to twitch...
        s.send(('PASS %s\r\n' % self.oauth).encode('utf-8'))
        s.send(('NICK %s\r\n' % self.username).encode('utf-8'))
        if self.verbose:
            print('PASS %s\r\n' % self.oauth)
            print('NICK %s\r\n' % self.username)

        received = s.recv(1024).decode()
        if self.verbose:
            print(received)
        if not TwitchChatStream._logged_in_successful(received):
            # ... and they didn't accept our details
            raise IOError("Twitch did not accept the username-oauth "
                          "combination")
        else:
            # ... and they accepted our details
            # Connected to twitch.tv!
            # now make this socket non-blocking on the OS-level
            fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)
            if self.s is not None:
                self.s.close()  # close the previous socket
            self.s = s          # store the new socket
            self.join_channel(self.username)

            # Wait until we have switched channels
            while self.current_channel != self.username:
                self.twitch_receive_messages()

    def _push_from_buffer(self):
        """
        Push a message on the stack to the IRC stream.
        This is necessary to avoid Twitch overflow control.
        """
        if len(self.buffer) > 0:
            if time.time() - self.last_sent_time > 5:
                try:
                    message = self.buffer.pop(0)
                    self.s.send(message.encode('utf-8'))
                    if self.verbose:
                        print(message)
                finally:
                    self.last_sent_time = time.time()

    def _send(self, message):
        """
        Send a message to the IRC stream

        :param message: the message to be sent.
        :type message: string
        """
        if len(message) > 0:
            self.buffer.append(message + "\n")

    def _send_pong(self):
        """
        Send a pong message, usually in reply to a received ping message
        """
        self._send("PONG")

    def join_channel(self, channel):
        """
        Join a different chat channel on Twitch.
        Note, this function returns immediately, but the switch might
        take a moment

        :param channel: name of the channel (without #)
        """
        self.s.send(('JOIN #%s\r\n' % channel).encode('utf-8'))
        if self.verbose:
            print('JOIN #%s\r\n' % channel)

    def send_chat_message(self, message):
        """
        Send a chat message to the server.

        :param message: String to send (don't use \\n)
        """
        self._send("PRIVMSG #{0} :{1}".format(self.username, message))

    def _parse_message(self, data):
        """
        Parse the bytes received from the socket.

        :param data: the bytes received from the socket
        :return:
        """
        if TwitchChatStream._check_has_ping(data):
            self._send_pong()
        if TwitchChatStream._check_has_channel(data):
            self.current_channel = \
                TwitchChatStream._check_has_channel(data)[0]

        if TwitchChatStream._check_has_message(data):
            return {
                'channel': re.findall(r'^:.+![a-zA-Z0-9_]+'
                                      r'@[a-zA-Z0-9_]+'
                                      r'.+ '
                                      r'PRIVMSG (.*?) :',
                                      data)[0],
                'username': re.findall(r'^:([a-zA-Z0-9_]+)!', data)[0],
                'message': re.findall(r'PRIVMSG #[a-zA-Z0-9_]+ :(.+)',
                                      data)[0]
            }
        else:
            return None

    def twitch_receive_messages(self):
        """
        Call this function to process everything received by the socket
        This needs to be called frequently enough (~10s) Twitch logs off
        users not replying to ping commands.

        :return: list of chat messages received. Each message is a dict
            with the keys ['channel', 'username', 'message']
        """
        self._push_from_buffer()
        result = []
        while True:
            # process the complete buffer, until no data is left no more
            try:
                msg = self.s.recv(4096).decode()     # NON-BLOCKING RECEIVE!
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    # There is no more data available to read
                    return result
                else:
                    # a "real" error occurred
                    # import traceback
                    # import sys
                    # print(traceback.format_exc())
                    # print("Trying to recover...")
                    self.connect()
                    return result
            else:
                if self.verbose:
                    print(msg)
                rec = [self._parse_message(line)
                       for line in filter(None, msg.split('\r\n'))]
                rec = [r for r in rec if r]     # remove Nones
                result.extend(rec)
