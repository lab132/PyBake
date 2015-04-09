"""Main module for the arguments creation in PyBake
"""

commands = {}

class command:
  """Decorator for subcommands of PyBake"""
  def __init__(self, commandName):
    self.commandName = commandName

  def __call__(self, commandClass):
    commands[self.commandName] = commandClass