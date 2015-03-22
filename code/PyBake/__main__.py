"""This module runs commands given by the user."""

# Make sure this module is executed, not imported.
if __name__ != '__main__':
    raise RuntimeError("This module is meant to be executed, not imported!")

import sys
import os

# Insert current working dir to the sys path so we can import python modules from there.
sys.path.insert(0, os.getcwd())

import argparse
import textwrap
from PyBake import Path
from PyBake.logging import *

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

serverDescription = textwrap.dedent(
    """
    Sets up a server for crumble management
    """
    )

def execute_server(args):
    log.debug(args)
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
        Log.success(p)
        return jsonify({"values" : p})
    import crumble
    app.run(debug=True, host=crumble.server.host, port=crumble.server.port)

def execute_client(args):
    import crumble
    log.debug(args)
    #Log.log(args.config.read())
    response = json.load(urlopen("{0}/list_packages".format(crumble.server)))
    log.success(response)

def execute_oven(args):
    log.info("Executing oven")
    from PyBake import oven
    oven.run(**vars(args))

## Main Parser
## ====
mainParser = argparse.ArgumentParser(prog="PyBake",description=description)
mainParser.add_argument("-V", "--Version", action="version", version="%(prog)s v{Release}.{Major}.{Minor}".format(**version))
mainParser.add_argument("-q", "--quiet", default=False, action="store_true")
mainParser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Set the verbosity of the output, more v's generates more verbose output (Up to 8). Default is {0}".format(int(LogVerbosity.Success)))

## Subparsers
## ====
subparsers = mainParser.add_subparsers(dest="CommandName",title="Commands")
# Commands are required except when calling -h or -V
subparsers.required = True

## OvenParser
## ====
ovenParser = subparsers.add_parser("oven", help=ovenDescription, description=ovenDescription)

ovenParser.add_argument("pastry_name",
                        type=str,
                        help="The name of the crumble to create.")
ovenParser.add_argument("pastry_version",
                        type=str,
                        help="The version of the crumble.")
ovenParser.add_argument("-r", "--recipe", type=str, default="recipe",
                        help="Name of the recipe module. This module is expected to live directly in the working directory, not sub-directory, with the name `<recipe>.py`.")
ovenParser.add_argument("-o", "--output", type=Path, default=Path("pastry.json"),
                        help="The resulting JSON file relative to the working dir.")
ovenParser.add_argument("-d", "--working-dir", type=Path, default=Path("."),
                        help="The working directory.")
ovenParser.add_argument("--no-indent-output", action="store_true", default=False,
                        help="Whether to produce a compressed NOT human-friendly, unindented JSON file.")
ovenParser.set_defaults(func=execute_oven)

## ClientParser
## ====

clientParser = subparsers.add_parser("client", help=clientDescription, description=clientDescription)

clientParser.add_argument("-c" , "--config", type=argparse.FileType(mode="r", encoding="UTF-8"), default="config.py",
                          help="Supply a custom config for the client (defaults to config.py)")
clientParser.set_defaults(func=execute_client)

## ServerParser
## ====

serverParser = subparsers.add_parser("server", help=serverDescription, description=serverDescription)

serverParser.add_argument("-c" , "--config", type=argparse.FileType(mode="r", encoding="UTF-8"), default="serverconfig.py",
                          help="Supply a custom config for the server (defaults to serverconfig.py")
serverParser.set_defaults(func=execute_server)

## Main
## ====

log.addLogSink(StdOutSink())

args = mainParser.parse_args()

# Set to Default if no -v is provided at all
if args.verbose == 0:
  args.verbose = int(LogVerbosity.Success)
log.verbosity = LogVerbosity(args.verbose)
log.quiet = args.quiet

args.func(args)
