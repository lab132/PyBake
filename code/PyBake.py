'''
Baking py since 2015
'''

import os
import sys

# Insert current working dir to the sys path so we can import the crumble in there.
sys.path.insert(0, os.getcwd())

try:
    import crumble
except:
    print("Unable to load crumble.py")
    raise

import socket
import importlib
from urllib.request import urlopen
import json
import pathlib

class ServerConfig:
    """docstring"""
    def __init__(self, *, host, port=1337, protocol="http"):
        self.host = host
        self.port = port
        self.protocol = protocol

    def __str__(self):
        return "{0.protocol}://{0.host}:{0.port}".format(self)

    def __repr__(self):
        return "Server config {0}".format(self)

Path = pathlib.Path

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

    app.run(debug=True, host=crumble.server.host, port=crumble.server.port)

@command("client")
def client():
    response = json.load(urlopen("{0}/list_packages".format(crumble.server)))
    print(response)

@command("oven")
def oven():
    # This command used an ingredients.json and a recipe.py file to generate a crumble (server-side package)
    pass

if __name__ == "__main__":
    commands[sys.argv[1]]()
