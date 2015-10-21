#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import subprocess as sp
import signal
import threading

class TwitchOutputStream(object):
    def __init__(self, width=640, height=480, fps=30., twitch_stream_key=TWITCH_STREAM_KEY):
        self.twitch_stream_key = twitch_stream_key
        self.width = width
        self.height = height
        self.fps = fps
        self.pipe = None
        self.reset()

    def reset(self):
        if self.pipe is not None:
            try:
                self.pipe.send_signal(signal.SIGINT)
            except OSError:
                pass


        FFMPEG_BIN = "avconv" # on Linux and Mac OS
        command = [ FFMPEG_BIN,
                        '-y', # overwrite
                        #'-re',# native frame-rate
                '-analyzeduration','1',
                '-f', 'rawvideo',
                '-r', '%d'%self.fps,
                '-vcodec','rawvideo',
                '-s', '%dx%d'%(self.width, self.height), # size of one frame
                '-pix_fmt', 'rgb24',
                #'-an', # Tells FFMPEG not to expect any audio
                #'-r', '%d'%fps, # frames per second
                '-i', '-', # The input comes from a pipe

                #'-i', 'silence.mp3', #otherwise, there is no sound in the output, which twitch doesn't like
                #'-ar', '48000', '-ac', '2', '-f', 's16le', '-i', '/dev/zero', #silence alternative, works forever. (Memory hole?)
                '-i','http://stream1.radiostyle.ru:8001/tunguska',
                        #'-filter_complex', '[0:1][1:0]amix=inputs=2:duration=first[all_audio]'
                #'-vcodec', 'libx264',
                '-vcodec', 'libx264', '-r', '%d'%self.fps, '-b:v', '3000k', '-s', '%dx%d'%(self.width, self.height),
                                '-preset', 'veryfast',#'-tune', 'film',
                                '-crf','23',
                                '-pix_fmt', 'yuv420p', #'-force_key_frames', r'expr:gte(t,n_forced*2)',
                                '-minrate', '3000k', '-maxrate', '3000k', '-bufsize', '12000k',
                                '-g','60',
                                '-keyint_min','1',
                #'-filter:v "setpts=0.25*PTS"'
                '-vsync','passthrough',
                #'-acodec', 'libmp3lame', '-ar', '44100', '-b', '160k',
                #               '-bufsize', '8192k', '-ac', '2',
                #'-acodec', 'aac', '-strict', 'normal', '-ab', '128k',
                #'-vcodec', 'libx264', '-s', '%dx%d'%(width, height), '-preset', 'libx264-fast',
                #'my_output_videofile2.avi'
                '-map', '0:v', '-map', '1:a', #use only video from first input and only audio from second
                '-threads', '1',
                '-f', 'flv', 'rtmp://live-fra.twitch.tv/app/%s'%self.twitch_stream_key
                ]

        fh = open("/dev/null", "w")
        #fh = None #uncomment for viewing ffmpeg output
        self.pipe = sp.Popen( command, stdin=sp.PIPE, stderr=fh, stdout=fh)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        #sigint so avconv can clean up the stream nicely
        self.pipe.send_signal(signal.SIGINT)
        #waiting doesn't work because reasons
        #self.pipe.wait()

    #send frame of shape (height, width, 3) with values between 0 and 1
    def send_frame(self, frame):
        if self.pipe.poll():
            self.reset()
        assert frame.shape == (self.height, self.width, 3), "Frame has the wrong shape %s iso %s"%(frame.shape,(self.height, self.width, 3))
        frame = np.clip(255*frame, 0, 255).astype('uint8')
        self.pipe.stdin.write( frame.tostring() )

"""
    This stream makes sure a steady framerate is kept by repeating the last frame when needed
"""
class TwitchOutputStreamRepeater(TwitchOutputStream):
    def __init__(self, *args, **kwargs):
        super(TwitchOutputStreamRepeater, self).__init__(*args, **kwargs)
        self.lastframe = np.ones((self.height, self.width, 3))
        self.send_me_last_frame_again()

    def send_me_last_frame_again(self):
        try:
            super(TwitchOutputStreamRepeater, self).send_frame(self.lastframe)
        except IOError:
            pass #stream has been closed. This function is still called once when that happens.
        else:
            #send the next frame at the appropriate time
            threading.Timer(1./self.fps, self.send_me_last_frame_again).start()

    def send_frame(self, frame):
        self.lastframe = frame
