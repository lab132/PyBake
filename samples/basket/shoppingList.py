"""
Shopping list sample that only requires the ezEngine.
"""

from PyBake import *

local = ServerConfig("http://127.0.0.1:1337")
server_config = local

pastries = [
  {
    "name" : "ezEngine",
    "version" : ">=0.6.0",
    "destination" : "thirdParty/ezEngine"
  },
]
