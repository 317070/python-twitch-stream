#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This file contains the classes used to send videostreams to Twitch
"""
from __future__ import print_function, division
import numpy as np
import subprocess
import signal
import threading
import sys
try:
    import Queue as queue
except ImportError:
    import queue
import time
import os

import requests

AUDIORATE = 44100


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
    :param enable_audio: whether there will be sound or not
    :type enable_audio: boolean
    :param ffmpeg_binary: the binary to use to create a videostream
        This is usually ffmpeg, but avconv on some (older) platforms
    :type ffmpeg_binary: String
    :param verbose: show ffmpeg output in stdout
    :type verbose: boolean
    """
    def __init__(self,
                 twitch_stream_key,
                 width=640,
                 height=480,
                 fps=30.,
                 ffmpeg_binary="ffmpeg",
                 enable_audio=False,
                 verbose=False):
        self.twitch_stream_key = twitch_stream_key
        self.width = width
        self.height = height
        self.fps = fps
        self.ffmpeg_process = None
        self.audio_pipe = None
        self.ffmpeg_binary = ffmpeg_binary
        self.verbose = verbose
        self.audio_enabled = enable_audio
        try:
            self.reset()
        except OSError:
            print("There seems to be no %s available" % ffmpeg_binary)
            if ffmpeg_binary == "ffmpeg":
                print("ffmpeg can be installed using the following"
                      "commands")
                print("> sudo add-apt-repository "
                      "ppa:mc3man/trusty-media")
                print("> sudo apt-get update && "
                      "sudo apt-get install ffmpeg")
            sys.exit(1)

    def reset(self):
        """
        Reset the videostream by restarting ffmpeg
        """

        if self.ffmpeg_process is not None:
            # Close the previous stream
            try:
                self.ffmpeg_process.send_signal(signal.SIGINT)
            except OSError:
                pass

        command = []
        command.extend([
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
            '-thread_queue_size', '1024',
            '-i', '-',  # The input comes from a pipe

            # Twitch needs to receive sound in their streams!
            # '-an',            # Tells FFMPEG not to expect any audio
        ])
        if self.audio_enabled:
            command.extend([
                '-ar', '%d' % AUDIORATE,
                '-ac', '2',
                '-f', 's16le',
                '-thread_queue_size', '1024',
                '-i', '/tmp/audiopipe'
            ])
        else:
            command.extend([
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100'
            ])
        command.extend([
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
            '-f', 'flv', self.get_closest_ingest(),
        ])

        devnullpipe = subprocess.DEVNULL
        if self.verbose:
            devnullpipe = None
        self.ffmpeg_process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stderr=devnullpipe,
            stdout=devnullpipe)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # sigint so avconv can clean up the stream nicely
        self.ffmpeg_process.send_signal(signal.SIGINT)
        # waiting doesn't work because of reasons I don't know
        # self.pipe.wait()

    def send_video_frame(self, frame):
        """Send frame of shape (height, width, 3)
        with values between 0 and 1.
        Raises an OSError when the stream is closed.

        :param frame: array containing the frame.
        :type frame: numpy array with shape (height, width, 3)
            containing values between 0.0 and 1.0
        """

        assert frame.shape == (self.height, self.width, 3)

        frame = np.clip(255*frame, 0, 255).astype('uint8')
        try:
            self.ffmpeg_process.stdin.write(frame.tostring())
        except OSError:
            # The pipe has been closed. Reraise and handle it further
            # downstream
            raise

    def send_audio(self, left_channel, right_channel):
        """Add the audio samples to the stream. The left and the right
        channel should have the same shape.
        Raises an OSError when the stream is closed.

        :param left_channel: array containing the audio signal.
        :type left_channel: numpy array with shape (k, )
            containing values between -1.0 and 1.0. k can be any integer
        :param right_channel: array containing the audio signal.
        :type right_channel: numpy array with shape (k, )
            containing values between -1.0 and 1.0. k can be any integer
        """
        if self.audio_pipe is None:
            if not os.path.exists('/tmp/audiopipe'):
                os.mkfifo('/tmp/audiopipe')
            self.audio_pipe = os.open('/tmp/audiopipe', os.O_WRONLY)

        assert len(left_channel.shape) == 1
        assert left_channel.shape == right_channel.shape

        frame = np.column_stack((left_channel, right_channel)).flatten()

        frame = np.clip(32767*frame, -32767, 32767).astype('int16')
        try:
            os.write(self.audio_pipe, frame.tostring())
        except OSError:
            # The pipe has been closed. Reraise and handle it further
            # downstream
            raise

    def get_closest_ingest(self):
        closest_server = requests.get(url='https://ingest.twitch.tv/api/v2/ingests').json()['ingests'][0]
        url_template = closest_server['url_template']
        print("Streaming to closest server: %s at %s" % (closest_server['name'],
                                                         url_template.replace('/app/{stream_key}', '')))
        return url_template.format(
            stream_key=self.twitch_stream_key)


class TwitchOutputStreamRepeater(TwitchOutputStream):
    """
    This stream makes sure a steady framerate is kept by repeating the
    last frame when needed.

    Note: this will not generate a stable, stutter-less stream!
     It does not keep a buffer and you cannot synchronize using this
     stream. Use TwitchBufferedOutputStream for this.
    """
    def __init__(self, *args, **kwargs):
        super(TwitchOutputStreamRepeater, self).__init__(*args, **kwargs)

        self.lastframe = np.ones((self.height, self.width, 3))
        self._send_last_video_frame()   # Start sending the stream

        if self.audio_enabled:
            # some audible sine waves
            xl = np.linspace(0.0, 10*np.pi, int(AUDIORATE/self.fps) + 1)[:-1]
            xr = np.linspace(0.0, 100*np.pi, int(AUDIORATE/self.fps) + 1)[:-1]
            self.lastaudioframe_left = np.sin(xl)
            self.lastaudioframe_right = np.sin(xr)
            self._send_last_audio()   # Start sending the stream

    def _send_last_video_frame(self):
        try:
            super(TwitchOutputStreamRepeater,
                  self).send_video_frame(self.lastframe)
        except OSError:
            # stream has been closed.
            # This function is still called once when that happens.
            pass
        else:
            # send the next frame at the appropriate time
            threading.Timer(1./self.fps,
                            self._send_last_video_frame).start()

    def _send_last_audio(self):
        try:
            super(TwitchOutputStreamRepeater,
                  self).send_audio(self.lastaudioframe_left,
                                   self.lastaudioframe_right)
        except OSError:
            # stream has been closed.
            # This function is still called once when that happens.
            pass
        else:
            # send the next frame at the appropriate time
            threading.Timer(1./self.fps,
                            self._send_last_audio).start()

    def send_video_frame(self, frame):
        """Send frame of shape (height, width, 3)
        with values between 0 and 1.

        :param frame: array containing the frame.
        :type frame: numpy array with shape (height, width, 3)
            containing values between 0.0 and 1.0
        """
        self.lastframe = frame

    def send_audio(self, left_channel, right_channel):
        """Add the audio samples to the stream. The left and the right
        channel should have the same shape.

        :param left_channel: array containing the audio signal.
        :type left_channel: numpy array with shape (k, )
            containing values between -1.0 and 1.0. k can be any integer
        :param right_channel: array containing the audio signal.
        :type right_channel: numpy array with shape (k, )
            containing values between -1.0 and 1.0. k can be any integer
        """
        self.lastaudioframe_left = left_channel
        self.lastaudioframe_right = right_channel


class TwitchBufferedOutputStream(TwitchOutputStream):
    """
    This stream makes sure a steady framerate is kept by buffering
    frames. Make sure not to have too many frames in buffer, since it
    will increase the memory load considerably!

    Adding frames is thread safe.
    """
    def __init__(self, *args, **kwargs):
        super(TwitchBufferedOutputStream, self).__init__(*args, **kwargs)
        self.last_frame = np.ones((self.height, self.width, 3))
        self.last_frame_time = None
        self.next_video_send_time = None
        self.frame_counter = 0
        self.q_video = queue.PriorityQueue()

        # don't call the functions directly, as they block on the first
        # call
        self.t = threading.Timer(0.0, self._send_video_frame)
        self.t.daemon = True
        self.t.start()

        if self.audio_enabled:
            # send audio at about the same rate as video
            # this can be changed
            self.last_audio = (np.zeros((int(AUDIORATE/self.fps), )),
                               np.zeros((int(AUDIORATE/self.fps), )))
            self.last_audio_time = None
            self.next_audio_send_time = None
            self.audio_frame_counter = 0
            self.q_audio = queue.PriorityQueue()
            self.t = threading.Timer(0.0, self._send_audio)
            self.t.daemon = True
            self.t.start()

    def _send_video_frame(self):
        start_time = time.time()
        try:
            frame = self.q_video.get_nowait()
            # frame[0] is frame count of the frame
            # frame[1] is the frame
            frame = frame[1]
        except IndexError:
            frame = self.last_frame
        except queue.Empty:
            frame = self.last_frame
        else:
            self.last_frame = frame

        try:
            super(TwitchBufferedOutputStream, self
                  ).send_video_frame(frame)
        except OSError:
            # stream has been closed.
            # This function is still called once when that happens.
            # Don't call this function again and everything should be
            # cleaned up just fine.
            return

        # send the next frame at the appropriate time
        if self.next_video_send_time is None:
            self.t = threading.Timer(1./self.fps, self._send_video_frame)
            self.next_video_send_time = start_time + 1./self.fps
        else:
            self.next_video_send_time += 1./self.fps
            next_event_time = self.next_video_send_time - start_time
            if next_event_time > 0:
                self.t = threading.Timer(next_event_time,
                                         self._send_video_frame)
            else:
                # we should already have sent something!
                #
                # not allowed for recursion problems :-(
                # (maximum recursion depth)
                # self.send_me_last_frame_again()
                #
                # other solution:
                self.t = threading.Thread(
                    target=self._send_video_frame)

        self.t.daemon = True
        self.t.start()

    def _send_audio(self):
        start_time = time.time()
        try:
            _, left_audio, right_audio = self.q_audio.get_nowait()
        except IndexError:
            left_audio, right_audio = self.last_audio
        except queue.Empty:
            left_audio, right_audio = self.last_audio
        else:
            self.last_audio = (left_audio, right_audio)

        try:
            super(TwitchBufferedOutputStream, self
                  ).send_audio(left_audio, right_audio)
        except OSError:
            # stream has been closed.
            # This function is still called once when that happens.
            # Don't call this function again and everything should be
            # cleaned up just fine.
            return

        # send the next frame at the appropriate time
        downstream_time = len(left_audio) / AUDIORATE

        if self.next_audio_send_time is None:
            self.t = threading.Timer(downstream_time,
                                     self._send_audio)
            self.next_audio_send_time = start_time + downstream_time
        else:
            self.next_audio_send_time += downstream_time
            next_event_time = self.next_audio_send_time - start_time
            if next_event_time > 0:
                self.t = threading.Timer(next_event_time,
                                         self._send_audio)
            else:
                # we should already have sent something!
                #
                # not allowed for recursion problems :-(
                # (maximum recursion depth)
                # self.send_me_last_frame_again()
                #
                # other solution:
                self.t = threading.Thread(
                    target=self._send_audio)

        self.t.daemon = True
        self.t.start()

    def send_video_frame(self, frame, frame_counter=None):
        """send frame of shape (height, width, 3)
        with values between 0 and 1

        :param frame: array containing the frame.
        :type frame: numpy array with shape (height, width, 3)
            containing values between 0.0 and 1.0
        :param frame_counter: frame position number within stream.
            Provide this when multi-threading to make sure frames don't
            switch position
        :type frame_counter: int
        """
        if frame_counter is None:
            frame_counter = self.frame_counter
            self.frame_counter += 1

        self.q_video.put((frame_counter, frame))

    def send_audio(self,
                   left_channel,
                   right_channel,
                   frame_counter=None):
        """Add the audio samples to the stream. The left and the right
        channel should have the same shape.

        :param left_channel: array containing the audio signal.
        :type left_channel: numpy array with shape (k, )
            containing values between -1.0 and 1.0. l can be any integer
        :param right_channel: array containing the audio signal.
        :type right_channel: numpy array with shape (k, )
            containing values between -1.0 and 1.0. l can be any integer
        :param frame_counter: frame position number within stream.
            Provide this when multi-threading to make sure frames don't
            switch position
        :type frame_counter: int
        """
        if frame_counter is None:
            frame_counter = self.audio_frame_counter
            self.audio_frame_counter += 1

        self.q_audio.put((frame_counter, left_channel, right_channel))

    def get_video_frame_buffer_state(self):
        """Find out how many video frames are left in the buffer.
        The buffer should never run dry, or audio and video will go out
        of sync. Likewise, the more filled the buffer, the higher the
        memory use and the delay between you putting your frame in the
        stream and the frame showing up on Twitch.

        :return integer estimate of the number of video frames left.
        """
        return self.q_video.qsize()

    def get_audio_buffer_state(self):
        """Find out how many audio fragments are left in the buffer.
        The buffer should never run dry, or audio and video will go out
        of sync. Likewise, the more filled the buffer, the higher the
        memory use and the delay between you putting your frame in the
        stream and the frame showing up on Twitch.

        :return integer estimate of the number of audio fragments left.
        """
        return self.q_audio.qsize()

