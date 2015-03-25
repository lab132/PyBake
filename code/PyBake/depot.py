from PyBake import *
from PyBake.logger import *
from importlib import import_module

def run(*, pastry_path, config, **kwargs):
  import requests, json

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
  files = { "pastry" : pastry_path.open("rb") }

  postUrl = "{}/upload_crumble".format(config.server)
  log.info("Placing deposit with {}...".format(postUrl))
  log.dev("Sending data: {}".format(data))
  # Finally send the post request with some meta and file data.
  response = requests.post(postUrl, data=data, files=files)

  with LogBlock("Response"):
    log.dev("Status Code: {}".format(response.status_code))
    log.dev(response.json())

  if response.status_code == requests.codes.ok:
    log.success("Successful deposit.")
