"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *
import json
import zipfile
import textwrap

class OvenModuleManager:
  """Manager class for the oven, registering the argparse commands"""
  # OvenParser
  # ==========

  longDescription = textwrap.dedent(
  """
  Tool to create crumbles.
  """)

  def createSubParser(self, subParsers):
    ovenParser = subParsers.add_parser("oven", help=self.longDescription, description=self.longDescription)

    ovenParser.add_argument("recipes_script",
                            type=Path,
                            nargs="?",
                            default=Path("recipes.py"),
                            help="Path to the recipes script. Default: 'recipes.py'")
    ovenParser.add_argument("-o", "--output", type=Path, default=Path(".pastries"),
                            help="The directory to store the pastries in. Defaults to '.pastries'.")
    ovenParser.add_argument("-d", "--working-dir",
                            type=Path,
                            nargs="?",
                            default=Path.cwd(),
                            help="The working directory when executing the `recipes_script`. Defaults to the current working dir.")
    ovenParser.add_argument("-c", "--compression",
                            choices=zipCompressionLookup.keys(),
                            default="deflated",
                            help="The compression method used to create a pastry.")
    ovenParser.set_defaults(func=execute_oven)

moduleManager = OvenModuleManager()



def execute_oven(args):
  """Execute the `oven` command."""
  log.info("Executing oven")
  from PyBake import oven
  args.compression = zipCompressionLookup[args.compression]
  return oven.run(**vars(args))

class Pot:
  """Manages new pastries when processing recipes."""

  def __init__(self):
    self.ingredients = {}

  def get(self, name, version):
    """Get a pastry matching the given name and version."""
    assert name is not None, "`name` must not be None!"
    assert version is not None, "`version` must not be None!"
    key = (name, version)
    listOfIngredients = self.ingredients.get(key, None)
    if listOfIngredients is None:
      log.debug("Creating new entry in pot: {}".format(key))
      listOfIngredients = []
      self.ingredients[key] = listOfIngredients
    return listOfIngredients


def writePastryJson(zipFile, pastry):
  """Helper function of `zipBaker` that writes a pastry.json file to the given `zipFile`."""
  log.info("Writing pastry.json...")
  pastryJSON = json.dumps(pastry, indent=2, sort_keys=True, cls=PastryJSONEncoder)
  zipFile.writestr("pastry.json", bytes(pastryJSON, "UTF-8"))


def writeIngredientsJson(zipFile, ingredients):
  """Helper function of `zipBaker` that writes an ingredients.json file to the given `zipFile`."""
  log.info("Writing ingredients.json...")
  ingredientsJSON = json.dumps(ingredients, indent=2, sort_keys=True, cls=PastryJSONEncoder)
  zipFile.writestr("ingredients.json", bytes(ingredientsJSON, "UTF-8"))


def zipIngredients(zipFile, ingredients):
  """Helper function of `zipBaker` that adds all files in `ingredients` to the `zipFile`"""
  log.info("Zipping ingredients...")
  for ingredient in ingredients:
    path = Path(ingredient).as_posix()
    log.debug(path)
    zipFile.write(path)


def zipBaker(*, menu, pot, options):
  """Processes ingredients in a pot and creates pastries from that."""
  with LogBlock("Baking Pastries (Zip)"):
    for key, ingredients in pot.ingredients.items():
      pastry = PastryDesc(name=key[0], version=key[1])
      if menu.add(pastry) is False:
        continue
      with LogBlock("Pastry: {} with {} ingredients".format(pastry, len(ingredients))):
        zipFilePath = menu.makePath(pastry)
        with zipfile.ZipFile(zipFilePath.as_posix(), "w", compression=options["compression"]) as zipFile:
          writePastryJson(zipFile, pastry)
          writeIngredientsJson(zipFile, ingredients)
          zipIngredients(zipFile, ingredients)

        log.success("Done baking pastry: {}".format(zipFilePath.as_posix()))


def run(*,                   # Keyword arguments only.
        recipes_script,      # Path to the recipes script.
        working_dir,         # Working directory when executing the recipes script.
        output,              # Directory that will contain all resulting pastries.
        bakerFunc=zipBaker,  # Processes ingredients and creates a pastry.
        **kwargs):           # kwargs passed as `options` to the `bakerFunc`.
  """Run the oven command."""
  with LogBlock("Oven"):
    # Make sure the working dir exists.
    working_dir = working_dir.resolve()

    # Create an empty pot.
    pot = Pot()

    # Change into the working directory given by the user.
    with ChangeDir(working_dir):
      log.debug("Working dir for recipes script: {}".format(working_dir.as_posix()))

      if not recipes_script.exists():
        log.error("Recipes script does not exist: {}".format(recipes_script.as_posix()))
        return 1

      log.info("Processing '{0}'".format(recipes_script))

      if recipes_script.suffix == ".py":
        # Remove file extension.
        recipes_script = recipes_script.parent / recipes_script.stem

      # Load the recipe, which will register some handlers.
      import_module(recipes_script.as_posix())
      if len(recipes) == 0:
        log.error("No recipes found. Make sure to create functions in your script and decorate them with @recipe.")
        return

      for rcp in recipes:
        # Call the recipe with our pot.
        rcp(pot)

    # We always treat `output` as a directory.
    output.safe_mkdir(parents=True)

    menu = Menu(output)
    log.info("Menu file path: {}".format(menu.filePath.as_posix()))
    menu.load()
    # All ingredients are collected in the pot now, so the baker can start working.
    bakerFunc(menu=menu, pot=pot, options=kwargs)
    menu.save()
