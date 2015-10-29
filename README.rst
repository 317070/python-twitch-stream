.. image:: https://readthedocs.org/projects/python-twitch-stream/badge/
    :target: http://python-twitch-stream.readthedocs.org/en/latest/

.. image:: https://travis-ci.org/317070/python-twitch-stream.svg
    :target: https://travis-ci.org/317070/python-twitch-stream

.. image:: https://coveralls.io/repos/317070/python-twitch-stream/badge.svg
    :target: https://coveralls.io/github/317070/python-twitch-stream

.. image:: https://img.shields.io/badge/license-MIT-green.svg
    :target: https://github.com/Lasagne/Lasagne/blob/master/LICENSE

Python-Twitch-Stream
====================

Python-twitch-stream is a simple lightweight library, which you can use to
send your python video to twitch and react with the chat in real time.
Its main features are:

* Supports sending of audio and video in a thread safe way to your twitch
  channel.
* Allows to interact with the chat of your channel by sending chat messages
  and reading what other users post.


Installation
------------

In short, you can install a known compatible version of ffmpeg and the latest
python-twitch-stream development version via:

.. code-block:: bash

  pip install git+https://github.com/317070/python-twitch-stream
  sudo add-apt-repository ppa:mc3man/trusty-media
  sudo apt-get update && sudo apt-get install ffmpeg

Or alternatively, install the latest stable version over pip.

.. code-block:: bash

  pip install python-twitch-stream
  sudo add-apt-repository ppa:mc3man/trusty-media
  sudo apt-get update && sudo apt-get install ffmpeg

The ffmpeg library needs to be very recent. There are plenty of bugs when
running a stream using older versions of ffmpeg and avconv, including but
not limited too 6GB of memory use, problems with the audio and
synchronization of the audio and the video.

Documentation
-------------

Documentation is available online: http://python-twitch-stream.readthedocs.org/

For support, please use the github issues on `the repository
<https://github.com/317070/python-twitch-stream/issues>`_.


Example
-------

This is a small example which creates a twitch stream which
changes the color of the video according to the colors provided in
the chat.

.. code-block:: python

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



For a fully-functional example, see `examples/color.py <examples/color.py>`_,
and check the `Tutorial
<http://317070.github.io/python/l>`_ for in-depth
explanations of the same. More examples, code snippets and reproductions of
recent research papers are maintained in the `examples directory
<examples>`_.


Development
-----------

Python-twitch-stream is a work in progress, but is stable. Feel free to ask
for features or add pull-requests with updates on the code.
