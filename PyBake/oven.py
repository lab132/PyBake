"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *
import json
import zipfile


class Pot:
  """Contains Dough that will be"""

  @staticmethod
  def createKey(name, version, platform):
    return createFilename(name, version, platform)

  def __init__(self):
    self.ingredients = {}

  def get(self, name, version, platform=Platform.All):
    """Get dough matching the index arguments."""
    assert platform is not None, "Expected valid platform instance, e.g. `Platform.All`."
    key = (name, version, platform)
    listOfIngredients = self.ingredients.get(key, None)
    if listOfIngredients is None:
      log.debug("Creating new entry in pot: {}".format(key))
      listOfIngredients = []
      self.ingredients[key] = listOfIngredients
    return listOfIngredients


def zipBaker(*, outDirPath, pot, options):
  """Processes ingredients in a pot and creates pastries from that."""

  def writePastryJson(zipFile, name, version, platform):
    log.info("Writing pastry.json...")
    pastry = {}
    pastry["name"] = name
    pastry["version"] = version
    pastry["platform"] = platform
    pastryJSON = json.dumps(pastry, indent=2, sort_keys=True, cls=PastryJSONEncoder)
    zipFile.writestr("pastry.json", bytes(pastryJSON, "UTF-8"))

  def writeIngredientsJson(zipFile, ingredients):
    log.info("Writing ingredients.json...")
    ingredientsJSON = json.dumps(ingredients, indent=2, sort_keys=True, cls=PastryJSONEncoder)
    zipFile.writestr("ingredients.json", bytes(ingredientsJSON, "UTF-8"))

  def zipIngredients(zipFile, ingredients):
    log.info("Zipping ingredients...")
    for ingredient in ingredients:
      path = Path(ingredient).as_posix()
      log.debug(path)
      zipFile.write(path)

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

class JSONBaker:
  """Simply serializes all ingredients as JSON to the given file."""

  def __init__(self, filePath, pastry_name, pastry_version, options):
    self.filePath = filePath
    self.pastry_name = pastry_name
    self.pastry_version = pastry_version
    self.options = options or {}
    self.ingredients = []

  def process(self, ingredient):
    """Processes an ingredient when querying user recipes."""
    self.ingredients.append(ingredient)

  def done(self):
    """Finalize processing of all ingredients."""
    # Create pastry meta info
    pastry = {}
    pastry["name"] = self.pastry_name
    pastry["version"] = self.pastry_version
    pastry["ingredients"] = self.ingredients

    indent_output = not self.options.get("no_indent_output", False)
    sort_keys = self.options.get("sort_keys", True)

    with self.filePath.open("w") as output:
      json.dump(pastry, output, indent=indent_output, sort_keys=sort_keys, cls=PastryJSONEncoder)


class ZipBaker:
  """Packs all ingredients into a zip file along with some metadata encoded as JSON."""

  # Suffix for the filePath while writing to it. Will be removed once all operations complete (transaction style).
  temp_suffix = ".tmp"

  def __init__(self, filePath, pastry_name, pastry_version, options):
    # Append the temp suffix.
    filePath = Path(filePath.as_posix() + ZipBaker.temp_suffix)

    # Make sure the dir exists.
    if not filePath.parent.exists():
      filePath.parent.mkdir(parents=True)

    # Make sure the file exists so we can resolve to ab absolute path (below).
    filePath.touch()

    # Make an absolute path.
    self.filePath = filePath.resolve()

    # Open the zip file for writing.
    self.zip = zipfile.ZipFile(self.filePath.as_posix(), "w", compression=zipfile.ZIP_DEFLATED)
    self.pastry_name = pastry_name
    self.pastry_version = pastry_version
    self.options = options or {}
    self.ingredients = []

  def process(self, ingredient):
    """Processes an ingredient when querying user recipes."""
    log.debug("Zipping: {}".format(repr(ingredient)))
    # Rember the ingredient so we can serialize it as JSON later.
    self.ingredients.append(ingredient)
    self.zip.write(ingredient.path.as_posix())

  def done(self):
    """Finalize processing of all ingredients."""
    # Write pastry.json.
    pastry = {}
    pastry["name"] = self.pastry_name
    pastry["version"] = self.pastry_version
    pastryJSON = json.dumps(pastry, indent=2, sort_keys=True, cls=PastryJSONEncoder)
    self.zip.writestr("pastry.json", bytes(pastryJSON, "UTF-8"))

    # Write ingredients.json.
    ingredientsJSON = json.dumps(self.ingredients, indent=2, sort_keys=True, cls=PastryJSONEncoder)
    self.zip.writestr("ingredients.json", bytes(ingredientsJSON, "UTF-8"))

    # Close the zip file
    self.zip.close()

    log.debug("Replacing {0}/{{ {1.name} => {1.stem} }}".format(self.filePath.parent.as_posix(), self.filePath))
    self.filePath.replace(Path(self.filePath.stem))


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
