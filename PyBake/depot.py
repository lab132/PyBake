"""
Sending pastries generated from the oven to the shop.
"""

from PyBake import *
from PyBake.logger import *
from importlib import import_module
import zipfile
import requests

# Note: This function could run concurrently.
def uploadPastry(pastryPath, server):
  """
  Uploads a pastry to the server.
  """
  # Extract pastry.json data from the pastry package (pastry.zip),
  # and convert this data to a python dictionary, which we send to the server.
  with pastryPath.open("rb") as pastryFile:
    with zipfile.ZipFile(pastryFile) as zip_file:
      # Note: For some reason, json.load does not accept the result
      #       of ZipFile.open, so we use ZipFile.read instead to load
      #       the entire file as bytes, convert it to a string, and parse that.
      pastryBytes = zip_file.read("pastry.json")
      data = json.loads(pastryBytes.decode("UTF-8"))

  # Construct the `files` dictionary with the pastry package (.zip).
  files = {"pastry": pastryPath.open("rb")}

  postUrl = "{}/upload_pastry".format(server)
  log.info("Uploading...")
  log.dev("Sending data: {}".format(data))
  # Finally send the post request with some meta and file data.
  response = requests.post(postUrl, data=data, files=files)

  with LogBlock("Response"):
    log.dev("Status Code: {}".format(response.status_code))
    log.dev(response.json())

  if response.status_code == requests.codes.ok:
    log.success("Successful deposit.")
  else:
    log.error("Failed to upload pastry.")


def run(*, pastryPaths, config, **kwargs):
  """Deposit a pastry in a shop."""

  # Import the config script.
  log.debug("Importing config script '{}.py'".format(config))
  config = import_module(config)

  with LogBlock("Server: {}".format(config.server)):
    for pastryPath in pastryPaths:
      # Make sure the path exists.
      pastryPath = pastryPath.resolve()

      toUpload = None
      if pastryPath.is_dir():
        toUpload = pastryPath.iterdir()
      else:
        toUpload = (pastryPath,)
      for pastry in toUpload:
        # TODO Properly validate `pastry` to actually be a pastry?
        if pastry.suffix != ".zip":
          log.warning("Given file is not a pastry. Ignoring: {}".format(pastry.as_posix()))
          continue
        with LogBlock("Pastry Upload: {}".format(pastry.as_posix())):
          uploadPastry(pastry, config.server)
