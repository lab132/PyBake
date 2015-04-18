"""
The place to get your daily pastries!
"""

from importlib import import_module
from zipfile import ZipFile

from PyBake import PastryDesc, log, LogBlock, Path, try_getattr, Menu, defaultPastriesDir, byteSuffixLookup


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


def run(*, shopping_list="shoppingList", **kwargs):
  """Gets pastries from the shop using the shopping list"""
  with LogBlock("Basket"):
    shopping_list = import_module(shopping_list)
    server = try_getattr(shopping_list, ("server_config", "server"), raise_error=True)
    allPastries = try_getattr(shopping_list, ("pastries", "pastry"), raise_error=True)
    cleanInstall = bool(try_getattr(shopping_list, ("cleanInstall", "clean"), default_value=False))
    pastriesRoot = Path(try_getattr(shopping_list, ("pastriesRoot", "pastriesDir", "pastriesPath"), default_value=defaultPastriesDir))
    pastriesRoot.safe_mkdir(parents=True)

    menu = Menu(pastriesRoot)
    log.debug("Menu file path: {}".format(menu.filePath.as_posix()))

    menu.load()

    with LogBlock("Downloading Pastries"):
      newPastries = downloadPastries(menu, allPastries, server)

    menu.save()

    with LogBlock("Installing Pastries"):
      installPastries(menu, newPastries if not cleanInstall else allPastries)
