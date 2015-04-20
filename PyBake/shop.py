"""
Serving pastries to customers, fresh from the oven!
"""

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify, send_from_directory, make_response

import json

from PyBake import Path, Menu, Pastry, try_getattr, defaultPastriesDir
from PyBake.logger import log, LogBlock, ScopedLogSink
from importlib import import_module
import textwrap


def processPastryUpload(menu, pastry, pastryFile):
  log.info("Pastry: {}".format(pastry))
  existing = menu.get(pastry.name, pastry.version)
  if existing:
    log.info("Pastry already exists. Ignoring.")
    return
  # Get the target path on the local system for the pastry.
  pastryPath = menu.makePath(pastry)
  log.info("Saving pastry to: {}".format(pastryPath.as_posix()))
  # Try saving the pastry.
  pastryFile.save(pastryPath.as_posix())
  # Add that pastry to the menu.
  menu.add(pastry)
  print("+++++++++++ saving menu")
  # Make sure the menu database is up to date.
  menu.save()


def getPastry(menu, pastryName, pastryVersionSpec):
  with LogBlock("Finding Pastry {} with version spec {}".format(pastryName, pastryVersionSpec)):
    pastry = menu.get(pastryName, pastryVersionSpec)
    if not pastry:
      log.error("Pastry not found.")
      return
    log.dev("Pastry '{}' found at: {}".format(pastry, menu.makePath(pastry).as_posix()))
    return pastry


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
            pastry = Pastry(name=name, version=version)
            with LogBlock("Processing Pastry Upload: {}".format(pastry)):
              processPastryUpload(menu, pastry, files["pastry"][0])
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

        pastryPath = None
        if len(errors) == 0:
          # `data` is a multi-dict, which is why we need to extract it here.
          name = data["name"][0]
          version = data["version"][0]
          with ScopedLogSink() as sink:
            pastry = getPastry(menu, name, version)
            if pastry:
              pastryPath = menu.makePath(pastry)
            errors.extend(sink.logged["error"])

        if errors and len(errors) != 0:
          response["errors"] = errors
          response["result"] = "Error"
          return jsonify(response), 400
        log.info("Sending file: {}".format(pastryPath.as_posix()))
        response = make_response(send_from_directory(pastryPath.parent.as_posix(), pastryPath.name))
        response.headers["X-Pastry-Version"] = str(pastry.version)
        return response

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
