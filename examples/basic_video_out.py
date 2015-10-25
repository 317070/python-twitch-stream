#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a small example which creates a twitch stream to connect with
and changes the color of the video according to the colors provided in
the chat.
"""
from __future__ import print_function
from twitchstream.outputvideo import TwitchOutputStreamRepeater
import argparse
import time
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-s', '--streamkey',
                          help='twitch streamkey',
                          required=True)
    args = parser.parse_args()

    with TwitchOutputStreamRepeater(
            twitch_stream_key=args.streamkey,
            width=640,
            height=480,
            fps=30.,
            verbose=True) as videostream:

        frame = np.zeros((480, 640, 3))

        while True:
            frame = np.random.rand(480, 640, 3)
            videostream.send_frame(frame)
            time.sleep(1./videostream.fps)
