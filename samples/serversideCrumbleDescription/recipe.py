# Generates the pastry.json.
from PyBake import *

tagRoutes = {
    "headers" : "Code/Engine",
    "runtime-binaries" : "Output/{operatingSystem}{bits}{generator}{config}/Bin/*.(dll|pdb)",
    "compile-binaries" : "Output/{operatingSystem}{bits}{generator}{config}/Lib/*.lib",
}

moduleNames = [
    "ezFoundation", "ezCore"
]

@packageTag("headers")
def getHeaderFiles():
    return [ "Code/Engine/{0}".format(x) for x in Path("Code/Engine/").iter_dir() ]

def getFiles(tag, platform, modules=None):
    if modules is None:
        modules = moduleNames

    if tag == "headers":
        return Path(tagRoutes["headers"])

