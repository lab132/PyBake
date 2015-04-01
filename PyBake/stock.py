"""The place to get your daily pastries!"""
from PyBake import *

def run(*, shopping_list=Path("shoppingList.json"), **kwargs):
  """Restocks pastries from the shop using the shopping list"""
  with LogBlock("Stock Exchange"):
    import requests

    shoppingList = ShoppingList.FromJSON(shopping_list.open("r").read())

    for pastry in shoppingList.pastries:
      response = requests.post("{}/get_pastry".format(shoppingList.serverConfig), data=data, stream=True)
      log.info(response)
      with Path("ezEngine_milestone-6.zip").open("wb") as out_file:
        chunk_size = 1024 * 4 # 4 KiB at a time.
        for chunk in response.iter_content(chunk_size):
          out_file.write(chunk)
