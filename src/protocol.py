"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket
import time

class Message:
    """Message Type."""
    def __init__(self, command):
        self.command = command
  
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, command, channel):
        super().__init__(command)
        self.channel = channel

    def __str__(self) -> str:
        return str(json.dumps(self.__dict__)) # preciso de fazer json.dumps para substituir '' por ""

class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, command, name):
        super().__init__(command)
        self.user = name

    def __str__(self) -> str:
        return str(json.dumps(self.__dict__))
    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, command, msg, ts, channel=None):
        super().__init__(command)
        self.message = msg
        self.channel = channel
        self.ts = ts

    def __str__(self) -> str:
        dic = self.__dict__
        dic = {k: v for k, v in dic.items() if v is not None} # para nao enviar o channel se for None pcausa do assert
        return str(json.dumps(dic))

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage("register", username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage("join", channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage("message", message, int(time.time()), channel)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        data = str(msg) # isto funciona porcausa do __str__
        connection.send(len(data).to_bytes(2, 'big') + bytes(data,"utf-8"))

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        header = connection.recv(2) # get first two bytes to know how many bytes to get after
        header = int.from_bytes(header, "big")
        body = connection.recv(header) # return the exact bytes needed
        body = body.decode("utf-8")

        try:
            data = json.loads(body)
        except:
            raise CDProtoBadFormat(body)

        if data["command"] == "register":
            return RegisterMessage("register", data["user"])

        elif data["command"] == "join":
            return JoinMessage("join", data["channel"])

        elif data["command"] == "message":
            if "channel" in data: 
                return TextMessage("message", data["message"], data["ts"], data["channel"])
            else: 
                return TextMessage("message", data["message"], data["ts"])
    

class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
