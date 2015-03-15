'''
Baking py since 2015
'''

import socket
from pathlib import Path
from sys import argv
from crumble import *

clientConnection = ("87.160.255.156",1337)
serveradress = ("192.168.0.150",1337)


commands = {}

class Baker:
    pass

def command(name):
    def commandwrapper(f):
        commands[name] = f
        return f
    return commandwrapper

@command("server")
def server():
    print("Starting up Server")

    baker = Baker()

    print("Server is listening on port {0}".format(serveradress[1]))

    while True:
        baker.serve()
        print('Connected with ' + address[0] + ':' + str(address[1]))

        data = baker.connection.recv(4096)
        fileName = str(data,"UTF-8")


        filePath = Path(".", fileName)

        print("Filepath is: {0}".format(filePath))

        if filePath.exists():
            c = Crumble(CrumbleType.PackageFile)

            fileContents = None
            with filePath.open("br") as fileHandle:
                fileContents = fileHandle.read()

            baker.connection.sendall(b"1" +  fileContents)
            baker.close()

        else:
            baker.error("File not found")

@command("client")
def client():
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(clientConnection)

    data = input("FileName:")

    s.sendall(bytes(data, "UTF-8"))

    filePath = Path(data + ".client")


    received = s.recv(1)
    if received == b"1":
        print("Receiving valid file")
        fileHandle = filePath.open("wb")

        while True:
            received = s.recv(4096)
            if not received:
                break
            fileHandle.write(received)

        print("All contents received")
        fileHandle.close()
    elif received == b"0":
        print("File was not found on server")
    else:
        print("Unknown return code")

    s.shutdown( socket.SHUT_RDWR )
    s.close()

    print("Connection closed")

if __name__ == "__main__":
    commands[argv[1]]()
