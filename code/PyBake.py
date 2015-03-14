'''
Baking py since 2015
'''

import socket
from pathlib import Path
from sys import argv

serveradress = ("127.0.0.1",1337)


commands = {}

def command(name):
    def commandwrapper(f):
        commands[name] = f
        return f
    return commandwrapper

@command("server")
def server():

    print("Starting up Server")

    s = socket.socket()
    s.bind(serveradress)
    s.listen(5)

    print("Server is listening on port {0}".format(serveradress[1]))

    while True:
        connection, address = s.accept()
        print('Connected with ' + address[0] + ':' + str(address[1]))

        data = connection.recv(4096)
        fileName = str(data,"UTF-8")


        filePath = Path(".", fileName)

        print("Filepath is: {0}".format(filePath))

        if filePath.exists():
            fileHandle = filePath.open("br")
            fileContents = fileHandle.read()
            fileHandle.close()

            connection.sendall(b"1" +  fileContents)

        else:
            connection.sendall(b"0" + bytes("File not found","UTF-8"))


        connection.shutdown( socket.SHUT_RDWR )
        connection.close()

@command("client")
def client():
    
    s = socket.socket()
    s.connect(serveradress)

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
