'''
Baking py since 2015
'''

import socket
import os
from sys import argv
import urllib2
import json


clientConnection = ("87.160.255.156",1337)
serveradress = ("192.168.0.150",1337)




commands = {}

def command(name):
    def commandwrapper(f):
        commands[name] = f
        return f
    return commandwrapper

@command("server")
def server():

    from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify
    # create our little application :)
    app = Flask(__name__)
    # Load default config and override config from an environment variable

    app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
    ))
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

    @app.route("/list_packages")
    def listPackages():
        p = os.listdir(".")
        print(p)
        return jsonify({"values" : p})


    app.run(debug=True,port=1337,host="0.0.0.0")

@command("client")
def client():
    response = json.load(urllib2.urlopen("http://127.0.0.1:1337/list_packages"))
    print(response)

if __name__ == "__main__":
    commands[argv[1]]()
