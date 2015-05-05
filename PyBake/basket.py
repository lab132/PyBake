"""
The place to get your daily pastries!
"""

from importlib import import_module
from zipfile import ZipFile
import json
from hashlib import sha1
import requests
from io import TextIOWrapper

# Variables.
from PyBake import dataDir, defaultPastriesDir, byteSuffixLookup
# Functions.
from PyBake import try_getattr, importFromFile, createFilename
# Classes.
from PyBake import Pastry, Path, Menu, PastryJSONEncoder
# Logging.
from PyBake.logger import log, LogBlock

def downloadPastry(menu, pastryData, server, *, forceDownload):
  pastryName = pastryData["name"]
  pastryVersionSpec = pastryData["version"]
  pastry = menu.get(pastryName, pastryVersionSpec)
  if forceDownload and pastry:
    log.info("Forcing re-download of already existing pastry: {}".format(pastry))
  if not forceDownload and pastry:
    log.dev("Skipping locally existing pastry: {}".format(pastry))
    return
  pastryRequestData = {"name": pastryName, "version": pastryVersionSpec}
  with LogBlock("Requesting {}".format(pastryRequestData)):
    response = requests.post("{}/get_pastry".format(server),
                             data=pastryRequestData,
                             stream=True)
    if not response.ok:
      log.error("Request failed:\n{}".format(response.text))
      return False

    size = 1024
    if "content-length" in response.headers:
      size = int(response.headers["content-length"])

    if "x-pastry-version" not in response.headers:
      log.error("Missing required http response header: X-Pastry-Version")
      return False

    pastryVersion = response.headers["x-pastry-version"]
    pastry = menu.add(Pastry(name=pastryName, version=pastryVersion))
    out_path = menu.makePath(pastry)
    log.info("Saving to: {}".format(out_path.as_posix()))

    with ByteProgressListener(maxSize=size) as progress:
      with out_path.open("wb") as out_file:
        chunk_size = 1024 * 4  # 4 KiB at a time.
        for chunk in response.iter_content(chunk_size):
          out_file.write(chunk)
          progress(chunk_size)
    log.success("Pastry received.")


def installPastry(menu, receipt, pastryData, server, *, forceDownload, forceInstall):
  def getDependencies(menu, pastry):
    with ZipFile(menu.makePath(pastry).as_posix()) as pastryFile:
      with pastryFile.open("pastry.json") as dataFile:
        pastryData = json.load(TextIOWrapper(dataFile, encoding="UTF-8"))
        return pastryData.get("dependencies", [])

  pastryName = pastryData["name"]
  pastryVersionSpec = pastryData["version"]
  callback = pastryData.get("callback", None)
  if callback:
    callback("pre-download", pastryData)
    pastryName = pastryData.get("forceDownload", pastryName)
    pastryVersionSpec = pastryData.get("forceInstall", pastryVersionSpec)
  pastry = menu.get(pastryName, pastryVersionSpec)
  if not pastry or forceDownload:
    downloadPastry(menu, pastryData, server, forceDownload=forceDownload)
    pastry = menu.get(pastryName, pastryVersionSpec)
    pastryData["pastry"] = pastry
    callback = pastryData.get("callback", None)
    if callback:
      callback("post-download", pastryData)
      forceInstall = pastryData.get("forceInstall", pastryName)
  assert pastry is not None, "Menu HAS to have a suitable pastry at this point!"
  # TODO check if we have a newer version at this point.
  installedPastry = receipt.get(pastry.name, pastry.version)
  callback = pastryData.get("callback", None)
  if callback:
    pastryData["pastry"] = installedPastry
    callback("pre-install", pastryData)
    forceInstall = pastryData.get("forceInstall", pastryName)
  if installedPastry:
    if not forceInstall:
      log.info("Pastry already installed: {}".format(installedPastry))
      return
    pastry = installedPastry
    log.info("Re-installing pastry: {}".format(pastry))
  else:
    log.info("Installing pastry: {}".format(pastry))
  pastryDestination = pastryData.get("destination", None)
  if not pastryDestination:
    pastryDestination = createFilename(pastry.name)
    pastryData["destination"] = pastryDestination
  pastryDestination = Path(pastryDestination)
  pastryDestination.safe_mkdir(parents=True)
  pastryDestination = pastryDestination.resolve()
  pastryPath = menu.makePath(pastry)
  for dep in getDependencies(menu, pastry):
    dep["destination"] = pastryDestination
    installPastry(menu, receipt, dep, server, forceDownload=forceDownload, forceInstall=forceInstall)
  log.info("{} => {}".format(pastryPath, pastryDestination))
  with ZipFile(pastryPath.as_posix()) as pastryFile:
    blackList = ("pastry.json", "ingredients.json")
    filteredFiles = [f for f in pastryFile.namelist() if f not in blackList]
    pastryFile.extractall(pastryDestination.as_posix(), members=filteredFiles)
  receipt.add(pastry)
  callback = pastryData.get("callback", None)
  if callback:
    pastryData["pastry"] = pastry
    callback("post-install", pastryData)


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


# The directory in which all receipts are stored by default.
defaultReceiptsDirPath = dataDir / "receipts"
defaultReceiptsDirPath.safe_mkdir(parents=True)

# The receipts database file.
defaultReceiptsDBPath = dataDir / "receipts.json"
if not defaultReceiptsDBPath.exists():
  with defaultReceiptsDBPath.open("w") as receiptsFile:
    json.dump({}, receiptsFile)


def getReceipt(shoppingListPath):
  """
  Creates a receipt from the shopping list path.
  """
  shoppingListPath = Path(shoppingListPath).resolve()
  log.debug("Getting receipt for shopping list: {}".format(shoppingListPath.as_posix()))
  projectPath = shoppingListPath.parent
  log.debug("Key for receipt: {}".format(projectPath.as_posix()))

  with defaultReceiptsDBPath.open("r") as receiptsDBFile:
    receiptsDB = json.load(receiptsDBFile)

  receipt = Receipt(key=projectPath.as_posix())
  log.debug("Using {}".format(repr(receipt)))

  # In case the receipt is new, we create it, add it to the database, and return.
  if receipt.key not in receiptsDB:
    log.debug("Adding nonexistant receipt.")
    receiptsDB[receipt.key] = receipt.hash
    log.debug("Saving receipts database.")
    with defaultReceiptsDBPath.open("w") as receiptsDBFile:
      json.dump(receiptsDB, receiptsDBFile, sort_keys=True, indent=2)
    return receipt

  # At this point, the receipt already exists.
  assert receipt.hash == receiptsDB[receipt.key], "Different hashes?!"
  return receipt


class Receipt(Menu):
  """
  Stores information about which pastries are installed.

  This is specific to each project.
  """

  def __init__(self, *, key, dirPath=None):
    self.key = key
    self.hash = sha1(str(self.key).encode("UTF-8")).hexdigest()
    filePath = Path(dirPath or defaultReceiptsDirPath) / "{}.json".format(self.hash)
    super().__init__(filePath)

  def __str__(self):
    return "{} => {}".format(self.key, self.filePath.as_posix())

  def __repr__(self):
    return "Receipt(key={}, hash={}, filePath={})".format(repr(self.key), repr(self.hash), repr(self.filePath))


def run(*, shoppingList="shoppingList.py", forceInstall=False, forceDownload=False, **kwargs):
  """Gets pastries from the shop using the shopping list"""
  with LogBlock("Basket"):
    shoppingListPath = shoppingList.resolve()
    shoppingList = importFromFile(shoppingListPath)

    callback = try_getattr(shoppingList, ["callback"])
    if callback:
      callback("pre-process", pastries)

    server = try_getattr(shoppingList, ("server_config", "server"), raise_error=True)
    pastries = try_getattr(shoppingList, ("pastries", "pastry"), raise_error=True)
    pastriesRoot = Path(try_getattr(shoppingList, ("pastriesRoot", "pastriesDir", "pastriesPath"), default_value=defaultPastriesDir))
    pastriesRoot.safe_mkdir(parents=True)

    with LogBlock("Load Menu"):
      menu = Menu(pastriesRoot)
      log.debug("Menu file path: {}".format(menu.filePath.as_posix()))
      menu.load()
    with LogBlock("Load Recipe"):
      receipt = getReceipt(shoppingListPath)
      log.debug("Receipt file path: {}".format(receipt.filePath.as_posix()))
      receipt.load()
    with LogBlock("Installing Pastries"):
      for pastry in pastries:
        installPastry(menu, receipt, pastry, server, forceInstall=forceInstall, forceDownload=forceDownload)
    receipt.save()
    menu.save()

    callback = try_getattr(shoppingList, ["callback"])
    if callback:
      callback("post-process", pastries)
