from PyBake import *

local = ServerConfig("http://127.0.0.1:1337")
server_config = local

pastries = [
  Pastry.from_dict({
    "name" : "ezEngine",
    "version" : "milestone-6",
    "location" : "thirdParty/ezEngine"
  })
]
