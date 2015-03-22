'''
Serving crumbles to customers, fresh from the oven!
'''

from flask import Flask, request, session, g, redirect, url_for, abort, \
  render_template, flash, jsonify

import json

from PyBake import Path
from importlib import import_module

class ShopDiskDriver:

  def __init__(self):
    self.menuPath = Path("crumbles/menu.json")
    if not self.menuPath.exists():
      if not self.menuPath.parent.exists():
        self.menuPath.parent.mkdir(mode=0o700, parents=True)
      #self.menuPath.open("w")
      self.menu = {}
      self.syncMenu()
    else:
      with self.menuPath.open("r") as menuFile:
        self.menu = json.load(menuFile)

  def saveCrumble(self, crumbleData, pastryJson):
    import base64
    file_name_string = base64.urlsafe_b64encode("{name}_{version}".format(**crumble))
    crumbleDir = Path("crumbles/{0}".format(file_name_string))
    if not crumbleDir.exists():
      crumbleDir.mkdir(mode=0o700, parents=True)
    pastryPath = crumbleDir / "pastry.json"

    with pastryPath.open("w") as pastryFile:
      pastryFile.write(pastryJson)

    self.addToMenu(crumbleData)

  def addToMenu(self, crumbleData):
    versionSet = self.menu.get(crumbleData["name"], set())
    versionSet.add(crumbleData["version"])
    self.menu[crumbleData["name"]] = versionSet
    self.syncMenu()

  def syncMenu(self):
    with self.menuPath.open("w") as menuFile:
      json.dump(self.menu, menuFile, indent=True, sort_keys=True)





class ShopBackend:

  def __init__(self, driver=ShopDiskDriver()):
    self.driver = driver

  def saveCrumble(self, crumbleData, pastryFile):
    self.driver.saveCrumble(crumbleData, pastryFile)

shopBackend = ShopBackend()


def Shop(name=__name__):

  # create our little application :)
  app = Flask(name)

  # Load default config and override config from an environment variable
  app.config.update(dict(
      DATABASE=(Path(app.root_path) / 'flaskr.db').as_posix(),
      DEBUG=True,
      SECRET_KEY='development key',
      USERNAME='admin',
      PASSWORD='default'
  ))
  app.config.from_envvar('FLASKR_SETTINGS', silent=True)

  @app.route("/upload_crumble")
  def upload_crumble():
    fileName = "pastry.json"

    if fileName in request.files and "crumbleName" in request.form and "crumbleVersion" in request.form:
      crumbleData = {
        "name" : request.form["crumbleName"],
        "version" : request.form["crumbleVersion"]
        }
      shopBackend.saveCrumble(crumbleData, request.files[fileName])


  @app.route("/get_crumble", methods=["POST"])
  def get_crumble():
    pass

  return app


def run(*, config, **kwargs):
  app = Shop()

  shop_config = import_module(config)

  app.run(debug=True, host=shop_config.server.host, port=shop_config.server.port)
