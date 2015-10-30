.. python-twitch-stream documentation master file, created by
   sphinx-quickstart on Wed Oct 21 19:45:57 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to python-twitch-stream's documentation!
================================================

Python-twitch-stream is a simple lightweight library, which you can use to
send your python video to twitch and react with the chat in real time.
Its main features are:

* Supports sending of audio and video in a thread safe way to your twitch
  channel.
* Allows to interact with the chat of your channel by sending chat messages
  and reading what other users post.

There is a complete tutorial available at `Tutorial
<http://317070.github.io/python/>`_.

Installation
------------

In short, you can install the latest stable version over pip.

.. code-block:: bash

  pip install python-twitch-stream

Make sure to also install a recent ffmpeg version:

.. code-block:: bash

  sudo add-apt-repository ppa:mc3man/trusty-media
  sudo apt-get update && sudo apt-get install ffmpeg

The ffmpeg library needs to be very recent (written in october 2015).
There are plenty of bugs when
running a stream using older versions of ffmpeg or avconv, including but
not limited to 6GB of memory use, problems with the audio and
synchronization of the audio and the video.

Or alternatively, install the latest
python-twitch-stream development version via:

.. code-block:: bash

  pip install git+https://github.com/317070/python-twitch-stream


Support
-------

For support, please use the github issues on `the repository
<https://github.com/317070/python-twitch-stream/issues>`_.


Contents
========
.. toctree::
   :maxdepth: 2

  modules/chat
  modules/inputvideo
  modules/outputvideo
