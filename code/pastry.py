from struct import Struct

class Pastry:
    """Basic tastiness for everything that crumbles!"""

    # Set your own value in a subclass.
    layout = None

    def packedSize(self):
        return self.layout.size
