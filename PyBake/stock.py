"""The place to get your daily pastries!"""
from PyBake import *
from os.path import expanduser

def get_location_path(loc):
  """Return a (resolved) path to the actual location on disk. `loc` must bei one of {"local", "system", "user"}."""
  if loc == "system":
    assert False, "Not supported yet."
  lookup = {"local" : Path.cwd(), "user" : Path(expanduser("~"))}

  return lookup[loc]


def run(*, location, shopping_list=Path("shoppingList.json"), **kwargs):
  """Restocks pastries from the shop using the shopping list"""
  with LogBlock("Stock Exchange"):
    import requests

    shoppingList = ShoppingList.FromJSONFile(shopping_list)

    pastries_root = get_location_path(location) / ".pastries"
    safe_mkdir(pastries_root, parents=True)
    #menu = MenuBackend(driver=MenuDiskDriver())

    for pastry in shoppingList.pastries:
      with LogBlock("Requesting {}".format(pastry)):
        response = requests.post("{}/get_pastry".format(shoppingList.serverConfig),
                                 data=pastry.server_data(),
                                 stream=True)
        if response.status_code != requests.codes.ok:
          log.error("Request failed:\n{}".format(response.text))
          return
        log.success("Pastry received.")
        out_path = pastries_root / "{}.zip".format(pastry.path().as_posix())
        log.info("Saving to: {}".format(out_path.as_posix()))
        with out_path.open("wb") as out_file:
          chunk_size = 1024 * 4 # 4 KiB at a time.
          for chunk in response.iter_content(chunk_size):
            out_file.write(chunk)
