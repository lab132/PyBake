"""
Assemble all ezEngine files on the current system and pack them into different pastries.
The working directory when this script is executed is assumed to be the ezEngine root directory.
Use `PyBake oven` with this script to generate a series of pastries (.zip files).
"""

from PyBake import *
from itertools import chain

pastry_version = "milestone-6"

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


def extract_platform(path):
  """Parses a platform object from something like 'WinVs2013RelDeb32'."""
  name = path.name

  platform = Platform()

  # Platform name.
  i_name = 1
  while not name[i_name].isupper():
    i_name += 1
  platform.name = name[:i_name]

  # Platform generator.
  i_gen = i_name + 1
  while not name[i_gen].isupper():
    i_gen += 1
  platform.generator = name[i_name:i_gen]

  # Platform config
  i_cfg = i_gen + 1
  while not name[i_cfg].isdigit():
    i_cfg += 1
  platform.config = name[i_gen:i_cfg]

  # Platform bits.
  platform.bits = int(name[-2:]) # Last 2 characters are the bits

  return platform


@recipe
def get_header_files(pots):
  pot = pots.get("ezEngine_Headers", pastry_version)
  for ingredient in ezEnginePath_Headers.rglob("*.h"):
    pot.append(ingredient)


@recipe
def get_runtime_files(pots):
  path = ezEnginePath_Bin.glob("*")
  for subpath in path:
    if not subpath.is_dir() or subpath.match("*Test*"):
      continue
    platform = extract_platform(subpath)
    pastryName = createFilename("ezEngine_Bin", platform)
    pot = pots.get(pastryName, pastry_version)
    for ingredient in chain(subpath.rglob("ez*.dll"), subpath.rglob("ez*.pdb"), subpath.rglob("ez*.so")):
      pot.append(ingredient)


@recipe
def get_compiletime_files(pots):
  path = ezEnginePath_Lib.glob("*")
  for subpath in path:
    if not subpath.is_dir() or subpath.match("*Test*"):
      continue
    platform = extract_platform(subpath)
    pastryName = createFilename("ezEngine_Lib", platform)
    pot = pots.get(pastryName, pastry_version)
    for ingredient in subpath.rglob("ez*.lib"):
      pot.append(ingredient)
