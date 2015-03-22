'''
Logging facility of our bakery
'''

import sys
from enum import IntEnum, unique

@unique
class LogVerbosity(IntEnum):
  Error          = 1, # Print only error Messages and messages that marked as 'All'
  SeriousWarning = 2, # Print Seriouse warnings and above
  Warning        = 3, # Print Warnings and above
  Success        = 4, # Print Success and above.
  Info           = 5, # Print Info and above
  Dev            = 6, # Print development messages and above
  Debug          = 7, # Print debug messages and above
  All            = 8  # Print ALL Messages

@unique
class LogLevel(IntEnum):
  All            = 0, # Log this one always
  Error          = 1, # An error message.
  SeriousWarning = 2, # A serious warning message.
  Warning        = 3, # A warning message.
  Success        = 4, # A success message.
  Info           = 5, # An info message.
  Dev            = 6, # A development message.
  Debug          = 7, # A debug message.


class LogBackend:
  """
  Main class for logging purposes.
  Features the enum names from LogLevel as lowercase functions for logging e.g.
  log.error(...)
  log.seriouswarning(...)

  where log is an object of this class
  """

  def __init__(self, *, sinks=[], verbosity=LogVerbosity.Success, quiet=False):
    self.sinks = sinks
    self.verbosity = verbosity
    self.quiet = quiet
    self.blockStack = []

    def create_log_message_function(value):
      return lambda self, message: self.log_message(value, message)

    # Auto generate helper methods like LogBackend.error("This is an error!") or LogBackend.warning() out of the LogVerbosity enum
    for name, value in LogLevel.__members__.items():
     setattr(LogBackend, name.lower(), create_log_message_function(value))

  def __call__(self, *args):
    self.info(*args)


  def addLogSink(self, sink):
    self.sinks.append(sink)

  def removeLogSink(self, sink):
    self.sinks.remove(sink)

  def addLogBlock(self, block):
    self.blockStack.append(block)

  def removeLogBlock(self, block):
    if self.blockStack[-1] == block:
      if block.printed == True: # Block was printed so we need to print out that we close this block now
        blockInfo = {
              "blockLevel" : len(self.blockStack)-1, # Decrement by one so the first LogBlock is at indentation 0
              "name" : block.name,
              "isOpening" : False
              }
        for sink in self.sinks:
          sink.log_block(**blockInfo)
      self.blockStack.pop()
    else:
      raise ValueError("The given block is not the last Element in the stack!")

  def log_message(self, verbosity, message):
    if not self.quiet and verbosity <= self.verbosity:
      logInfo = {
        "message" : message,
        "verbosity" : verbosity,
        "blockLevel" : len(self.blockStack)
        }
      for block in reversed(self.blockStack):
        if block.printed == False:
          block.printed = True
          blockInfo = {
              "blockLevel" : len(self.blockStack)-1, # Decrement by one so the first LogBlock is at indentation 0
              "name" : block.name,
              "isOpening" : True
              }
          for sink in self.sinks:
            sink.log_block(**blockInfo)
        else:
          break #We reached the position in the stack where all messages are printed so stop
      for sink in self.sinks:
        sink.log_message(**logInfo)

# Create a global LogBackend
log = LogBackend()


class StdOutSink:

  def log_message(self, *, verbosity, message, blockLevel):
    output = sys.stdout
    if verbosity <= LogVerbosity.Warning:
      output = sys.stderr
    output.write("{0}{1}\n".format("  " * blockLevel, message))

  def log_block(self, *, blockLevel, name, isOpening):
    sys.stdout.write("{0}{1} {2}\n".format("  " * blockLevel, "+++" if isOpening else "---", name))




class LogBlock:

  def __init__(self, name, log=log):
    self.printed = False
    self.name = name
    self.log = log


  def __enter__(self):
    self.log.addLogBlock(self)

  enter = __enter__

  def __exit__(self, type, value, tb):
    self.exit()

  def exit(self):
    self.log.removeLogBlock(self)
