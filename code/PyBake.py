'''
Baking py since 2015
'''

import socket
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
    #s.connect()
    s.bind(serveradress)
    s.listen(5)

    print("Server is listening on port {0}".format(serveradress[1]))

    while True:
        connection, address = s.accept()
        print('Connected with ' + address[0] + ':' + str(address[1]))

        data = connection.recv(4096)
        
        connection.sendall( bytes("Received: " +str(data, "UTF-8"), "UTF-8") )

        connection.shutdown( socket.SHUT_RDWR )
        connection.close()

@command("client")
def client():
    
    s = socket.socket()
    s.connect(serveradress)

    data = input("Give some data:")

    s.sendall(bytes(data, "UTF-8"))

    received = s.recv(4096)
    print("Received: {0}".format(data))

if __name__ == "__main__":
    commands[argv[1]]()
