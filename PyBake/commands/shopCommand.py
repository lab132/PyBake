"""Command generation for the shop"""

from PyBake.commands import command
from PyBake import log
import textwrap

@command("shop")
class ShopModuleManager:
  """Creating argparse arguments for the shop command and the command itself"""

  longDescription = textwrap.dedent(
    """
    Sets up a server for crumble management
    """)

  def createArguments(self, shopParser):
    shopParser.add_argument("-c", "--config", default="shop_config",
                            help="Supply a custom config for the shop (defaults to shop_config")
    shopParser.set_defaults(func=execute_shop)

def execute_shop(args):
  """Execute the `shop` command."""
  log.debug(args)
  from PyBake import shop
  return shop.run(**vars(args))
