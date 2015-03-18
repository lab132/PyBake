"""
Generate a list of tagged files that will be combined to a crumble.
"""

import sys
from importlib import import_module
print(sys.path)
from PyBake import *

def run(recipeScript):
    # Remove extension
    recipeScript = Path(recipeScript).stem
    print("Importing {0}".format(recipeScript))
    recipe = import_module(recipeScript)
    print("something.")
    pastry = json.dumps(recipe.ingredients, cls=Baker, indent=True)
    print("Pastry: {0}".format(pastry))
