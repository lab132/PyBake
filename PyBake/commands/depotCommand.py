"""Creates argparse commands for the depot command
"""

from PyBake.commands import command
import textwrap
from PyBake import Path
from PyBake.depot import execute_depot

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