from PyBake import *
from PyBake.logger import *
from importlib import import_module

def upload_generator(pastry_name, pastry_file, ingredients):
  # First, send the pastry file.
  yield (pastry_name, pastry_file,)

  # Then, iterate all ingredients, sending them one after another.
  for ingredient in ingredients:
    path = Path(ingredient["path"]).resolve().relative_to(Path.cwd())
    log.info("Uploading {}...".format(path.as_posix()))
    yield (path.as_posix(), path.open("rb"),)

def run(*, pastry_path, config, **kwargs):
  import requests, json

  # Import the config script.
  log.debug("Importing config script '{}'".format(config))
  config = import_module(config)

  # Make sure the path exists.
  pastry_path = pastry_path.resolve()
  log.debug("Pastry path: {}".format(pastry_path.as_posix()))
  log.debug("Pastry name: {}".format(pastry_path.name))
  if pastry_path.is_dir():
    log.error("Expected given pastry to be a file, but is a directory!")
    return

  with ChangeDir(pastry_path.parent):
    log.dev("Loading pastry from '{}'...".format(pastry_path.as_posix()))
    with pastry_path.open("r") as pastry_file:
      pastry = json.load(pastry_file)
      data = { "name"    : pastry["name"],
               "version" : pastry["version"],
               "pastry_file_name"  : pastry_path.name, }
      files = upload_generator(pastry_path.name, pastry_file, pastry["ingredients"])
      postUrl = "{}/upload_crumble".format(config.server)
      log.info("Posting to {}...".format(postUrl))
      response = requests.post(postUrl, data=data, files=files)
      if response.status_code == requests.codes.ok:
        log.success("Successful deposit.")

  with LogBlock("Response"):
    log.dev("Status Code: {}".format(response.status_code))
    log.dev(response.json())
