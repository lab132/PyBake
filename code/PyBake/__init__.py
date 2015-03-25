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
    return "{0.path.name} for {0.platform}".format(self)

  def __repr__(self):
    return "Ingredient({}{}{})".format(repr(self.path), repr(self.platform), repr(self.tags))

  def __iter__(self):
    yield ("path", self.path.as_posix(),)
    yield ("tags", self.tags,)

  def make_relative_to(self, root):
    if self.path.is_absolute():
      self.path = self.path.relative_to(root)

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
