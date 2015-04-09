"""This module runs commands given by the user."""

import sys
import os
import argparse
import textwrap
from PyBake import Path, version, zipCompressionLookup
from PyBake.logger import StdOutSink, LogVerbosity, log, LogBlock
import pkgutil
from importlib import import_module
import re

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

pyBakeSubmodules = [name for _, name, _ in pkgutil.iter_modules(['PyBake']) if re.search("__[\w]+__",name) is None]

for module in pyBakeSubmodules:
  importedModule = import_module("PyBake.{}".format(module))
  if hasattr(importedModule, "moduleManager"):
    importedModule.moduleManager.createSubParser(subparsers)

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
