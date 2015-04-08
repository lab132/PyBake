"""This module runs commands given by the user."""

import sys
import os
import argparse
import textwrap
from PyBake import Path, version, zipCompressionLookup
from PyBake.logger import StdOutSink, LogVerbosity, log, LogBlock
import pkgutil
from importlib import import_module

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

serverDescription = textwrap.dedent(
  """
  Sets up a server for crumble management
  """)


def execute_shop(args):
  """Execute the `shop` command."""
  log.debug(args)
  from PyBake import shop
  return shop.run(**vars(args))


def execute_basket(args):
  """Execute the `basket` command."""
  log.debug(args)
  from PyBake import basket
  return basket.run(**vars(args))


def execute_oven(args):
  """Execute the `oven` command."""
  log.info("Executing oven")
  from PyBake import oven
  args.compression = zipCompressionLookup[args.compression]
  return oven.run(**vars(args))

# Main Parser
# ===========
mainParser = argparse.ArgumentParser(prog="PyBake", description=description)
mainParser.add_argument("-V", "--Version", action="version",
                        version="%(prog)s v{Major}.{Minor}.{Patch}".format(**version))
mainParser.add_argument("-q", "--quiet", default=False, action="store_true")
mainParser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Set the verbosity of the output, "
                        "more v's generates more verbose output (Up to 8). "
                        "Default is {0}".format(int(LogVerbosity.Success)))

# Subparsers
# ==========
subparsers = mainParser.add_subparsers(dest="CommandName", title="Commands")
# Commands are required except when calling -h or -V
subparsers.required = True

pyBakeSubmodules = [name for _, name in pkgutil.iter_modules(['PyBake'])]

for module in pyBakeSubmodules:
  importedModule = import_module("PyBake.{}".format(module))
  if hasattr(importedModule, "moduleManager"):
    importedModule.moduleManager.createSubParser(subparsers)

# OvenParser
# ==========
ovenParser = subparsers.add_parser("oven", help=ovenDescription, description=ovenDescription)

ovenParser.add_argument("recipes_script",
                        type=Path,
                        nargs="?",
                        default=Path("recipes.py"),
                        help="Path to the recipes script. Default: 'recipes.py'")
ovenParser.add_argument("-o", "--output", type=Path, default=Path(".pastries"),
                        help="The directory to store the pastries in. Defaults to '.pastries'.")
ovenParser.add_argument("-d", "--working-dir",
                        type=Path,
                        nargs="?",
                        default=Path.cwd(),
                        help="The working directory when executing the `recipes_script`. Defaults to the current working dir.")
ovenParser.add_argument("-c", "--compression",
                        choices=zipCompressionLookup.keys(),
                        default="deflated",
                        help="The compression method used to create a pastry.")
ovenParser.set_defaults(func=execute_oven)


# BasketParser
# ===========

basketParser = subparsers.add_parser("basket", help=basketDescription, description=basketDescription)

basketParser.add_argument("shopping_list",
                          nargs="?",
                          default="shoppingList",
                          help="Sets the used shoppingList (defaults to 'shoppingList') which will be reused"
                          "to retrieve pastries from the shop.")
basketParser.add_argument("-l", "--location",
                          default="user",
                          choices=["local", "user", "system"],
                          help="Where to save the pastries to.")
basketParser.set_defaults(func=execute_basket)

# ServerParser
# ============

shopParser = subparsers.add_parser("shop", help=serverDescription, description=serverDescription)

shopParser.add_argument("-c", "--config", default="shop_config",
                        help="Supply a custom config for the shop (defaults to shop_config")
shopParser.set_defaults(func=execute_shop)


# Main
# ====


def main():
  """Main function of this script. Mainly serves as a scope."""
  log.addLogSink(StdOutSink())

  args = mainParser.parse_args()

  # Set to Default if no -v is provided at all
  if args.verbose == 0:
    args.verbose = int(LogVerbosity.Success)
  log.verbosity = LogVerbosity(args.verbose)
  log.quiet = args.quiet

  result = args.func(args)
  sys.exit(result)

main()
