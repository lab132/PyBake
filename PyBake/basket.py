"""
The place to get your daily pastries!
"""

from PyBake import *
from os.path import expanduser
from importlib import import_module
from zipfile import ZipFile
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


def downloadPastries(menu, pastries, server):
  import requests
  newPastries = []
  for pastryData in pastries:
    pastry = PastryDesc(pastryData)
    if menu.exists(pastry):
      log.dev("Pastry already exists locally: {}".format(pastry))
      continue
    with LogBlock("Requesting {}".format(pastry)):
      response = requests.post("{}/get_pastry".format(server),
                               data=dict(pastry),
                               stream=True)
      if not response.ok:
        log.error("Request failed:\n{}".format(response.text))
        return

      size = 1024
      if "content-length" in response.headers:
        size = int(response.headers["content-length"])

      out_path = menu.makePath(pastry)
      log.info("Saving to: {}".format(out_path.as_posix()))

      with ByteProgressListener(maxSize=size) as progress:
        with out_path.open("wb") as out_file:
          chunk_size = 1024 * 4  # 4 KiB at a time.
          for chunk in response.iter_content(chunk_size):
            out_file.write(chunk)
            progress(chunk_size)
      menu.add(pastry)
      newPastries.append(pastryData)
      log.success("Pastry received.")
  return newPastries


def installPastries(menu, pastries):
  for pastryData in pastries:
    pastry = PastryDesc(pastryData)
    pastryDestination = pastryData.get("destination", pastryData.get("dest", None))
    pastryDestination = Path(pastryDestination)
    pastryDestination.safe_mkdir(parents=True)
    pastryPath = menu.makePath(pastry)
    with LogBlock("Installing Pastry"):
      log.info("{} => {}".format(pastryPath, pastryDestination))
      with ZipFile(pastryPath.as_posix()) as pastryFile:
        blackList = ("pastry.json", "ingredients.json")
        filteredFiles = [f for f in pastryFile.namelist() if f not in blackList]
        pastryFile.extractall(pastryDestination.as_posix(), members=filteredFiles)


class ByteProgressListener:
  """
  Takes care of logging some bytes progressing.

  Automatically abbreviates to the nearest multiple of 1024, i.e. will turn a `maxSize` of "4096" to "4 KiB".

  Usage example:
    with ByteProgressListener(50) as progress:
      for i in range(5):
        progress(10) # 10, 20, 30, 40, 50
  """

  template = "%s[%s%s] %i/%i {byteSuffix} - %s\r"

  def __init__(self, *, logInterface=log, maxSize, template=None):
    self.logInterface = logInterface
    self.maxSize = maxSize
    byteSuffixIndex = 0
    while maxSize > 1024:
      maxSize /= 1024
      byteSuffixIndex += 1
    self.maxSize = int(maxSize)
    self.byteSuffix = byteSuffixLookup[byteSuffixIndex]
    self.sizeFactor = 1024 * (byteSuffixIndex + 1)
    self.template = template or ByteProgressListener.template.format(byteSuffix=self.byteSuffix)
    self.currentSize = 0
    self.accu = 0

  def __enter__(self, *args):
    self.logInterface.start_progress(expectedSize=self.maxSize, barTemplate=self.template)
    self.currentSize = 0
    self.accu = 0
    return self

  def __exit__(self, *args):
    self.logInterface.set_progress(self.maxSize)
    self.logInterface.end_progress()
    self.currentSize = 0
    self.accu = 0

  def __call__(self, size):
    if self.currentSize == self.maxSize:
      return
    self.accu += size
    if self.accu >= self.sizeFactor:
      self.currentSize += self.accu / self.sizeFactor
      self.currentSize = min(self.currentSize, self.maxSize)
      self.accu = 0
      self.logInterface.set_progress(int(self.currentSize))


def run(*, location, shopping_list="shoppingList", **kwargs):
  """Gets pastries from the shop using the shopping list"""
  with LogBlock("Basket"):
    shopping_list = import_module(shopping_list)
    server = try_getattr(shopping_list, ("server_config", "server"), raise_error=True)
    pastries = try_getattr(shopping_list, ("pastries", "pastry"), raise_error=True)

    pastries_root = get_location_path(location) / Menu.defaultPastriesDirPath
    pastries_root.safe_mkdir(parents=True)
    menu = Menu(pastries_root)
    menu.load()
    newPastries = downloadPastries(menu, pastries, server)
    menu.save()
    installPastries(menu, pastries)
