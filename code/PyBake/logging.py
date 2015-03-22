'''
Logging facility of our bakery
'''

import sys
from enum import IntEnum, unique

@unique
class LogVerbosity(IntEnum):
  Error = 1
  Warning = 2
  Log = 3
  Verbose = 4
  Info = 5

def create_log_message(value):

  def log_message(self, message):
    self.log_message(value, message)
  return log_message

class LogBackend:

  def __init__(self, *, sinks=[], verbosity=LogVerbosity.Log, quiet=False):
    self.sinks = sinks
    self.verbosity = verbosity
    self.quiet = quiet

    # Auto generate helper methods like LogBackend.error("This is an error!") or LogBackend.warning() out of the LogVerbosity enum
    for name, value in LogVerbosity.__members__.items():
     setattr(LogBackend, name.lower(),create_log_message(value))


  def addLogSink(self, sink):
    """Adds a log sink to the logger, a log sink needs a 'log_message(verbosity, message)' function."""
    self.sinks.append(sink)

  def removeLogSink(self, sink):
    self.sinks.remove(sink)

  def log_message(self, verbosity, message):
    if not self.quiet and verbosity <= self.verbosity:
      for sink in self.sinks:
        sink.log_message(verbosity, message)

class StdOutSink:

  def log_message(self, verbosity, message):
    if verbosity <= LogVerbosity.Warning:
      sys.stderr.write("{0}\n".format(message))
    else:
      sys.stdout.write("{0}\n".format(message))

Log = LogBackend()
