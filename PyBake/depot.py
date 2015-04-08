"""
Sending pastries generated from the oven to the shop.
"""

from PyBake import *
from PyBake.logger import *
from importlib import import_module
import textwrap

class DepotModuleManager:
  """Module Manager for Depot"""

  longDescription = textwrap.dedent(
  """
  Uploads crumbles to the server given a pastry info file.
  """
  )

  def createSubParser(self, subParsers):
    """Create the subparser and arguments for the depot command"""

    depotParser = subParsers.add_parser("depot", help=self.longDescription, description=self.longDescription)

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


def execute_depot(args):
  """Execute the `depot` command."""
  with LogBlock("Depot"):
    log.debug(args)
    return depot.run(**vars(args))


moduleManager = DepotModuleManager()

def run(*, pastry_path, config, **kwargs):
  """Deposit a pastry in a shop."""
  import requests

  # Import the config script.
  log.debug("Importing config script '{}.py'".format(config))
  config = import_module(config)

  # Make sure the path exists.
  pastry_path = pastry_path.resolve()
  log.debug("Pastry path: {}".format(pastry_path.as_posix()))
  log.debug("Pastry name: {}".format(pastry_path.name))
  if pastry_path.is_dir():
    log.error("Expected given pastry to be a file, but is a directory!")
    return

  import zipfile

  # Extract pastry.json data from the pastry package (pastry.zip),
  # and convert this data to a python dictionary, which we send to the server.
  with pastry_path.open("rb") as pastry_file:
    with zipfile.ZipFile(pastry_file) as zip_file:
      # Note: For some reason, json.load does not accept the result
      #       of ZipFile.open, so we use ZipFile.read instead to load
      #       the entire file as bytes, convert it to a string, and parse that.
      pastry_bytes = zip_file.read("pastry.json")
      data = json.loads(pastry_bytes.decode("UTF-8"))

  # Construct the `files` dictionary with the pastry package (.zip).
  files = {"pastry": pastry_path.open("rb")}

  postUrl = "{}/upload_pastry".format(config.server)
  log.info("Placing deposit with {}...".format(postUrl))
  log.dev("Sending data: {}".format(data))
  # Finally send the post request with some meta and file data.
  response = requests.post(postUrl, data=data, files=files)

  with LogBlock("Response"):
    log.dev("Status Code: {}".format(response.status_code))
    log.dev(response.json())

  if response.status_code == requests.codes.ok:
    log.success("Successful deposit.")
