"""
The place to get your daily pastries!
"""

from PyBake import *
from os.path import expanduser
from importlib import import_module
import textwrap

class BasketModuleManager:
  """Module Manager for Basket"""

  longDescription = textwrap.dedent(
  """
  Retrieves pastries from the shop.
  """)

  def createSubParser(self, subparsers):
    basketParser = subparsers.add_parser("basket", help=self.longDescription, description=self.longDescription)

    basketParser.add_argument("shopping_list",
                              nargs="?",
                              default="shoppingList",
                              help="Sets the used shoppingList (defaults to 'shoppingList') which will be reused"
                              "to retrieve pastries from the shop.")
    basketParser.add_argument("-l", "--location",
                              default="user",
                              choices=["local", "user", "system"],
                              help="Where to save the pastries to.")
    basketParser.set_defaults(func=execute_basket)

moduleManager = BasketModuleManager()

def execute_basket(args):
  """Execute the `basket` command."""
  log.debug(args)
  from PyBake import basket
  return basket.run(**vars(args))



def get_location_path(loc):
  """Return a (resolved) path to the actual location on disk. `loc` must be one of {"local", "system", "user"}."""
  if loc == "system":
    assert False, "Not supported yet."
  lookup = {"local": Path.cwd(), "user": Path(expanduser("~"))}

  return lookup[loc]


class ProgressListener:
  """
  Takes care of logging some progress.

  Usage example:
    with ProgressListener(50) as progress:
      for i in range(5):
        progress(10)
  """

  def __init__(self, *, logInterface=log, maxSize):
    self.logInterface = logInterface
    self.maxSize = maxSize

  def __enter__(self, *args):
    self.logInterface.start_progress(self.maxSize)
    return self

  def __exit__(self, *args):
    self.logInterface.set_progress(self.maxSize)
    self.logInterface.end_progress()

  def __call__(self, size):
    self.logInterface.set_progress(size)


def run(*, location, shopping_list="shoppingList", **kwargs):
  """Gets pastries from the shop using the shopping list"""
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
                                 data=pastry.shop_data(),
                                 stream=True)
        if response.status_code != requests.codes.ok:
          log.error("Request failed:\n{}".format(response.text))
          return

        size = 1024
        if "content-length" in response.headers:
          size = int(response.headers["content-length"])

        out_path = pastries_root / pastry.path()
        log.info("Saving to: {}".format(out_path.as_posix()))

        with ProgressListener(maxSize=size) as progress:
          with out_path.open("wb") as out_file:
            chunk_size = 1024 * 4  # 4 KiB at a time.
            bytes_written = 0
            for chunk in response.iter_content(chunk_size):
              out_file.write(chunk)
              bytes_written += chunk_size
              progress(bytes_written)
        log.success("Pastry received.")
