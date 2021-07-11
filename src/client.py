"""CD Chat client program"""
import logging
from .protocol import CDProto, CDProtoBadFormat
import socket, selectors, fcntl, os, sys, json

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.channel = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.send_msg)
        self.sel.register(self.sock, selectors.EVENT_READ, self.receive_msg)
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sock.connect(('localhost', 6666))
        self.sock.setblocking(False)
        print("You are now connected to the server. Start typing!")

    def send_msg(self):
        s1 = sys.stdin.read()

        if s1 == "exit\n":
            sys.exit()
        elif s1.startswith("/join"):
            self.channel = s1.split()[1]
            msg = CDProto.join(self.channel)
        else:
            msg = CDProto.message(s1, self.channel)
        
        CDProto.send_msg(self.sock, msg)

    def receive_msg(self):
        msg = CDProto.recv_msg(self.sock)

        if msg != None:
            print(msg.message, end="")
            logging.debug(msg.message)

    def loop(self):
        """Loop indefinetely.""" 
        #send register message:
        register_msg = CDProto.register(self.name)
        CDProto.send_msg(self.sock, register_msg)

        try:
            while True:
                events = self.sel.select()

                for key, mask in events:
                    callback = key.data
                    callback()

        except KeyboardInterrupt:
            self.sel.unregister(sys.stdin)
            self.sel.unregister(self.sock)
            self.sock.close()