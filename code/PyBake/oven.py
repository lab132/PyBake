"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *
import json
import zipfile

class JSONBakersApprentice(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Platform):
      return dict(obj)
    if isinstance(obj, Ingredient):
      return dict(obj)
    return json.JSONEncoder.default(self, obj)

class JSONBaker:
  """Simply serializes all ingredients as JSON to the given file."""
  def __init__(self, filepath, pastry_name, pastry_version, options):
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

class ZipBaker:
  # Suffix for the filepath while writing to it. Will be removed once all operations complete (transaction style).
  temp_suffix = ".tmp"

  """Packs all ingredients into a zip file along with some metadata encoded as JSON."""
  def __init__(self, filepath, pastry_name, pastry_version, options):
    # Append the temp suffix.
    filepath = Path(filepath.as_posix() + ZipBaker.temp_suffix)

    # Make sure the dir exists.
    if not filepath.parent.exists():
      filepath.parent.mkdir(parents=True)

    # Make sure the file exists so we can resolve to ab absolute path (below).
    filepath.touch()

    # Make an absolute path.
    self.filepath = filepath.resolve()

    # Open the zip file for writing.
    self.zip = zipfile.ZipFile(self.filepath.as_posix(), "w", compression=zipfile.ZIP_STORED)
    self.pastry_name = pastry_name
    self.pastry_version = pastry_version
    self.options = options or {}
    self.ingredients = []

  def process(self, ingredient):
    log.debug("Zipping: {}".format(repr(ingredient)))
    # Rember the ingredient so we can serialize it as JSON later.
    self.ingredients.append(ingredient)
    self.zip.write(ingredient.path.as_posix())

  def done(self):
    # Write pastry.json.
    pastry = {}
    pastry["name"] = self.pastry_name
    pastry["version"] = self.pastry_version
    pastryJSON = json.dumps(pastry, indent=2, sort_keys=True, cls=JSONBakersApprentice)
    self.zip.writestr("pastry.json", bytes(pastryJSON, "UTF-8"))

    # Write ingredients.json.
    ingredientsJSON = json.dumps(self.ingredients, indent=2, sort_keys=True, cls=JSONBakersApprentice)
    self.zip.writestr("ingredients.json", bytes(ingredientsJSON, "UTF-8"))

    # Close the zip file
    self.zip.close()

    log.debug("Replacing {0}{{{1.name} => {1.stem}}}".format(self.filepath.parent.as_posix(), self.filepath))
    self.filepath.replace(Path(self.filepath.stem))


def run(*,                    # Keyword arguments only.
        pastry_name,          # The name of the pastry.
        pastry_version,       # The version-string of the pastry.
        working_dir,          # Working directory in which to look for and execute the `recipe`
        recipe,               # The recipe to load, which provides ingredients.
        output,               # The target file specified by the user, e.g. a ZIP file. Relative to the original working dir.
        baker_class=ZipBaker, # Processes ingredients and creates a pastry.
        **kwargs):            # kwargs passed as `options` to the `baker_function`.
  with LogBlock("Oven"):
    # Make sure the working dir exists.
    working_dir = working_dir.resolve()

    baker = baker_class(output, pastry_name, pastry_version, kwargs)

    # Change into the working directory given by the user.
    with ChangeDir(working_dir):
      log.debug("Working dir for recipe: {}".format(working_dir.as_posix()))
      log.info("Processing recipe '{0}'".format(recipe))

      # Load the recipe, which will register some handlers that yield ingredients.
      import_module(recipe)
      if len(recipes) == 0:
        log.error("No recipes found. Make sure to create functions and decorate them with @recipe.")
        return

      for rcp in recipes:
        for ing in rcp():
          baker.process(ing)

      baker.done()
