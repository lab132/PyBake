"""
Generate a list of tagged files that will be combined to a crumble.
"""

import sys
from importlib import import_module
from PyBake import *

def run(workingDir, recipeScript, jsonTarget, indentOutput):
    # Make sure the recipeScript exists.
    recipePath = Path(recipeScript).resolve()

    # Remove the file extension.
    recipeScript = recipeScript.parent / recipeScript.stem

    # Make sure the working dir exists.
    workingDir = Path(workingDir).resolve()

    # Change into the working directory given by the user.
    with ChangeDir(workingDir):
        print("Processing recipe '{0}'".format(recipeScript))

        # Load the recipe, which will register some handlers that yield ingredients.
        recipe = import_module(recipeScript.as_posix())
        if len(recipes) == 0:
            print("No recipes found. Make sure to create functions and decorate them with @recipe.")
            return

        ingredients = []
        for rcp in recipes:
            ingredients.extend([ dict(ing) for ing in rcp() ])

        pastry = dict(
            name="???",
            version="v.0.1.whatever",
            ingredients=ingredients
        )

    # Write the JSON file (pastry.json by default).
    with jsonTarget.open("w") as outfile:
        json.dump(pastry, outfile, cls=Baker, indent=indentOutput)
