#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This file contains the classes used to send videostreams to Twitch
"""

import numpy as np
import subprocess as sp
import signal
import threading


class TwitchOutputStream(object):
    """
    Initialize a TwitchOutputStream object and starts the pipe.
    The stream is only started on the first frame.

    :param twitch_stream_key:
    :type twitch_stream_key:
    :param width: the width of the videostream (in pixels)
    :type width: int
    :param height: the height of the videostream (in pixels)
    :type height: int
    :param fps: the number of frames per second of the videostream
    :type fps: float
    :param ffmpeg_binary: the binary to use to create a videostream
        This is usually ffmpeg, but avconv on some (older) platforms
    :type ffmpeg_binary: String
    """
    def __init__(self,
                 twitch_stream_key,
                 width=640,
                 height=480,
                 fps=30.,
                 ffmpeg_binary="ffmpeg"):
        self.twitch_stream_key = twitch_stream_key
        self.width = width
        self.height = height
        self.fps = fps
        self.pipe = None
        self.ffmpeg_binary = ffmpeg_binary
        self.reset()

    def reset(self):
        """
        Reset the videostream by restarting ffmpeg
        """

        if self.pipe is not None:
            # Close the previous stream
            try:
                self.pipe.send_signal(signal.SIGINT)
            except OSError:
                pass

        command = [
            self.ffmpeg_binary,
            '-loglevel', 'verbose',
            '-y',       # overwrite previous file/stream
            # '-re',    # native frame-rate
            '-analyzeduration', '1',
            '-f', 'rawvideo',
            '-r', '%d' % self.fps,  # set a fixed frame rate
            '-vcodec', 'rawvideo',
            # size of one frame
            '-s', '%dx%d' % (self.width, self.height),
            '-pix_fmt', 'rgb24',  # The input are raw bytes
            '-i', '-',            # The input comes from a pipe

            # Twitch needs to receive sound in their streams!
            # '-an',            # Tells FFMPEG not to expect any audio
            '-ar', '8000',
            '-ac', '1',
            '-f', 's16le',
            '-i', '/dev/zero',  # silence alternative, works forever.
            # '-i','http://stream1.radiostyle.ru:8001/tunguska',
            # '-filter_complex',
            # '[0:1][1:0]amix=inputs=2:duration=first[all_audio]'

            # VIDEO CODEC PARAMETERS
            '-vcodec', 'libx264',
            '-r', '%d' % self.fps,
            '-b:v', '3000k',
            '-s', '%dx%d' % (self.width, self.height),
            '-preset', 'faster', '-tune', 'zerolatency',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            # '-force_key_frames', r'expr:gte(t,n_forced*2)',
            '-minrate', '3000k', '-maxrate', '3000k',
            '-bufsize', '12000k',
            '-g', '60',     # key frame distance
            '-keyint_min', '1',
            # '-filter:v "setpts=0.25*PTS"'
            # '-vsync','passthrough',

            # AUDIO CODEC PARAMETERS
            '-acodec', 'libmp3lame', '-ar', '44100', '-b:a', '160k',
            # '-bufsize', '8192k',
            '-ac', '1',
            # '-acodec', 'aac', '-strict', 'experimental',
            # '-ab', '128k', '-ar', '44100', '-ac', '1',
            # '-async','44100',
            # '-filter_complex', 'asplit', #for audio sync?

            # STORE THE VIDEO PARAMETERS
            # '-vcodec', 'libx264', '-s', '%dx%d'%(width, height),
            # '-preset', 'libx264-fast',
            # 'my_output_videofile2.avi'

            # MAP THE STREAMS
            # use only video from first input and only audio from second
            '-map', '0:v', '-map', '1:a',

            # NUMBER OF THREADS
            '-threads', '2',

            # STREAM TO TWITCH
            '-f', 'flv', 'rtmp://live-ams.twitch.tv/app/%s' %
            self.twitch_stream_key
            ]

        fh = open("/dev/null", "w")     # Throw away stream
        # fh = None     # uncomment this line for viewing ffmpeg output
        self.pipe = sp.Popen(
            command,
            stdin=sp.PIPE,
            stderr=fh,
            stdout=fh)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # sigint so avconv can clean up the stream nicely
        self.pipe.send_signal(signal.SIGINT)
        # waiting doesn't work because reasons I don't know
        # self.pipe.wait()

    def send_frame(self, frame):
        """send frame of shape (height, width, 3)
        with values between 0 and 1

        :param frame: array containing the frame.
        :type frame: numpy array with shape (height, width, 3)
            containing values between 0.0 and 1.0

        """
        if self.pipe.poll():
            self.reset()
        assert (frame.shape == (self.height, self.width, 3),
                "Frame has the wrong shape %s iso %s" %
                (frame.shape, (self.height, self.width, 3)))

        frame = np.clip(255*frame, 0, 255).astype('uint8')
        self.pipe.stdin.write(frame.tostring())


class TwitchOutputStreamRepeater(TwitchOutputStream):
    """
    This stream makes sure a steady framerate is kept by repeating the
    last frame when needed.

    Note: this will not make for a stable, stutter-less stream!
     It does not keep a buffer and you cannot synchronize using this
     stream.
    """
    def __init__(self, *args, **kwargs):
        super(TwitchOutputStreamRepeater, self).__init__(*args, **kwargs)
        self.lastframe = np.ones((self.height, self.width, 3))
        self.send_me_last_frame_again()     # Start sending the stream

    def send_me_last_frame_again(self):
        try:
            super(TwitchOutputStreamRepeater,
                  self).send_frame(self.lastframe)
        except IOError:
            # stream has been closed.
            # This function is still called once when that happens.
            pass
        else:
            # send the next frame at the appropriate time
            threading.Timer(1./self.fps,
                            self.send_me_last_frame_again).start()

    def send_frame(self, frame):
        """send frame of shape (height, width, 3)
        with values between 0 and 1

        :param frame: array containing the frame.
        :type frame: numpy array with shape (height, width, 3)
            containing values between 0.0 and 1.0

        """
        self.lastframe = frame
