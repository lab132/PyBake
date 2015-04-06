'''
Baking py since 2015
'''
import socket
import importlib
from urllib.request import urlopen
import pathlib
from copy import deepcopy
from importlib import import_module
from PyBake.logger import log, LogBlock
from werkzeug.utils import secure_filename
from os import path
import re
import json

if __name__ == "__main__":
  raise RuntimeError("__init__.py is not supposed to be executed!")

here = path.abspath(path.dirname(__file__))

version = {
  "Major": 0,
  "Minor": 0,
  "Patch": 0,
}

with open(path.join(here, "VERSION"), encoding="UTF-8") as f:
  versionString = f.read().strip()
  versionMatch = re.search(r"(?P<Major>\d+)\.(?P<Minor>\d+)\.(?P<Patch>\d+)", versionString)
  if versionMatch:
    for key in version:
      version[key] = int(versionMatch.group(key))


def try_getattr(obj, choices, default_value=None, raise_error=False):
  """
  Try `getattr` on `obj`, querying for everything in `choices`,
  which may also be only a single value.

  If `raise_error` is `True`, and no attributes could be found,
  an AttributeError is raised. Otherwise `default_value` is returned.
  """
  for attr in choices:
    try:
      return getattr(obj, attr)
    except AttributeError:
      continue
  if raise_error:
    raise AttributeError("Unable to find attribute with any of these names: {}".format(choices))
  return default_value


recipes = []


def recipe(func):
  """
  Decorator function used to collect all recipes for the `oven` command within a given user script.
  """
  recipes.append(func)
  return func


class ServerConfig:
  """Helper class that stores server configuration infos."""

  port_lookup = {
    "http": 80,
    "https": 443
  }

  def __init__(self, host_str=None, *, host=None, port=None, protocol="http"):
    if host_str:
      self.fromString(host_str)
    else:
      self.host = host
      self.protocol = protocol
      self.port = port or ServerConfig.port_lookup[self.protocol]

  def fromString(self, string):
    """Creates a server configuration from a given <protocol>://<address>:<port> string"""

    with LogBlock("ServerConfig From String"):
      # Ported from https://gist.github.com/dperini/729294
      # Re-enabled local ip addresses
      urlMatch = (r"^"
                  # protocol identifier
                  r"(?:(?P<protocol>https?)://)"
                  # user:pass authentication
                  r"(?:(?P<user>\S+)(?::(?P<password>\S*))?@)?"
                  r"(?P<address>"
                  # IP address exclusion
                  # private & local networks
                  # "(?!(?:10|127)(?:\.\d{1,3}){3})"
                  # "(?!(?:169\\.254|192\.168)(?:\.\d{1,3}){2})"
                  # "(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
                  # IP address dotted notation octets
                  # excludes network & broacast addresses
                  # (first & last IP address of each class)
                  r"(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-5])"
                  r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
                  r"(?:\.(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
                  r"|"
                  # host name
                  r"(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)"
                  # domain name
                  r"(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*"
                  # TLD identifier
                  r"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
                  r")"
                  # port number
                  r"(?::(?P<port>\d{2,5}))?"
                  # resource path
                  r"(?P<resource_path>/\S*)?"
                  r"$")
      match = re.match(urlMatch, string)
      if match is None:
        log.error("Could not match given string as an url")
        return None
      log.info(match)
      matchDict = match.groupdict()
      port = matchDict.get("port", None)
      protocol = matchDict.get("protocol", "default")
      if port is not None:
        port = int(port)
      elif protocol in ServerConfig.port_lookup:
        log.info("No port given in url, using default from protocol.")
        port = ServerConfig.port_lookup[protocol]

      log.info("Port is {}".format(port))
      self.host = matchDict["address"]
      self.port = port
      self.protocol = protocol

  def __str__(self):
    return "{}://{}:{}".format(self.protocol, self.host, self.port)

  def __repr__(self):
    return "ServerConfig({})".format(self)


class Platform:
  """Object describing a platform such as 'Windows 64 bit VisualStudio2013 Debug'."""

  def __init__(self, *, name=None, detailed_name=None, bits=64, generator=None, config="Debug", user_data=None):
    self.name = name
    self.detailed_name = detailed_name
    self.bits = bits
    self.generator = generator
    self.config = config
    self.user_data = user_data

  def isValid(self):
    """A platform is valid if it has either a `name` or a `detailed_name`."""
    return self.name is not None or self.detailed_name is not None

  def __str__(self):
    if self.detailed_name is not None:
      return self.detailed_name
    return "Platform '{}'".format(self.name)

  def __repr__(self):
    return "<{0.name} ({0.detailed_name}) {0.bits} bit {0.generator} {0.config}: {0.user_data}>".format(self)

  def __iter__(self):
    yield ("name", self.name,)
    yield ("detailed_name", self.detailed_name,)
    yield ("bits", self.bits,)
    yield ("generator", self.generator,)
    yield ("config", self.config,)
    yield ("user_data", str(self.user_data),)

  # Represents all platforms.
  All = None  # Is initialized after the declaration of this class

  @staticmethod
  def FromDict(desc):
    """Extracts data from a dictionary and instanciates a `Platform` instance from that."""
    result = Platform()
    result.name = desc.get("name", result.name)
    result.detailed_name = desc.get("detailed_name", result.detailed_name)
    result.bits = desc.get("bits", result.bits)
    result.generator = desc.get("generator", result.generator)
    result.config = desc.get("config", result.config)
    result.user_data = desc.get("user_data", result.user_data)
    return result

Platform.All = Platform(name="all")


class Ingredient:
  """A wrapper for an existing file that has tags attached to it."""

  def __init__(self, ingredient_path, *, tags={}):
    self.path = ingredient_path
    self.tags = tags

  def __str__(self):
    return "{0.path.name}".format(self)

  def __repr__(self):
    return "Ingredient({}{})".format(repr(self.path), repr(self.tags))

  def __iter__(self):
    yield ("path", self.path.as_posix(),)
    yield ("tags", self.tags,)

  def make_relative_to(self, root):
    """Makes the path of the ingredient relative to `root`. `root` must be an absolute path."""
    if self.path.is_absolute():
      self.path = self.path.relative_to(root)


class PastryJSONEncoder(json.JSONEncoder):
  """JSON Encoder that can handle PyBake classes."""

  def default(self, obj):
    """Called in the process of serializing python data structures to JSON."""
    if isinstance(obj, Platform):
      return dict(obj)
    if isinstance(obj, Ingredient):
      return dict(obj)
    return json.JSONEncoder.default(self, obj)


Path = pathlib.Path


def safe_mkdir(self, **kwargs):
  """Like `Path.mkdir`, except it is allowed to call this on an existing path."""
  if not self.exists():
    self.mkdir(**kwargs)
setattr(Path, "safe_mkdir", safe_mkdir)


class ChangeDir:
  """
  Change the current directory. The previous directory will be restored when
  Usage:
    with ChangeDir('some/dir'):
      pass
  """

  def __init__(self, target_path):
    self.previous = Path.cwd()
    try:
      self.current = Path(target_path).resolve()
      assert self.current.is_dir()
    except FileNotFoundError as ex:
      log.error("Cannot change into directory:")
      log.error(ex)
      self.current = self.previous

  def __enter__(self):
    self.enter()

  def __exit__(self, theType, value, traceback):
    self.exit()

  def enter(self):
    """Enter the given directory. Should not be called manually, use `with` instead."""
    import os
    os.chdir(self.current.as_posix())

  def exit(self):
    """Exit the given directory. Should not be called manually, use `with` instead."""
    import os
    os.chdir(self.previous.as_posix())


class Pastry:
  """Describes a pastry (a package)."""

  def __init__(self, name, pastry_version, file):
    self.name = name
    self.version = pastry_version
    self.file = file

  def path(self):
    """Return the path of this pastry."""
    return Path(secure_filename("{}/{}.zip".format(self.name, self.version)))

  def shop_data(self):
    """Returns a dictionary containing all relevent data the shop (server) needs."""
    return dict(name=self.name, version=self.version)

  def __str__(self):
    return "{} version {}".format(self.name, self.version)

  def __repr__(self):
    return "Pastry(name={}, version={})".format(self.name, self.version)

  @staticmethod
  def from_dict(desc):
    """Extract data from a dictionary and instanciate a `Pastry` instance from that."""
    return Pastry(name=desc["name"], pastry_version=desc["version"], file=None)


class ShoppingList:
  """Describes the shop and the pastries needed for rebasketing."""

  def __init__(self):
    """Creates a default localhost config with no pastries"""
    self.serverConfig = ServerConfig(host="127.0.0.1")
    self.pastries = []

  @staticmethod
  def FromJSONFile(json_path):
    """Reads the shoppingList from a given json string"""
    with LogBlock("ShoppingList From Json"):
      with json_path.open("r") as json_file:
        data = json.load(json_file)

      if "shop" not in data:
        log.error("No shop specified in the shoppingList!")
        return None
      if "pastries" not in data:
        log.error("No pastries specified in the shoppingList!")
        return None

      shoppingList = ShoppingList()
      shoppingList.serverConfig = ServerConfig(data["shop"])

      for pastryDesc in data["pastries"]:
        shoppingList.pastries.append(Pastry.from_dict(pastryDesc))
      return shoppingList


class MenuDiskDriver:
  """Menu handling on a harddisk drive, as opposed to a database or a remote connection."""

  pastries_root = Path(".pastries")

  def __init__(self, pastries_root=pastries_root):
    log.debug("Creating menu disk driver.")
    # Make sure the pastries dir exists
    self.pastries_root.safe_mkdir(parents=True)
    self.pastries_root = self.pastries_root.resolve()
    log.info("Pastries root: {}".format(self.pastries_root.as_posix()))

    self.menu_path = self.pastries_root / "menu.json"
    if not self.menu_path.exists():
      if not self.menu_path.parent.exists():
        self.menu_path.parent.mkdir(mode=0o700, parents=True)
      self.menu = {}
      self.sync_menu()
    else:
      with self.menu_path.open("r") as menu_file:
        self.menu = json.load(menu_file)

  def create_pastry(self, pastry):
    """Writes the given pastry to the disk"""
    with LogBlock("Writing Disk"):
      pastry_path = self.pastries_root / pastry.path()
      if not pastry_path.parent.exists():
        pastry_path.parent.mkdir(parents=True)

      log.info("Pastry destination: {}".format(pastry_path.as_posix()))

      pastry.file.save(pastry_path.as_posix())
      self.add_to_menu(pastry)

  def has_pastry(self, *, name, pastry_version, **kwargs):
    """Checks if the menu contains a given pastry"""
    log.info("menu: {}".format(self.menu))
    return name in self.menu and pastry_version in self.menu[name]

  def get_pastry(self, errors, name, pastry_version):
    """Fetches a readable object of the pastry from the disk if it exists otherwise returns None."""
    with LogBlock("Get Pastry"):
      if self.has_pastry(name=name, pastry_version=pastry_version):
        log.info("Found pastry {} with version {} at {}".format(name, pastry_version, self.menu[name][pastry_version]))
        return self.pastries_root / self.menu[name][pastry_version]
      else:
        err = "Could not find pastry '{}' with version '{}'".format(name, pastry_version)
        log.error(err)
        errors.append(err)
        return None

  def add_to_menu(self, pastry):
    """Adds a new pastry to the menu"""
    with LogBlock("Add To Menu"):
      log.info("Adding {0.name} with version {0.version} to menu.".format(pastry))
      # Get the menu entry for this pastry (name only) or a new list.
      known_versions = self.menu.get(pastry.name, {})
      if pastry.version not in known_versions:
        known_versions.update({pastry.version: pastry.path().as_posix()})
      self.menu[pastry.name] = known_versions
      self.sync_menu()

  def sync_menu(self):
    """Syncs the menu to the file system"""
    with self.menu_path.open("w") as menu_file:
      log.info("Writing menu to disk")
      json.dump(self.menu, menu_file, indent=True, sort_keys=True)


class MenuBackend:
  """Manages locally available pastries."""

  def __init__(self, driver):
    log.debug("Creating menu backend.")
    assert driver, "Need valid Menu driver instance."
    self.driver = driver

  def process_pastry(self, pastry_name, pastry_version, pastry_files):
    """Process a pastry with the set driver."""
    num_files = len(pastry_files)
    with LogBlock("Backend Pastry Processing {} File(s)".format(num_files)):
      for pastry_file in pastry_files:
        pastry = Pastry(name=pastry_name,
                        pastry_version=pastry_version,
                        file=pastry_file)
        self.driver.create_pastry(pastry)

  def get_pastry(self, errors, pastry_name, pastry_version):
    """Gets a pastry from the menu, if it exists"""
    log.info("pastry_data: {0} version {1}".format(pastry_name, pastry_version))
    return self.driver.get_pastry(errors, pastry_name, pastry_version)