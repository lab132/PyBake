import socket
from utils import *
from crumble import *

class Baker(object):
    """The guy who gets things done."""

    def __init__(self, connectionInfo):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(connectionInfo)
        self.socket.listen(5)

    def serve(self):
        self.connection, self.address = self.socket.accept()

    def close(self):
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()

    def error(self, message):
        message = bytes(message,"UTF-8")
        c = Crumble(CrumbleType.Error)
        c.contentLength += sizeof(message)
        self.connection.sendall(c.pack())
        self.connection.sendall(message)
        self.close()
