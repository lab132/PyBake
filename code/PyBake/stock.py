"""The place to get your daily pastries!"""
from PyBake import *

def run(**kwargs):
  with LogBlock("Stock Exchange"):
    import requests

    import config

    data = dict(name="ezEngine",
                version="milestone-6")

    response = requests.post("{}/get_pastry".format(config.server), data=data, stream=True)
    log.info(response)
    with Path("ezEngine_milestone-6.zip").open("wb") as out_file:
      chunk_size = 1024 * 4 # 4 KiB at a time.
      for chunk in response.iter_content(chunk_size):
        out_file.write(chunk)
