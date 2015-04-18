"""Commands for argparse for basket command"""

import textwrap
from PyBake.commands import command


@command("basket")
class BasketModuleManager:
  """Module Manager for Basket"""

  longDescription = textwrap.dedent(
  """
  Retrieves pastries from the shop.
  """)

  def createArguments(self, basketParser):

    basketParser.add_argument("shopping_list",
                              nargs="?",
                              default="shoppingList",
                              help="Sets the used shoppingList (defaults to 'shoppingList') which will be reused"
                              "to retrieve pastries from the shop.")
    basketParser.set_defaults(func=execute_basket)

def execute_basket(args):
  """Execute the `basket` command."""
  from PyBake import log
  log.debug(args)
  from PyBake import basket
  return basket.run(**vars(args))
