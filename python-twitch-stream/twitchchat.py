import numpy as np
import subprocess as sp
import time
import signal
import socket
import sys
import re
import fcntl, os
import errno
import threading
from models.default import TWITCH_STREAM_KEY, TWITCH_OAUTH, TWITCH_USERNAME


class TwitchChatStream(object):

    user = ""
    oauth = ""
    s = None

    @staticmethod
    def twitch_login_status(data):
        if not re.match(r'^:(testserver\.local|tmi\.twitch\.tv) NOTICE \* :Login unsuccessful\r\n$', data):
            return True
        else:
            return False

    def __init__(self, user=TWITCH_USERNAME, oauth=TWITCH_OAUTH):
        self.user = user
        self.oauth= oauth
        self.last_sent_time = time.time()
        self.twitch_connect()

    def twitch_connect(self):
        print("Connecting to twitch.tv")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.setblocking(False)
        #s.settimeout(1.0)
        connect_host = "irc.twitch.tv"
        connect_port = 6667
        try:
            s.connect((connect_host, connect_port))
        except:
            pass #expected, because is non-blocking socket
            sys.exit()
        print("Connected to twitch")
        print("Sending our details to twitch...")
        #s.send('USER %s\r\n' % self.user)
        s.send('PASS %s\r\n' % self.oauth)
        s.send('NICK %s\r\n' % self.user)

        if not TwitchChatStream.twitch_login_status(s.recv(1024)):
            print("... and they didn't accept our details")
            sys.exit()
        else:
            print("... they accepted our details")
            print("Connected to twitch.tv!")
            fcntl.fcntl(s, fcntl.F_SETFL, os.O_NONBLOCK)
            if self.s is not None:
                self.s.close()
            self.s = s
            s.send('JOIN #%s\r\n' % self.user)

    def send(self, message):
        if time.time() - self.last_sent_time > 5:
            if len(message) > 0:
                try:
                    self.s.send(message + "\n")
                    #print message
                finally:
                    self.last_sent_time = time.time()

    @staticmethod
    def check_has_ping(data):
        return re.match(r'^PING :(tmi\.twitch\.tv|\.testserver\.local)$', data)

    def send_pong(self):
        self.send("PONG")

    def send_chat_message(self, message):
        self.send("PRIVMSG #{0} :{1}".format(self.user, message))

    @staticmethod
    def check_has_message(data):
        return re.match(r'^:[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+(\.tmi\.twitch\.tv|\.testserver\.local) PRIVMSG #[a-zA-Z0-9_]+ :.+$', data)

    def parse_message(self, data):
        if TwitchChatStream.check_has_ping(data):
            self.send_pong()
        if TwitchChatStream.check_has_message(data):
            return {
                'channel': re.findall(r'^:.+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+.+ PRIVMSG (.*?) :', data)[0],
                'username': re.findall(r'^:([a-zA-Z0-9_]+)\!', data)[0],
                'message': re.findall(r'PRIVMSG #[a-zA-Z0-9_]+ :(.+)', data)[0].decode('utf8')
            }
        else:
            return None

    def twitch_recieve_messages(self, amount=1024):
        result = []
        while True: #process the complete buffer, until no data is left no more
            try:
                msg = self.s.recv(4096) # NON-BLOCKING RECEIVE!
                if msg:
                    pass
                    #print msg
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    #print 'No more data available'
                    return result
                else:
                    # a "real" error occurred
                    import traceback
                    import sys
                    print(traceback.format_exc())

                    text_file = open("log1.txt", "w")
                    text_file.write(traceback.format_exc())
                    text_file.close()

                    self.twitch_connect()
                    return result
            except:
                import traceback
                import sys
                print(traceback.format_exc())

                text_file = open("log2.txt", "w")
                text_file.write(traceback.format_exc())
                text_file.close()

                self.twitch_connect()
                return result
            else:
                rec = [self.parse_message(line) for line in filter(None, msg.split('\r\n'))]
                rec = [r for r in rec if r] #remove None's
                result.extend(rec)
