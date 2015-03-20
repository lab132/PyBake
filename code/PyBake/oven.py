"""
Generate a list of tagged files that will be combined to a crumble.
"""

import sys
from importlib import import_module
from PyBake import *

def run(*, working_dir, recipe, output, indent_output, **kwargs):
    # Make sure the recipe exists.
    recipePath = recipe.resolve()

    # Remove the file extension.
    recipe = recipe.parent / recipe.stem

    # Make sure the working dir exists.
    working_dir = working_dir.resolve()

    # Change into the working directory given by the user.
    with ChangeDir(working_dir):
        print("Processing recipe '{0}'".format(recipe))

        # Load the recipe, which will register some handlers that yield ingredients.
        recipe = import_module(recipe.as_posix())
        if len(recipes) == 0:
            print("No recipes found. Make sure to create functions and decorate them with @recipe.")
            return

        ingredients = []
        for rcp in recipes:
            ingredients.extend(dict(ing) for ing in rcp())

        pastry = dict(
            name="???",
            version="v.0.1.whatever",
            ingredients=ingredients
        )

    # Write the JSON file (pastry.json by default).
    with output.open("w") as outfile:
        json.dump(pastry, outfile, cls=Baker, indent=indent_output)
