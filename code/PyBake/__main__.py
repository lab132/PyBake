"""This module runs commands given by the user."""

# Make sure this module is executed, not imported.
if __name__ != '__main__':
    raise Error("This module is meant to be executed, not imported!")

import sys
import argparse
import textwrap

## Data for Argparser

version ={
    "Release" : 0,
    "Major" : 0,
    "Minor" : 1,
}
description = textwrap.dedent(
    """
    Dependency Management Tool for any kind of dependencies.
    A single dependency is referred to as a crumble.
    """
    )

ovenDescription = textwrap.dedent(
    """
    Tool to create crumbles.
    """
)

clientDescription = textwrap.dedent(
    """
    Syncs all dependencies of the current Project with the server.
    """
)

def server(args):
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

def execute_client(args):
    #import crumble
    print(args)
    print(args.config.read())
    #response = json.load(urlopen("{0}/list_packages".format(crumble.server)))
    #print(response)

def execute_oven(args):
    print("Executing oven")
    print(args)
    #recipeScript = "recipe.py" if len(sys.argv) == 2 else sys.argv[2]
    #from PyBake import oven
    #oven.run(recipeScript)


## Main Parser
## ====
mainParser = argparse.ArgumentParser(prog="PyBake",description=description)
mainParser.add_argument("-V", "--Version", action="version", version="%(prog)s v{Release}.{Major}.{Minor}".format(**version))

## Subparsers
## ====
subparsers = mainParser.add_subparsers(dest="CommandName",title="Commands")
# Commands are required except when calling -h or -V
subparsers.required = True

## OvenParser
## ====
ovenParser = subparsers.add_parser("oven", help=ovenDescription, description=ovenDescription)

ovenParser.add_argument("-r", "--recipe", default="recipe.py", help="Supply a custom recipe, (defaults to recipe.py)")
ovenParser.set_defaults(func=execute_oven)

## ClientParser
## ====

clientParser = subparsers.add_parser("client", help=clientDescription, description=clientDescription)

clientParser.add_argument("-c" , "--config", type=argparse.FileType(mode="r", encoding="UTF-8"), default="config.py",
                          help="Supply a custom config for the client (defaults to config.py)")
clientParser.set_defaults(func=execute_client)

## Main
## ====

args = mainParser.parse_args()

args.func(args)
