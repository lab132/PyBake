"""This module runs commands given by the user."""

import sys
import os
import argparse
import textwrap
from PyBake import Path, version
from PyBake.logger import StdOutSink, LogVerbosity, log, LogBlock

# Make sure this module is executed, not imported.
if __name__ != '__main__':
  raise RuntimeError("This module is meant to be executed, not imported!")

# Insert current working dir to the sys path
# so we can import python modules from there.
sys.path.insert(0, os.getcwd())


# Data for Argparser

description = textwrap.dedent(
  """
  Dependency Management Tool for any kind of dependencies.
  A single dependency is referred to as a crumble.
  """)

ovenDescription = textwrap.dedent(
  """
  Tool to create crumbles.
  """)

basketDescription = textwrap.dedent(
  """
  Retrieves pastries from the shop.
  """)

depotDescription = textwrap.dedent(
  """
  Uploads crumbles to the server given a pastry info file.
  """
  )

serverDescription = textwrap.dedent(
  """
  Sets up a server for crumble management
  """)


def execute_shop(args):
  log.debug(args)
  from PyBake import shop
  shop.run(**vars(args))

def execute_basket(args):
  log.debug(args)
  from PyBake import basket
  basket.run(**vars(args))

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
mainParser = argparse.ArgumentParser(prog="PyBake", description=description)
mainParser.add_argument("-V", "--Version", action="version",
                        version="%(prog)s v{Major}.{Minor}.{Patch}".format(**version))
mainParser.add_argument("-q", "--quiet", default=False, action="store_true")
mainParser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Set the verbosity of the output, "
                        "more v's generates more verbose output (Up to 8). "
                        "Default is {0}".format(int(LogVerbosity.Success)))

# Subparsers
# ====
subparsers = mainParser.add_subparsers(dest="CommandName", title="Commands")
# Commands are required except when calling -h or -V
subparsers.required = True

# OvenParser
# ====
ovenParser = subparsers.add_parser("oven", help=ovenDescription, description=ovenDescription)

ovenParser.add_argument("pastry_name",
                        type=str,
                        help="The name of the crumble to create.")
ovenParser.add_argument("pastry_version",
                        type=str,
                        help="The version of the crumble.")
ovenParser.add_argument("-r", "--recipe", type=str, default="recipe", dest="recipe_name",
                        help="Name of the recipe module. "
                        "This module is expected to live directly in the working directory, "
                        "not any sub-directory, with the name `<RECIPE>.py`.")
ovenParser.add_argument("-o", "--output", type=Path, default=Path("pastry.zip"),
                        help="The resulting JSON file relative to the original working dir. Ignored --working-dir")
ovenParser.add_argument("-d", "--working-dir", type=Path, default=Path("."),
                        help="The working directory when executing the RECIPE.")
ovenParser.add_argument("--no-indent-output", action="store_true", default=False,
                        help="Whether to produce a compressed NOT human-friendly, unindented JSON file.")
ovenParser.set_defaults(func=execute_oven)

# DepotParser
# =============

depotParser = subparsers.add_parser("depot", help=depotDescription, description=depotDescription)

depotParser.add_argument("pastry_path",
                         type=Path,
                         nargs="?",
                         default=Path("pastry.zip"),
                         help="Path to the pastry file (defaults to \"./pastry.zip\").")

depotParser.add_argument("-c", "--config",
                         default="config",
                         help="Name of the python module containing configuration data. "
                         "This file must exist in the working directory. (defaults to \"config\").")
depotParser.set_defaults(func=execute_depot)

# StockParser
# ============

basketParser = subparsers.add_parser("basket", help=basketDescription, description=basketDescription)

basketParser.add_argument("shopping_list", nargs="?", default="shoppingList",
                         help="Sets the used shoppingList (defaults to 'shoppingList') which will be reused"
                         "to retrieve pastries from the shop.")
basketParser.add_argument("-l", "--location",
                         default="user",
                         choices=["local", "user", "system"],
                         help="Where to save the pastries to.")
basketParser.set_defaults(func=execute_basket)

# ServerParser
# ====

shopParser = subparsers.add_parser("shop", help=serverDescription, description=serverDescription)

shopParser.add_argument("-c", "--config", default="shop_config",
                        help="Supply a custom config for the shop (defaults to shop_config")
shopParser.set_defaults(func=execute_shop)

# Main
# ====

log.addLogSink(StdOutSink())

args = mainParser.parse_args()

# Set to Default if no -v is provided at all
if args.verbose == 0:
  args.verbose = int(LogVerbosity.Success)
log.verbosity = LogVerbosity(args.verbose)
log.quiet = args.quiet

args.func(args)