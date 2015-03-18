'''
Baking py since 2015
'''

import os
import sys

# Insert current working dir to the sys path so we can import python modules from there.
sys.path.insert(0, os.getcwd())

import socket
import importlib
from urllib.request import urlopen
import json
import pathlib
from copy import deepcopy
from importlib import import_module

# Relative path to the user-defined script.
userRecipe = "recipe"

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

class Platform:
    """Object describing a platform such as 'Windows 64 bit VisualStudio2013 Debug'."""

    def __init__(self, *, name=None, detailed_name=None, bits=64, generator=None, config="Debug", user_data=None):
        self.name = name
        self.detailed_name = detailed_name
        self.bits = bits
        self.generator = generator
        self.config = config
        self.user_data = user_data

    def isValid(self):
        return self.name is not None or self.detailed_name is not None

    def __str__(self):
        if self.detailed_name is not None:
            return self.detailed_name
        return self.name

    def __repr__(self):
        return "<{0.name} ({0.detailed_name}) {0.bits} bit {0.generator} {0.config}: {0.user_data}".format(self)

    # Represents all platforms.
    All = None # Is initialized after the declaration of this class

    @staticmethod
    def FromDict(desc):
        result = Platform()
        result.name          = desc.get("name", result.name)
        result.detailed_name = desc.get("detailed_name", result.detailed_name)
        result.bits          = desc.get("bits", result.bits)
        result.generator     = desc.get("generator", result.generator)
        result.config        = desc.get("config", result.config)
        result.user_data     = desc.get("user_data", result.user_data)
        return result

Platform.All = Platform(name="all")

class Pastry:
    """File meta data."""
    def __init__(self, path):
        self.path = path

class Ingredient:
    """A wrapper for an existing file that has tags attached to it."""
    def __init__(self, path, *, platform=Platform.All, tags=[]):
        self.path = path
        self.platform = platform
        self.tags = tags

    def __str__(self):
        return "{0.path.name}<{0.platform}>{0.tags}".format(self)

    def __repr__(self):
        return "{}<{}>{}".format(repr(self.path.name), repr(self.platform), repr(self.tags))

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
    import crumble
    app.run(debug=True, host=crumble.server.host, port=crumble.server.port)

@command("client")
def client():
    import crumble
    response = json.load(urlopen("{0}/list_packages".format(crumble.server)))
    print(response)

@command("oven")
def oven():
    """
    This command uses a recipe.py file to generate a pastry.json (server-side package/crumble).
    """
    global recipes
    recipes = []

    # Import recipe.py, which should be defined by the user.
    # This will register functions in the global variable `recipes`.
    recipe = import_module(userRecipe)

    print("Ingredients:")
    for ing in recipe.ingredients:
        print("  {0}".format(repr(ing)))

if __name__ == "__main__":
    commands[sys.argv[1]]()
