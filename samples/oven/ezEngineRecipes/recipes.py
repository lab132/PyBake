"""
Assemble all ezEngine files on the current system and pack them into different pastries.
The working directory when this script is executed is assumed to be the ezEngine root directory.
Use `PyBake oven` with this script to generate a series of pastries (.zip files).
"""

from PyBake import *
from itertools import chain

pastryVersion = Version("0.6.0")

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
def get_header_files(pot):
  """Get all header files."""
  master = pot.get("ezEngine", pastryVersion)
  master.addDependency("ezEngine_Headers", pastryVersion)
  pastry = pot.get("ezEngine_Headers", pastryVersion)
  add_common(pastry)
  for ingredient in ezEnginePath_Headers.rglob("*.h"):
    pastry.addIngredient(ingredient)


@recipe
def get_runtime_files(pot):
  """Get all runtime files."""
  master = pot.get("ezEngine", pastryVersion)
  for path in ezEnginePath_Bin.glob("*"):
    if not path.is_dir() or path.match("*Test*"):
      continue
    platform = extract_platform(path)
    name = createFilename("ezEngine_Bin", platform)
    master.addDependency(name, pastryVersion)
    pastry = pot.get(name, pastryVersion)
    add_common(pastry)
    for ingredient in chain(path.rglob("ez*.dll"), path.rglob("ez*.pdb"), path.rglob("ez*.so")):
      pastry.addIngredient(ingredient)


@recipe
def get_compiletime_files(pot):
  """Get all compile-time files."""
  master = pot.get("ezEngine", pastryVersion)
  for path in ezEnginePath_Lib.glob("*"):
    if not path.is_dir() or path.match("*Test*"):
      continue
    platform = extract_platform(path)
    name = createFilename("ezEngine_Lib", platform)
    master.addDependency(name, pastryVersion)
    pastry = pot.get(name, pastryVersion)
    add_common(pastry)
    pastry.addIngredient("exports_{name}{bits}{generator}.cmake".format(**vars(platform)))
    for ingredient in path.rglob("ez*.lib"):
      pastry.addIngredient(ingredient)


def add_common(pastry):
  """
  Add common ingredients to a pastry.
  """
  pastry.addIngredient("README.md")
  pastry.addIngredient("License.txt")
  for ingredient in root.glob("*.cmake"):
    pastry.addIngredient(ingredient)
