#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a small example which creates a twitch stream to connect with
and changes the color of the video according to the colors provided in
the chat.
"""
from twitchstream.outputvideo import TwitchOutputStreamRepeater
from twitchstream.chat import TwitchChatStream
import argparse
import time

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

    print args.username
    print args.oauth
    with TwitchChatStream(username=args.username,
                          oauth=args.oauth) as chatstream:

        #chatstream.send_chat_message("Hello World!")
        while True:
            received = chatstream.twitch_receive_messages()
            if received:
                print("rec:", received)
            time.sleep(1)
