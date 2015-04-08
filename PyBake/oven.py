"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *
import json
import zipfile


class Pot:
  """Manages new pastries when processing recipes."""

  def __init__(self):
    self.ingredients = {}

  def get(self, name, version, platform=Platform.All):
    """Get a pastry matching the given name, version, and platform."""
    key = (name, version, platform)
    assert None not in key, "None of the given arguments are allowed to be `None`."
    listOfIngredients = self.ingredients.get(key, None)
    if listOfIngredients is None:
      log.debug("Creating new entry in pot: {}".format(key))
      listOfIngredients = []
      self.ingredients[key] = listOfIngredients
    return listOfIngredients


def writePastryJson(zipFile, name, version, platform):
  """Helper function of `zipBaker` that writes a pastry.json file to the given `zipFile`."""
  log.info("Writing pastry.json...")
  pastry = {}
  pastry["name"] = name
  pastry["version"] = version
  pastry["platform"] = platform
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


def zipBaker(*, outDirPath, pot, options):
  """Processes ingredients in a pot and creates pastries from that."""

  log.info("Creating directory for pastries: {}".format(outDirPath.as_posix()))
  outDirPath.safe_mkdir(parents=True)

  with LogBlock("Baking Pastries (Zip)"):
    for key, ingredients in pot.ingredients.items():
      name = key[0]
      version = key[1]
      platform = key[2]
      with LogBlock("{} version {} for platform {} with {} ingredients".format(name, version, platform, len(ingredients))):
        platformName = str(platform) if platform is not Platform.All else ""
        zipFilePath = outDirPath / createFilename(name, version, platformName, fileExtension=".zip")
        with zipfile.ZipFile(zipFilePath.as_posix(), "w", compression=options["compression"]) as zipFile:
          writePastryJson(zipFile, name, version, platform)
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

    # All ingredients are collected in the pot now, so the baker can start working.
    bakerFunc(outDirPath=output, pot=pot, options=kwargs)
