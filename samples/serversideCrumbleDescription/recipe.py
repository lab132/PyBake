# This script is used to attach tags to files.
from PyBake import *

# [Required] Will contain all tagged files.
ingredients = []

def extract_platform(path):
    """Parses a platform object from something like 'WinVs2013RelDeb32'."""
    name = path.name

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
    p.bits = int(name[-2:]) # Last 2 characters are the bits

    print("Extracted platform: {0} => {1}".format(name, repr(p)))
    return p


ezEngineRoot = Path(".").resolve()

# Path for all header files.
ezEnginePath_Headers = ezEngineRoot / "Code" / "Engine"
ezEnginePath_Headers.resolve()

# Path for dll, pdb, and so files.
ezEnginePath_Bin     = ezEngineRoot / "Output" / "Bin"
ezEnginePath_Bin.resolve()

# Path for lib files.
ezEnginePath_Lib     = ezEngineRoot / "Output" / "Lib"
ezEnginePath_Lib.resolve()

print("headers")
tags = [ "header-file" ]
files = ezEnginePath_Headers.rglob("*.h")
ingredients.extend([ Ingredient(h.relative_to(ezEngineRoot), tags=["header-file"]) for h in files ])


print("runtime_files")
tags = [ "rt-file" ]
path = ezEnginePath_Bin.glob("*")
for subpath in path:
    if not subpath.is_dir() or subpath.match("*Tests"):
        continue
    files = []
    p = extract_platform(subpath)

    files.extend(subpath.rglob("ez*.dll"))
    files.extend(subpath.rglob("ez*.pdb"))
    files.extend(subpath.rglob("ez*.so"))
    ingredients.extend([ Ingredient(x.relative_to(ezEngineRoot), platform=p, tags=tags) for x in files ])


print("compiletime_files")
tags = [ "ct-file" ]
path = ezEnginePath_Lib.glob("*")
for subpath in path:
    if not subpath.is_dir():
        continue
    files = []
    p = extract_platform(subpath)

    files.extend(subpath.rglob("ez*.lib"))
    ingredients.extend([ Ingredient(x.relative_to(ezEngineRoot), platform=p, tags=tags) for x in files ])

@regger
def foo():
    print("+++ bar +++")

print("__ done __")
