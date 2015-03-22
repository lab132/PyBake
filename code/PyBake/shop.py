'''
Serving crumbles to customers, fresh from the oven!
'''

from flask import Flask, request, session, g, redirect, url_for, abort, \
  render_template, flash, jsonify

import json

from PyBake import Path
from PyBake.logger import log, LogBlock
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
    with LogBlock("Shop Disk"):
      import base64
      file_name_string = base64.urlsafe_b64encode(bytes("{name}_{version}".format(**crumbleData), "UTF-8"))
      crumbleDir = Path("crumbles/{0}".format(file_name_string))
      log.info("Working on path {0}".format(crumbleDir.as_posix()))
      if not crumbleDir.exists():
        log.info("Path is missing.... creating")
        crumbleDir.mkdir(mode=0o700, parents=True)
      pastryPath = crumbleDir / "pastry.json"

      with pastryPath.open("w") as pastryFile:
        log.info("Writing pastry.json with {0} chars".format(len(pastryJson)))
        pastryFile.write(pastryJson)

      self.addToMenu(crumbleData)

  def addToMenu(self, crumbleData):
    with LogBlock("Add To Menu"):
      log.info("Adding {name} with version {version} to menu".format(**crumbleData))
      versionSet = self.menu.get(crumbleData["name"], [])
      if not crumbleData["version"] in versionSet:
        versionSet.append(crumbleData["version"])
      self.menu[crumbleData["name"]] = versionSet
      self.syncMenu()

  def syncMenu(self):
    with self.menuPath.open("w") as menuFile:
      log.info("Writing menu to disk")
      json.dump(self.menu, menuFile, indent=True, sort_keys=True)





class ShopBackend:

  def __init__(self, driver=ShopDiskDriver()):
    self.driver = driver

  def saveCrumble(self, crumbleData, pastryFile):
    with LogBlock("Backend Crumble Save"):
      log.debug("Saving crumble with pastryFile of length {0}".format(len(pastryFile)))
      self.driver.saveCrumble(crumbleData, pastryFile)

shopBackend = ShopBackend()


def Shop(name=__name__):
  with LogBlock("Shop"):
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

    @app.route("/upload_crumble", methods=["POST"])
    def upload_crumble():
      with LogBlock("Upload"):
        log.debug("Recieved upload request")
        log.debug(request.form)
        log.debug(request.files)
        fileName = "pastry.json"

        returnCode = 200
        errors = []
        data = {
          "result" : "Ok"
          }

        if fileName not in request.files:
          errors.append("missing pastry.json")

        if "crumbleName" not in request.form:
          errors.append("missing crumbleName")


        if "crumbleVersion" not in request.form:
          errors.append("missing crumbleVersion")

        if len(errors) == 0:
          crumbleData = {
            "name" : request.form["crumbleName"],
            "version" : request.form["crumbleVersion"]
            }
          shopBackend.saveCrumble(crumbleData, request.files[fileName].read().decode("UTF-8"))
        else:
          returnCode = 400
          data["errors"] = errors
          data["result"] = "Error"

        return jsonify(data), returnCode


    @app.route("/get_crumble", methods=["POST"])
    def get_crumble():
      pass

    return app


def run(*, config, **kwargs):
  app = Shop()

  shop_config = import_module(config)

  app.run(debug=True, host=shop_config.server.host, port=shop_config.server.port)
