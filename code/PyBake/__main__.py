"""This module runs commands given by the user."""

# Make sure this module is executed, not imported.
if __name__ != '__main__':
    raise Error("This module is meant to be executed, not imported!")

import sys


commands = {}

def command(name):
    def helper(func):
        commands[name] = func
        return func
    return helper

@command("server")
def server():
    from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify
    # create our little application :)
    app = Flask(__name__)
    # Load default config and override config from an environment variable

    app.config.update(dict(
        DATABASE=os.path.join(app.root_path, 'flaskr.db'),
        DEBUG=True,
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default'
    ))
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

    @app.route("/list_packages")
    def listPackages():
        p = os.listdir(".")
        print(p)
        return jsonify({"values" : p})
    import crumble
    app.run(debug=True, host=crumble.server.host, port=crumble.server.port)

@command("client")
def client():
    import crumble
    response = json.load(urlopen("{0}/list_packages".format(crumble.server)))
    print(response)

@command("oven")
def execute_oven():
    recipeScript = "recipe.py" if len(sys.argv) == 2 else sys.argv[2]
    from PyBake import oven
    oven.run(recipeScript)

## Main
## ====

if len(sys.argv) == 1:
    print("Expected a command name as first argument.")
    sys.exit(-1)

commandName = sys.argv[1]
if not commandName in commands:
    print("Unknown command name: {}".format(commandName))
    sys.exit(1)

# Call the command
commands[commandName]()
