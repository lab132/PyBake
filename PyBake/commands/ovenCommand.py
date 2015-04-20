"""Command generation for oven"""

from PyBake.commands import command
from PyBake import Path, log, zipCompressionLookup
import textwrap

@command("oven")
class OvenModuleManager:
  """Manager class for the oven, registering the argparse commands"""
  # OvenParser
  # ==========

  longDescription = textwrap.dedent(
  """
  Tool to create crumbles.
  """)

  def createArguments(self, ovenParser):
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
    ovenParser.add_argument("-f", "--force",
                            action="store_true",
                            help="Ignore already existing pastries in the target output dir.")
    ovenParser.add_argument("-c", "--compression",
                            choices=zipCompressionLookup.keys(),
                            default="deflated",
                            help="The compression method used to create a pastry.")
    ovenParser.set_defaults(func=execute_oven)

def execute_oven(args):
  """Execute the `oven` command."""
  from PyBake import log
  log.info("Executing oven")
  from PyBake import oven
  args.compression = zipCompressionLookup[args.compression]
  return oven.run(**vars(args))
