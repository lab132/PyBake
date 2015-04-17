"""
The place to get your daily pastries!
"""

from PyBake import *
from os.path import expanduser
from importlib import import_module


def get_location_path(loc):
  """Return a (resolved) path to the actual location on disk. `loc` must be one of {"local", "system", "user"}."""
  if loc == "system":
    assert False, "Not supported yet."
  lookup = {"local": Path.cwd(), "user": Path(expanduser("~"))}

  return lookup[loc]


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
    import requests

    shopping_list = import_module(shopping_list)
    server_config = try_getattr(shopping_list, ("server_config", "server"), raise_error=True)
    pastries = try_getattr(shopping_list, ("pastries", "pastry"), raise_error=True)

    pastries_root = get_location_path(location) / Menu.defaultPastriesDirPath
    pastries_root.safe_mkdir(parents=True)
    menu = Menu(pastries_root)
    menu.load()

    for pastry in pastries:
      if menu.exists(pastry):
        log.dev("Pastry already exists locally: {}".format(pastry))
        continue
      with LogBlock("Requesting {}".format(pastry)):
        response = requests.post("{}/get_pastry".format(server_config),
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
        log.success("Pastry received.")

    menu.save()
