"""
Serving pastries to customers, fresh from the oven!
"""

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify, send_from_directory

import json

from PyBake import Path, Menu, Pastry, try_getattr, defaultPastriesDir
from PyBake.logger import log, LogBlock, ScopedLogSink
from importlib import import_module
import textwrap


def processPastryUpload(menu, pastryDesc, pastryFile):
  with LogBlock("Processing Pastry Upload: {}".format(pastryDesc)):
    if menu.exists(pastryDesc):
      log.info("Pastry already exists. Ignoring.")
      return
    # Get the target path on the local system for the pastry.
    pastryPath = menu.makePath(pastryDesc)
    log.info("Saving pastry to: {}".format(pastryPath.as_posix()))
    # Try saving the pastry.
    pastryFile.save(pastryPath.as_posix())
    # Add that pastry to the menu.
    menu.add(pastryDesc)
    # Make sure the menu database is up to date.
    menu.save()


def getPastryFilePath(menu, pastryDesc):
  with LogBlock("Finding Pastry File Path"):
    if menu.exists(pastryDesc):
      return menu.makePath(pastryDesc)
    log.error("Pastry not found.")


def Shop(*, menu, name=__name__):
  """Create the Fask application."""
  with LogBlock("Creating Shop Instance"):
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
          with ScopedLogSink() as sink:
            processPastryUpload(menu, Pastry(name=name, version=version), files["pastry"][0])
            errors.extend(sink.logged["error"])

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
          pastryDesc = Pastry(name=data["name"][0],
                                  version=data["version"][0])
          with ScopedLogSink() as sink:
            pastry_path = getPastryFilePath(menu, pastryDesc)
            errors.extend(sink.logged["error"])

        if errors and len(errors) != 0:
          print("errors:", errors)
          response["errors"] = errors
          response["result"] = "Error"
          return jsonify(response), 400
        log.info("Sending file: {}".format(pastry_path.as_posix()))
        return send_from_directory(pastry_path.parent.as_posix(), pastry_path.name)

    return app


def run(*, config, **kwargs):
  """Open the shop!"""
  with LogBlock("Shop"):
    shop_config = import_module(config)

    pastriesRoot = try_getattr(shop_config,
                               ("pastriesRoot", "pastriesDir", "pastriesPath"),
                               default_value=defaultPastriesDir)
    pastriesRoot = Path(pastriesRoot)
    pastriesRoot.safe_mkdir(parents=True)

    debug = try_getattr(shop_config, ("debug", "debugEnabled"), default_value=False)

    menu = Menu(pastriesRoot)
    log.info("Full menu file path: {}".format(menu.filePath.as_posix()))
    menu.load()
    app = Shop(menu=menu)
    app.run(debug=debug, host=shop_config.server.host, port=shop_config.server.port)
    menu.save()
