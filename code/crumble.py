from struct import Struct
from utils import *
from pastry import Pastry

class CrumbleType(Pastry):
    """Single Byte identifier for Crumbles"""

    layout = Struct(">B")

    ## Enum Values
    ## ===========

    Error = CrumbleType(0)
    Success = CrumbleType(1)

    PackageRequest = CrumbleType(10)
    PackageFile = CrumbleType(11)

    PackageUpload = CrumbleType(20)
    
    PackageListingRequest = CrumbleType(30)
    PackageListingResponse = CrumbleType(31)


    def __init__(self, value):
        self.value = value

    def pack(self):
        return layout(self.value)

class Crumble(Pastry):
    """Describes PyBake Network Protocol header meta-data"""
    layout = Struct(">BI")

    def __init__(self, *, type):
        self.type = type
        self.contentLength = 0

    def pack(self):
        if self.contentLength == 0:
            raise RuntimeError("Crumble has no content.")
        return layout(self.type, self.contentLength)
