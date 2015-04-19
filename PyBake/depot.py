"""
Sending pastries generated from the oven to the shop.
"""

from PyBake import *
from PyBake.logger import *
from importlib import import_module
import textwrap
import zipfile
import requests



# Note: This function could run concurrently.
def uploadPastry(menu, pastry, server):
  """
  Uploads a pastry to the server.
  """
  pastryPath = menu.makePath(pastry)
  # Extract pastry.json data from the pastry package (pastry.zip),
  # to validate the pastry.
  with pastryPath.open("rb") as pastryFile:
    with zipfile.ZipFile(pastryFile) as zip_file:
      # Note: For some reason, json.load does not accept the result
      #       of ZipFile.open, so we use ZipFile.read instead to load
      #       the entire file as bytes, convert it to a string, and parse that.
      pastryBytes = zip_file.read("pastry.json")
      zippedPastry = Pastry(data=json.loads(pastryBytes.decode("UTF-8")))

  if zippedPastry != pastry:
    log.error("")
    return

  # Construct the `files` dictionary with the pastry package (.zip).
  files = {"pastry": pastryPath.open("rb")}

  postUrl = "{}/upload_pastry".format(server)
  with LogBlock("Uploading {}".format(pastry)):
    log.info("Sending data...")
    # Send the post request with some meta data and the actual file data.
    response = requests.post(postUrl, data=dict(pastry), files=files)

    log.dev("Status: {}\n{}".format(response.status_code, response.text))
    if response.ok:
      log.success("Successful deposit.")
    else:
      log.error("Failed to upload pastry.")


def importConfigScript(configPath):
  with ChangeDir(configPath.parent):
    if configPath.suffix == ".py":
      config = configPath.parent / configPath.stem
    return import_module(config.name)



def run(*, pastryPaths, configPath, **kwargs):
  """Deposit a pastry in a shop."""

  # Make sure the config file exists.
  configPath = configPath.resolve()

  # Import the config script.
  log.debug("Importing config script: {}".format(configPath.as_posix()))
  config = importConfigScript(configPath)
  server = try_getattr(config, ("server", "serverConfig"), raise_error=True)

  with LogBlock("Server: {}".format(server)):
    for pastryPath in pastryPaths:
      pastryPath.safe_mkdir(parents=True)
      menu = Menu(pastryPath)
      menu.load()
      for pastry in menu.registry:
        uploadPastry(menu, pastry, server)
