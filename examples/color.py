#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a small example which creates a twitch stream to connect with
and changes the color of the video according to the colors provided in
the chat.
"""
from __future__ import print_function
from twitchstream.outputvideo import TwitchBufferedOutputStream
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
    required.add_argument('-s', '--streamkey',
                          help='twitch streamkey',
                          required=True)
    args = parser.parse_args()
    # TODO: merge two with statements
    with TwitchChatStream(username=args.username,
                          oauth=args.oauth,
                          verbose=False) as chatstream:

        with TwitchBufferedOutputStream(
                twitch_stream_key=args.streamkey,
                width=640,
                height=480,
                fps=30.) as videostream:

            chatstream.send_chat_message("Taking requests!")

            frame = np.zeros((480, 640, 3))

            while True:
                received = chatstream.twitch_receive_messages()
                if received:
                    if received[0]['message'] == "black":
                        frame[:, :, :] = np.array(
                            [0, 0, 0])[None, None, :]
                    elif received[0]['message'] == "red":
                        frame[:, :, :] = np.array(
                            [1, 0, 0])[None, None, :]
                    elif received[0]['message'] == "green":
                        frame[:, :, :] = np.array(
                            [0, 1, 0])[None, None, :]
                    elif received[0]['message'] == "blue":
                        frame[:, :, :] = np.array(
                            [0, 0, 1])[None, None, :]
                    elif received[0]['message'] == "cyan":
                        frame[:, :, :] = np.array(
                            [0, 1, 1])[None, None, :]
                    elif received[0]['message'] == "magenta":
                        frame[:, :, :] = np.array(
                            [1, 0, 1])[None, None, :]
                    elif received[0]['message'] == "yellow":
                        frame[:, :, :] = np.array(
                            [1, 1, 0])[None, None, :]
                    elif received[0]['message'] == "white":
                        frame[:, :, :] = np.array(
                            [1, 1, 1])[None, None, :]

                videostream.send_frame(frame)
                time.sleep(1.0 / videostream.fps)
