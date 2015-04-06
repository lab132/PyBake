"""
Generate a list of tagged files that will be combined to a crumble.
"""

from importlib import import_module
from PyBake import *
import json
import zipfile


class JSONBaker:
  """Simply serializes all ingredients as JSON to the given file."""

  def __init__(self, filepath, pastry_name, pastry_version, options):
    self.filepath = filepath
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

    with self.filepath.open("w") as output:
      json.dump(pastry, output, indent=indent_output, sort_keys=sort_keys, cls=PastryJSONEncoder)


class ZipBaker:
  """Packs all ingredients into a zip file along with some metadata encoded as JSON."""

  # Suffix for the filepath while writing to it. Will be removed once all operations complete (transaction style).
  temp_suffix = ".tmp"

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
    self.zip = zipfile.ZipFile(self.filepath.as_posix(), "w", compression=zipfile.ZIP_DEFLATED)
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

    log.debug("Replacing {0}/{{ {1.name} => {1.stem} }}".format(self.filepath.parent.as_posix(), self.filepath))
    self.filepath.replace(Path(self.filepath.stem))


def run(*,                     # Keyword arguments only.
        pastry_name,           # The name of the pastry.
        pastry_version,        # The version-string of the pastry.
        working_dir,           # Working directory in which to look for and execute the `recipe`
        recipe_name,           # The name of the recipe to load, which provides ingredients.
        output,                # The target file e.g. a ZIP file. Relative to the original working dir.
        baker_class=ZipBaker,  # Processes ingredients and creates a pastry.
        **kwargs):             # kwargs passed as `options` to the `baker_function`.
  with LogBlock("Oven"):
    # Make sure the working dir exists.
    working_dir = working_dir.resolve()

    baker = baker_class(output, pastry_name, pastry_version, kwargs)

    # Change into the working directory given by the user.
    with ChangeDir(working_dir):
      log.debug("Working dir for recipe: {}".format(working_dir.as_posix()))
      log.info("Processing recipe '{0}'".format(recipe_name))

      # Load the recipe, which will register some handlers that yield ingredients.
      import_module(recipe_name)
      if len(recipes) == 0:
        log.error("No recipes found. Make sure to create functions in your script and decorate them with @recipe.")
        return

      for rcp in recipes:
        for ing in rcp():
          baker.process(ing)

      baker.done()
