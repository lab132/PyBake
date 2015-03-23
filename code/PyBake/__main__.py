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
from PyBake import Path, version
from PyBake.logger import StdOutSink, LogVerbosity, log, LogBlock

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

depotDescription = textwrap.dedent(
  """
  Uploads crumbles to the server given a pastry info file.
  """
  )

serverDescription = textwrap.dedent(
    """
    Sets up a server for crumble management
    """
    )

def execute_shop(args):
    log.debug(args)
    from PyBake import shop
    shop.run(**vars(args))

def execute_client(args):
    log.debug(args)
    response = json.load(urlopen("{0}/list_packages".format(crumble.server)))
    log.success(response)

def execute_oven(args):
    log.info("Executing oven")
    from PyBake import oven
    oven.run(**vars(args))

def execute_depot(args):
  with LogBlock("Depot"):
    log.debug(args)
    from PyBake import depot
    depot.run(**vars(args))


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

## DepotParser
## =============

depotParser = subparsers.add_parser("depot", help=depotDescription, description=depotDescription)

depotParser.add_argument("pastry_path",
                         type=Path,
                         default=Path("pastry.json"),
                         help="Path to the pastry file (defaults to \"./pastry.json\").")

depotParser.add_argument("-c" , "--config",
                         default="config",
                         help="Name of the python module containing configuration data. This file must exist in the working directory. (defaults to \"config\").")
depotParser.set_defaults(func=execute_depot)

## ClientParser
## ====

clientParser = subparsers.add_parser("client", help=clientDescription, description=clientDescription)

clientParser.add_argument("-c" , "--config", default="config",
                          help="Supply a custom config for the client (defaults to config)")
clientParser.set_defaults(func=execute_client)

## ServerParser
## ====

shopParser = subparsers.add_parser("shop", help=serverDescription, description=serverDescription)

shopParser.add_argument("-c" , "--config", default="shop_config",
                          help="Supply a custom config for the shop (defaults to shop_config")
shopParser.set_defaults(func=execute_shop)

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
