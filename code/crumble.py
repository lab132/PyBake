
class CrumbleType:
    """Single Byte identifier for Crumbles"""

    Error=b"0"
    Success=b"1"

    PackageRequest=b"10"
    PackageFile=b"11"
    
    PackageUpload=b"20"
    
    PackageListingRequest=b"30"
    PackageListingResponse=b"31"

class Crumble(object):
    """Describes PyBake Network Protocol header meta-data"""

    def __init__(self, *, type):
        self.type = type
        self.contentLength = 0
        self.size = 1 + 4




