"""The place to get your daily pastries!"""
from PyBake import *
from os.path import expanduser
from importlib import import_module

def get_location_path(loc):
  """Return a (resolved) path to the actual location on disk. `loc` must bei one of {"local", "system", "user"}."""
  if loc == "system":
    assert False, "Not supported yet."
  lookup = {"local" : Path.cwd(), "user" : Path(expanduser("~"))}

  return lookup[loc]

def progress_listener(max_size):
  max_size = max_size / (1024 * 1024)
  log.start_progress(max_size, bar_template="%s[%s%s] %i/%i MiB - %s\r")
  def on_progress(size):
    if size:
      log.set_progress(size / (1024 * 1024))
    else:
      log.set_progress(max_size)
      log.end_progress()
  return on_progress


def run(*, location, shopping_list="shoppingList", **kwargs):
  """Restocks pastries from the shop using the shopping list"""
  with LogBlock("Stock Exchange"):
    import requests

    shopping_list = import_module(shopping_list)
    server_config = try_getattr(shopping_list, ("server_config", "server"), raise_error=True)
    pastries = try_getattr(shopping_list, ("pastries", "pastry"), raise_error=True)

    pastries_root = get_location_path(location) / ".pastries"
    pastries_root.safe_mkdir(parents=True)

    for pastry in pastries:
      with LogBlock("Requesting {}".format(pastry)):
        response = requests.post("{}/get_pastry".format(server_config),
                                 data=pastry.server_data(),
                                 stream=True)
        if response.status_code != requests.codes.ok:
          log.error("Request failed:\n{}".format(response.text))
          return

        size = 1024
        if "content-length" in response.headers:
          size = int(response.headers["content-length"])

        out_path = pastries_root / pastry.path()
        log.info("Saving to: {}".format(out_path.as_posix()))

        listener = progress_listener(size)

        with out_path.open("wb") as out_file:
          chunk_size = 1024 * 4 # 4 KiB at a time.
          bytes_written = 0
          for chunk in response.iter_content(chunk_size):
            out_file.write(chunk)
            bytes_written += chunk_size
            listener(bytes_written)
        listener(None)
        log.success("Pastry received.")
