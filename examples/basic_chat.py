#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a small example which connects to a user's chat channel to
send and receive the messages posted there
"""
from __future__ import print_function
from twitchstream.outputvideo import TwitchOutputStreamRepeater
from twitchstream.chat import TwitchChatStream
import argparse
import time
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-u', '--username',
                          help='twitch username',
                          required=True)
    required.add_argument('-o', '--oauth',
                          help='twitch oauth '
                               '(visit https://twitchapps.com/tmi/ '
                               'to create one for your account)',
                          required=True)
    args = parser.parse_args()

    # Launch a verbose (!) twitch stream
    with TwitchChatStream(username=args.username,
                          oauth=args.oauth,
                          verbose=True) as chatstream:

        # Send a message to this twitch stream
        chatstream.send_chat_message("I'm reading this!")

        # Continuously check if messages are received (every ~10s)
        # This is necessary, if not, the chat stream will close itself
        # after a couple of minutes (due to ping messages from twitch)
        while True:
            received = chatstream.twitch_receive_messages()
            if received:
                print("received:", received)
            time.sleep(1)
