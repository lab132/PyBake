"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *

def pastry_to_json_file(out_file, name, version, ingredients, options):
  import json
  class BakersApprentice(json.JSONEncoder):
    def default(self, obj):
      if isinstance(obj, Platform):
        return dict(obj)
      if isinstance(obj, Ingredient):
        return dict(obj)
      return json.JSONEncoder.default(self, obj)

  # Create the pastry
  pastry = {}
  pastry["name"] = name
  pastry["version"] = version
  pastry["ingredients"] = ingredients

  indent_output = not (options.get("no_indent_output", False) if options is not None else False)
  sort_keys = options.get("sort_keys", True) if options is not None else True

  # Write the JSON file (pastry.json by default).
  with out_file.open("w") as out:
    json.dump(pastry, out, indent=indent_output, sort_keys=sort_keys, cls=BakersApprentice)

def run(*,                                  # Keyword arguments only.
        pastry_name,                        # The name of the pastry.
        pastry_version,                     # The version-string of the pastry.
        working_dir,                        # Working directory in which to look for and execute the `recipe`
        recipe,                             # The recipe to load, which provides ingredients.
        output,                             # The target file specified by the user, e.g. a JSON file. Relative to the original working dir.
        baker_function=pastry_to_json_file, # The function that finally processes the ingredients and creates a pastry. Expected signature: func(out_file, name, version, list_of_ingredients, options)
        **kwargs):                          # kwargs passed as `options` to the `baker_function`.
  # Make sure the working dir exists.
  working_dir = working_dir.resolve()

  # Change into the working directory given by the user.
  with ChangeDir(working_dir):
    Log.log("Processing recipe '{0}'".format(recipe))

    # Load the recipe, which will register some handlers that yield ingredients.
    import_module(recipe)
    if len(recipes) == 0:
      Log.error("No recipes found. Make sure to create functions and decorate them with @recipe.")
      return

    # Collect all ingredients
    ingredients = []
    for rcp in recipes:
      ingredients.extend(dict(ing) for ing in rcp())

  # Note: Do not call the pastry_writer from within the ChangeDir block above!
  baker_function(output, pastry_name, pastry_version, ingredients, kwargs)
