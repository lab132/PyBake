"""
This script assembles all ezEngine files on the current system and tags them appropriately.
The working directory when this script is executed is assumed to be the ezEngine root directory.
Use `PyBake oven` with this script to generate a pastry.
"""

from PyBake import *
from itertools import chain


def extract_platform(dirpath):
  """Parses a platform object from something like 'WinVs2013RelDeb32'."""
  name = dirpath.name

  p = Platform()

  # Platform name.
  i_name = 1
  while not name[i_name].isupper():
    i_name += 1
  p.name = name[:i_name]

  # Platform generator.
  i_gen = i_name + 1
  while not name[i_gen].isupper():
    i_gen += 1
  p.generator = name[i_name:i_gen]

  # Platform config
  i_cfg = i_gen + 1
  while not name[i_cfg].isdigit():
    i_cfg += 1
  p.config = name[i_gen:i_cfg]

  # Platform bits.
  p.bits = int(name[-2:])  # Last 2 characters are the bits

  print("Extracted platform: {0} => {1}".format(name, repr(p)))
  return p

# This is expected to be the ezEngine repo root.
root = Path(".")

# Path for all header files.
ezEnginePath_Headers = root / "Code" / "Engine"
ezEnginePath_Headers.resolve()

# Path for dll, pdb, and so files.
ezEnginePath_Bin = root / "Output" / "Bin"
ezEnginePath_Bin.resolve()

# Path for lib files.
ezEnginePath_Lib = root / "Output" / "Lib"
ezEnginePath_Lib.resolve()


@recipe
def get_header_files():
  """Find all header files."""
  print("Assemlbing 'header-file's")
  tags = {"header-file": None}
  for filename in ezEnginePath_Headers.rglob("*.h"):
    yield Ingredient(filename, tags=tags)


@recipe
def get_runtime_files():
  """Find all runtime-time files, such as .dll files."""
  print("Assemlbing 'rt-file's")
  bindir = ezEnginePath_Bin.glob("*")
  for subpath in bindir:
    if not subpath.is_dir() or subpath.match("*Test*"):
      continue
    tags = {"rt-file": None, "platform": extract_platform(subpath)}

    for filename in chain(subpath.rglob("ez*.dll"), subpath.rglob("ez*.pdb"), subpath.rglob("ez*.so")):
      yield Ingredient(filename, tags=tags)


@recipe
def get_compiletime_files():
  """Find all compile-time files, such as .lib files."""
  print("Assemlbing 'ct-file's")
  libdir = ezEnginePath_Lib.glob("*")
  for subpath in libdir:
    if not subpath.is_dir() or subpath.match("*Test*"):
      continue
    tags = {"ct-file": None, "platform": extract_platform(subpath)}

    for filename in subpath.rglob("ez*.lib"):
      yield Ingredient(filename, tags=tags)
