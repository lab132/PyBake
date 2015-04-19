"""Commands for argparse for basket command"""

import textwrap
from PyBake import Path
from PyBake.commands import command


@command("basket")
class BasketModuleManager:
  """Module Manager for Basket"""

  longDescription = textwrap.dedent(
  """
  Retrieves pastries from the shop.
  """)

  def createArguments(self, basketParser):
    basketParser.add_argument("shoppingList",
                              nargs="?",
                              default=Path("shoppingList.py"),
                              type=Path,
                              help="The shopping list script that describes which pastries are required. "
                                   "Default: 'shoppingList.py'")
    basketParser.add_argument("--force-download",
                              dest="force",
                              action="append_const",
                              const="download",
                              help="Download all required pastries, whether they exist locally already or not.")
    basketParser.add_argument("--force-install",
                              dest="force",
                              action="append_const",
                              const="install",
                              help="Perform an install, regardless whether the pastry is already installed or not.")
    basketParser.add_argument("--force",
                              dest="force",
                              action="append_const",
                              const="all",
                              help="Implies --force-download and --force-install.")
    basketParser.set_defaults(func=execute_basket)

def execute_basket(args):
  """Execute the `basket` command."""
  from PyBake import log
  force = args.force or []
  del args.force
  args.forceDownload = any(arg in ("all", "download") for arg in force)
  args.forceInstall = any(arg in ("all", "install") for arg in force)
  log.debug(args)
  from PyBake import basket
  return basket.run(**vars(args))
