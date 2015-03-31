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

if __name__ == "__main__":
  raise RuntimeError("__init__.py is not supposed to be executed!")

version = {
  "Release" : 0,
  "Major" : 0,
  "Minor" : 1,
}

recipes = []

def recipe(func):
  recipes.append(func)
  return func


class ServerConfig:
  """docstring"""
  def __init__(self, *, host, port=1337, protocol="http"):
    self.host = host
    self.port = port
    self.protocol = protocol

  @staticmethod
  def FromString(string):
    """Creates a server configuration from a given <protocol>://<address>:<port> string"""

    with LogBlock("ServerConfig From String"):
      import re
      # Ported from https://gist.github.com/dperini/729294
      # Re-enabled local ip addresses
      urlMatch=(r"^"
      # protocol identifier
      r"(?:(?P<protocol>https?)://)"
      # user:pass authentication
      r"(?:(?P<user>\S+)(?::(?P<password>\S*))?@)?"
      r"(?P<address>"
      # IP address exclusion
      # private & local networks
      #"(?!(?:10|127)(?:\.\d{1,3}){3})"
      #"(?!(?:169\\.254|192\.168)(?:\.\d{1,3}){2})"
      #"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
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
      if port is not None:
        port = int(port)
        log.info("Port is {}".format(port))
      else:
        log.info("No port given in url")
      return ServerConfig(host=matchDict["address"], port=port, protocol=matchDict.get("protocol", "http"))

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
  def __init__(self, path, *, tags={}):
    self.path = path
    self.tags = tags

  def __str__(self):
    return "{0.path.name}".format(self)

  def __repr__(self):
    return "Ingredient({}{})".format(repr(self.path), repr(self.tags))

  def __iter__(self):
    yield ("path", self.path.as_posix(),)
    yield ("tags", self.tags,)

  def make_relative_to(self, root):
    if self.path.is_absolute():
      self.path = self.path.relative_to(root)

import json
class PastryJSONEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Platform):
      return dict(obj)
    if isinstance(obj, Ingredient):
      return dict(obj)
    return json.JSONEncoder.default(self, obj)

Path = pathlib.Path


class ChangeDir:
  """
  Change the current directory. The previous directory will be restored when
  Usage:
    with ChangeDir('some/dir'):
      pass
  """
  def __init__(self, path):
    self.previous = Path.cwd()
    try:
      self.current = Path(path).resolve()
      assert self.current.is_dir()
    except FileNotFoundError as ex:
      log.error("Cannot change into directory:")
      log.error(ex)
      self.current = self.previous

  def __enter__(self):
    self.enter()

  def __exit__(self, type, value, traceback):
    self.exit()

  def enter(self):
    import os
    os.chdir(self.current.as_posix())

  def exit(self):
    import os
    os.chdir(self.previous.as_posix())

class Pastry:
  def __init__(self, name, version, file):
    self.name = name
    self.version = version
    self.file = file

  def as_path(self):
    print("name", self.name)
    print("version", self.version)
    return Path(self.name) / "{}.zip".format(self.version)
    #import base64
    #encoded_path = base64.urlsafe_b64encode("{0.name}_{0.version}".format(self).encode("UTF-8"))
    #return Path(encoded_path.decode("UTF-8"))


class MenuDiskDriver:

  pastries_root = Path("pastries")

  def __init__(self):
    log.debug("Creating menu disk driver.")
    # Make sure the pastries dir exists
    if not MenuDiskDriver.pastries_root.exists():
      MenuDiskDriver.pastries_root.mkdir(parents=True)
    MenuDiskDriver.pastries_root = MenuDiskDriver.pastries_root.resolve()
    log.info("Pastries dir: {}".format(MenuDiskDriver.pastries_root.as_posix()))

    self.menu_path = MenuDiskDriver.pastries_root / "menu.json"
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
      pastry_path = MenuDiskDriver.pastries_root / pastry.as_path()
      if not pastry_path.parent.exists():
        pastry_path.parent.mkdir(parents=True)

      log.info("Pastry destination: {}".format(pastry_path.as_posix()))

      pastry.file.save(pastry_path.as_posix())
      self.add_to_menu(pastry)

  def has_pastry(self, *, name, version, **kwargs):
    """Checks if the menu contains a given pastry"""
    log.info("menu: {}".format(self.menu))
    return name in self.menu and version in self.menu[name]

  def get_pastry(self, errors, name, version):
    """Fetches a readable object of the pastry from the disk if it exists otherwise returns None."""
    with LogBlock("Get Pastry"):
      if self.has_pastry(name=name, version=version):
        log.info("Found pastry {} with version {} at {}".format(name,version,self.menu[name][version]))
        return MenuDiskDriver.pastries_root / self.menu[name][version]
      else:
        err = "Could not find pastry '{}' with version '{}'".format(name,version)
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
        known_versions.update({ pastry.version : pastry.as_path().as_posix() })
      self.menu[pastry.name] = known_versions
      self.sync_menu()

  def sync_menu(self):
    """Syncs the menu to the file system"""
    with self.menu_path.open("w") as menu_file:
      log.info("Writing menu to disk")
      json.dump(self.menu, menu_file, indent=True, sort_keys=True)


class MenuBackend:
  def __init__(self, driver=MenuDiskDriver()):
    log.debug("Creating menu backend.")
    self.driver = driver

  def process_pastry(self, pastry_name, pastry_version, pastry_files):
    num_files = len(pastry_files)
    import zipfile
    with LogBlock("Backend Pastry Processing {} File(s)".format(num_files)):
      for pastry_file in pastry_files:
        pastry = Pastry(pastry_name,
                        pastry_version,
                        pastry_file)
        self.driver.create_pastry(pastry)

  def get_pastry(self, errors, pastry_name, pastry_version):
    """Gets a pastry from the menu, if it exists"""
    log.info("pastry_data: {0} version {1}".format(pastry_name, pastry_version))
    return self.driver.get_pastry(errors, pastry_name, pastry_version)
