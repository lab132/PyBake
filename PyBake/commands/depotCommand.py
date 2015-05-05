"""Creates argparse commands for the depot command
"""

from PyBake.commands import command
import textwrap
from PyBake import Path, log, LogBlock
from PyBake.depot import run

@command("depot")
class DepotModuleManager:
  """Module Manager for Depot"""

  longDescription = textwrap.dedent(
    """
    Uploads crumbles to the server given a pastry info file.
    """
  )

  def createArguments(self, depotParser):
    """Create the subparser and arguments for the depot command"""
    depotParser.add_argument("pastryPaths",
                             type=Path,
                             nargs="*",
                             default=[Path(".pastries")],
                             help="Path to the pastry directory. Must contain a valid 'menu.json' that describes "
                                  "the available packages. "
                                  "Default: .pastries")
    depotParser.add_argument("-c", "--config",
                             default=Path("config.py"),
                             dest="configPath",
                             type=Path,
                             help="Name of the python module containing configuration data. "
                                  "Default: config.py.")
    depotParser.add_argument("-f", "--force",
                             action="store_true",
                             help="Force the server to overwrite all exisitng pastries with the incoming ones.")
    depotParser.set_defaults(func=execute_depot)

def execute_depot(args):
  """Execute the `depot` command."""
  with LogBlock("Depot"):
    log.debug(args)
    return run(**vars(args))
