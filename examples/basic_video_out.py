#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a small example which creates a twitch stream to connect with
and changes the color of the video according to the colors provided in
the chat.
"""
from __future__ import print_function
from twitchstream.outputvideo import TwitchOutputStreamRepeater, TwitchBufferedOutputStream
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

    with TwitchBufferedOutputStream(
            twitch_stream_key=args.streamkey,
            width=640,
            height=480,
            fps=30.,
            verbose=True,
            audio_enabled=True) as videostream:

        frame = np.zeros((480, 640, 3))

        while True:
            if videostream.get_video_frame_buffer_state() < 30:
                # print("V",videostream.get_video_buffer_state())
                frame = np.random.rand(480, 640, 3)
                videostream.send_video_frame(frame)

            if videostream.get_audio_buffer_state() < 30:
                # print("A",videostream.get_video_buffer_state())
                left_audio = np.random.randn(1470)
                right_audio = np.random.randn(1470)
                videostream.send_audio(left_audio, right_audio)

