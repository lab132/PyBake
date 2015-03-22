'''
Logging facility of our bakery
'''

import sys
from enum import IntEnum, unique
import textwrap

@unique
class LogVerbosity(IntEnum):
  Error = 1
  Warning = 2
  Log = 3
  Verbose = 4
  Info = 5

def create_log_message_function(value):

  def log_message(self, message):
    self.log_message(value, message)
  return log_message

class LogBackend:

  def __init__(self, *, sinks=[], verbosity=LogVerbosity.Log, quiet=False):
    self.sinks = sinks
    self.verbosity = verbosity
    self.quiet = quiet
    self.blockStack = []

    # Auto generate helper methods like LogBackend.error("This is an error!") or LogBackend.warning() out of the LogVerbosity enum
    for name, value in LogVerbosity.__members__.items():
     setattr(LogBackend, name.lower(), create_log_message_function(value))


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
    sys.stdout.write("{0} {1} {2}\n".format("  " * blockLevel, "+++" if isOpening else "---", name))




class logBlock:

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
