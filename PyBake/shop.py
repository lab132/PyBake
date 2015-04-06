"""
Serving pastries to customers, fresh from the oven!
"""

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify, send_from_directory

import json

from PyBake import Path, MenuBackend, MenuDiskDriver
from PyBake.logger import log, LogBlock
from importlib import import_module


def Shop(name=__name__):
  """Create the Fask application."""
  with LogBlock("Shop"):
    menuBackend = MenuBackend(driver=MenuDiskDriver())

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
      """Downloads a pastry from the client to the server."""
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
          # `data` is a multi-dict, which is why we need to extract it here.
          name = data["name"][0]
          version = data["version"][0]
          errors = menuBackend.process_pastry(name, version, files["pastry"])

        if errors and len(errors) != 0:
          returnCode = 400
          response["errors"] = errors
          response["result"] = "Error"

        return jsonify(response), returnCode

    @app.route("/get_pastry", methods=["POST"])
    def get_pastry():
      """Sends a pastry to the client."""
      with LogBlock("Get Pastry"):
        log.debug("Recieved download request")

        data = dict(request.form)
        log.debug("Data: {}".format(data))

        errors = []
        response = {
          "result": "Ok"
        }

        if "name" not in data:
          errors.append("missing pastry 'name'")

        if "version" not in data:
          errors.append("missing pastry 'version'")

        pastry_path = None
        if len(errors) == 0:
          # `data` is a multi-dict, which is why we need to extract it here.
          name = data["name"][0]
          version = data["version"][0]
          pastry_path = menuBackend.get_pastry(errors, name, version)

        if errors and len(errors) != 0:
          response["errors"] = errors
          response["result"] = "Error"
          return jsonify(response), 400
        log.info("Sending file: {}".format(pastry_path.as_posix()))
        return send_from_directory(pastry_path.parent.as_posix(), pastry_path.name)

    return app


def run(*, config, **kwargs):
  """Open the shop!"""
  app = Shop()

  shop_config = import_module(config)

  app.run(debug=True, host=shop_config.server.host, port=shop_config.server.port)
