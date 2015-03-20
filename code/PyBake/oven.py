"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *

def run(*, pastry_name, pastry_version, working_dir, recipe, output, indent_output, **kwargs):
  # Make sure the working dir exists.
  working_dir = working_dir.resolve()

  # Prepare the pastry.
  pastry = {}

  # Change into the working directory given by the user.
  with ChangeDir(working_dir):
    print("Processing recipe '{0}'".format(recipe))

    # Load the recipe, which will register some handlers that yield ingredients.
    import_module(recipe)
    if len(recipes) == 0:
      print("No recipes found. Make sure to create functions and decorate them with @recipe.")
      return

    # Collect all ingredients
    ingredients = []
    for rcp in recipes:
      ingredients.extend(dict(ing) for ing in rcp())

  # Create the pastry
  pastry["name"] = pastry_name
  pastry["version"] = pastry_version
  pastry["ingredients"] = ingredients

  # Write the JSON file (pastry.json by default).
  with output.open("w") as outfile:
    json.dump(pastry, outfile, cls=Baker, indent=indent_output, sort_keys=True)
