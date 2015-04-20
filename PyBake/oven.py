"""
Generate a list of tagged files that will be combined to a crumble.
"""
from PyBake import *
import json
import zipfile


class Pastry(Pastry):
  """
  Oven pastries are special, because they can have ingredients and dependencies.
  """
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.ingredients = set()
    self.dependencies = set()

  def __iter__(self):
    log.debug("dicting pastry! {}".format(self))
    yield ("name", str(self.name))
    yield ("version", str(self.version))
    if len(self.dependencies):
      yield ("dependencies", [d for d in self.dependencies])

  def addIngredient(self, ing):
    """
    Adds and ingredient to this pastry.
    """
    self.ingredients.add(Path(ing))

  def addDependency(self, name, versionSpec):
    """
    Adds a dependency to this pastry.
    """
    dep = (str(name), VersionSpec(versionSpec))
    self.dependencies.add(dep)


class Pot:
  """
  Manages new pastries when processing recipes.
  """

  def __init__(self):
    self.pastries = []

  def get(self, name, version):
    """
    Get or create a special pot-pastry with the given name and version.
    You can use the returned pastry to add ingredients and pastries.
    pastry = pot.get("foo", "0.1.0")
    pastry.addIngredient(Path("some/file.h))
    pastry.addDependency("bar", VersionSpec(=="0.1.0"))
    """
    assert name, "Invalid `name`."
    assert version, "Invalid `version`"
    for p in self.pastries:
      if p.name == name and p.version == version:
        return p

    p = Pastry(name=name, version=version)
    self.pastries.append(p)
    return p


def writePastryJson(zipFile, pastry):
  """Helper function of `zipBaker` that writes a pastry.json file to the given `zipFile`."""
  log.info("Writing pastry.json...")
  pastryJSON = json.dumps(pastry, indent=2, sort_keys=True, cls=PastryJSONEncoder)
  zipFile.writestr("pastry.json", bytes(pastryJSON, "UTF-8"))


def writeIngredientsJson(zipFile, pastry):
  """Helper function of `zipBaker` that writes an ingredients.json file to the given `zipFile`."""
  log.info("Writing ingredients.json...")
  ingredientsJSON = json.dumps(pastry.ingredients, indent=2, sort_keys=True, cls=PastryJSONEncoder)
  zipFile.writestr("ingredients.json", bytes(ingredientsJSON, "UTF-8"))


def zipIngredients(zipFile, pastry):
  """Helper function of `zipBaker` that adds all files in `ingredients` to the `zipFile`"""
  log.info("Zipping ingredients...")
  for ingredient in pastry.ingredients:
    path = Path(ingredient).as_posix()
    log.debug(path)
    zipFile.write(path)


def zipBaker(*, menu, pot, force=False, options):
  """Processes ingredients in a pot and creates pastries from that."""
  with LogBlock("Baking Pastries (Zip)"):
    for pastry in pot.pastries:
      existing = menu.get(pastry.name, pastry.version)
      if existing and not force:
        log.debug("Ignoring pastry because it is already on the menu: {}".format(pastry))
        continue
      menu.add(pastry)
      zipFilePath = menu.makePath(pastry)
      with LogBlock("Pastry: {} with {} ingredients -> {}".format(pastry, len(pastry.ingredients), zipFilePath.as_posix())):
        if existing and force:
          log.info("Overwriting existing pastry file (force).")
        with zipfile.ZipFile(zipFilePath.as_posix(), "w", compression=options["compression"]) as zipFile:
          writePastryJson(zipFile, pastry)
          writeIngredientsJson(zipFile, pastry)
          zipIngredients(zipFile, pastry)

        log.success("Done baking pastry: {}".format(zipFilePath.as_posix()))


def run(*,                   # Keyword arguments only.
        recipes_script,      # Path to the recipes script.
        working_dir,         # Working directory when executing the recipes script.
        output,              # Directory that will contain all resulting pastries.
        force,               # Overwrite existing pastries.
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
    bakerFunc(menu=menu, force=force, pot=pot, options=kwargs)
    menu.save()
