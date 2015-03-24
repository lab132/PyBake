"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *
import json

class JSONBakersApprentice(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Platform):
      return dict(obj)
    if isinstance(obj, Ingredient):
      return dict(obj)
    return json.JSONEncoder.default(self, obj)

class JSONBaker:
  def __init__(self, filepath, pastry_name, pastry_version, options, *args, **kwargs):
    super(JSONBaker, self).__init__(*args, **kwargs)
    self.filepath = filepath
    self.pastry_name = pastry_name
    self.pastry_version = pastry_version
    self.options = options or {}
    self.ingredients = []

  def process(self, ingredient):
    self.ingredients.append(ingredient)

  def done(self):
    # Create pastry meta info
    pastry = {}
    pastry["name"] = self.pastry_name
    pastry["version"] = self.pastry_version
    pastry["ingredients"] = self.ingredients

    indent_output = not self.options.get("no_indent_output", False)
    sort_keys = self.options.get("sort_keys", True)

    with self.filepath.open("w") as output:
      json.dump(pastry, output, indent=indent_output, sort_keys=sort_keys, cls=JSONBakersApprentice)

def run(*,                     # Keyword arguments only.
        pastry_name,           # The name of the pastry.
        pastry_version,        # The version-string of the pastry.
        working_dir,           # Working directory in which to look for and execute the `recipe`
        recipe,                # The recipe to load, which provides ingredients.
        output,                # The target file specified by the user, e.g. a JSON file. Relative to the original working dir.
        baker_class=JSONBaker, # Processes ingredients and creates a pastry.
        **kwargs):             # kwargs passed as `options` to the `baker_function`.
  with LogBlock("Oven"):
    # Make sure the working dir exists.
    working_dir = working_dir.resolve()

    # Change into the working directory given by the user.
    with ChangeDir(working_dir):
      log.info("Processing recipe '{0}'".format(recipe))

      # Load the recipe, which will register some handlers that yield ingredients.
      import_module(recipe)
      if len(recipes) == 0:
        log.error("No recipes found. Make sure to create functions and decorate them with @recipe.")
        return

      baker = baker_class(output, pastry_name, pastry_version, kwargs)
      for rcp in recipes:
        for ing in rcp():
          baker.process(ing)

    # Note: Do not call the baker.done() from within the ChangeDir block above!
    baker.done()
