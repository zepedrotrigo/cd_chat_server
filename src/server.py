"""CD Chat server program."""
import logging
import socket, selectors
from src.protocol import CDProto, CDProtoBadFormat
import json

logging.basicConfig(filename="server.log", level=logging.DEBUG)

class Server:
    """Chat Server process."""
    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', 6666))
        self.sock.listen(100)
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        self.sockets = {} # Key: connection, value: [username, ch1, ch2, ...]

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        try:
            msg = CDProto.recv_msg(conn)
        except CDProtoBadFormat as err:
            msg = None

        if msg != None:
            if msg.command == "register":
                self.sockets[conn] = [msg.user] # add to sockets dictionary
                print("{} connected.".format(self.sockets[conn][0]))
                logging.debug("{} connected.".format(self.sockets[conn][0]))

            elif msg.command == "message":
                if msg.channel != None:
                    message = CDProto.message(msg.message, msg.channel)
                else:
                    message = CDProto.message(msg.message)

                for k,v in self.sockets.items():
                    if (msg.channel == None or msg.channel in v):
                        CDProto.send_msg(k, message)
                        print("sending message from {} to {} in #{}.".format(self.sockets[conn][0], v[0], msg.channel))
                        logging.debug("sending message from {} to {} in #{}.".format(self.sockets[conn][0], v[0], msg.channel))

            elif msg.command == "join":
                lst = self.sockets.get(conn)

                if msg.channel in lst: # a bit pointless, but organized
                    lst.remove(msg.channel)

                lst.append(msg.channel)
                self.sockets[conn] = lst
                print("{} joined {}".format(self.sockets[conn][0], msg.channel))
                logging.debug("{} joined {}".format(self.sockets[conn][0], msg.channel))

        else:
            print("{} disconnected.".format(self.sockets[conn][0]))
            logging.debug("{} disconnected.".format(self.sockets[conn][0]))
            self.sockets.pop(conn)

            self.sel.unregister(conn)
            conn.close()


    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)