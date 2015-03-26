'''
Serving pastries to customers, fresh from the oven!
'''

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify

import json

from PyBake import Path
from PyBake.logger import log, LogBlock
from importlib import import_module

class Pastry:
  def __init__(self, name, version, file):
    self.name = name
    self.version = version
    self.file = file

  def as_path(self):
    print("name", self.name)
    print("version", self.version)
    return Path(self.name) / "{}.zip".format(self.version)
    #import base64
    #encoded_path = base64.urlsafe_b64encode("{0.name}_{0.version}".format(self).encode("UTF-8"))
    #return Path(encoded_path.decode("UTF-8"))


class ShopDiskDriver:

  pastries_root = Path("pastries")

  def __init__(self):
    # Make sure the pastries dir exists
    if not ShopDiskDriver.pastries_root.exists():
      ShopDiskDriver.pastries_root.mkdir(parents=True)
    ShopDiskDriver.pastries_root = ShopDiskDriver.pastries_root.resolve()
    log.info("Pastries dir: {}".format(ShopDiskDriver.pastries_root.as_posix()))

    self.menu_path = ShopDiskDriver.pastries_root / "menu.json"
    if not self.menu_path.exists():
      if not self.menu_path.parent.exists():
        self.menu_path.parent.mkdir(mode=0o700, parents=True)
      self.menu = {}
      self.sync_menu()
    else:
      with self.menu_path.open("r") as menu_file:
        self.menu = json.load(menu_file)

  def create_pastry(self, pastry):
    with LogBlock("Writing Disk"):
      pastry_path = ShopDiskDriver.pastries_root / pastry.as_path()
      if not pastry_path.parent.exists():
        pastry_path.parent.mkdir(parents=True)

      log.info("Pastry destination: {}".format(pastry_path.as_posix()))

      pastry.file.save(pastry_path.as_posix())
      self.add_to_menu(pastry)

  def add_to_menu(self, pastry):
    with LogBlock("Add To Menu"):
      log.info("Adding {0.name} with version {0.version} to menu.".format(pastry))
      # Get the menu entry for this pastry (name only) or a new list.
      known_versions = self.menu.get(pastry.name, {})
      if pastry.version not in known_versions:
        known_versions.update({ pastry.version : pastry.as_path().as_posix() })
      self.menu[pastry.name] = known_versions
      self.sync_menu()

  def sync_menu(self):
    with self.menu_path.open("w") as menu_file:
      log.info("Writing menu to disk")
      json.dump(self.menu, menu_file, indent=True, sort_keys=True)


class ShopBackend:
  def __init__(self, driver=ShopDiskDriver()):
    self.driver = driver

  def process_pastry(self, pastry_data, pastry_files):
    num_files = len(pastry_files)
    import zipfile
    with LogBlock("Backend Pastry Processing ({} files)".format(num_files)):
      for pastry_file in pastry_files:
        pastry = Pastry(pastry_data["name"][0],
                        pastry_data["version"][0],
                        pastry_file)
        self.driver.create_pastry(pastry)

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

    @app.route("/upload_pastry", methods=["POST"])
    def upload_pastry():
      with LogBlock("Upload"):
        log.debug("Recieved upload request")

        data = dict(request.form)
        log.debug("Data: {}".format(data))

        files = dict(request.files)
        log.debug("Files: {}".format(files))

        returnCode = 200
        errors = []
        response = {
          "result": "Ok"
        }

        if "name" not in data:
          errors.append("missing pastry 'name'")

        if "version" not in data:
          errors.append("missing pastry 'version'")

        if "pastry" not in files:
          errors.append("missing pastry file")

        if len(errors) == 0:
          errors = shopBackend.process_pastry(data, files["pastry"])

        if errors and len(errors) != 0:
          returnCode = 400
          response["errors"] = errors
          response["result"] = "Error"

        return jsonify(response), returnCode

    @app.route("/get_pastry", methods=["POST"])
    def get_pastry():
      pass

    return app


def run(*, config, **kwargs):
  app = Shop()

  shop_config = import_module(config)

  app.run(debug=True, host=shop_config.server.host, port=shop_config.server.port)
