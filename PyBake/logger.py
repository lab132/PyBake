"""
Logging facility of our bakery
"""

import sys
from enum import IntEnum, unique
from clint.textui import progress


@unique
class LogVerbosity(IntEnum):
  """Available log verbosity."""
  Error = 1,  # Print only error Messages and messages that marked as 'All'
  SeriousWarning = 2,  # Print Seriouse warnings and above
  Warning = 3,  # Print Warnings and above
  Success = 4,  # Print Success and above.
  Info = 5,  # Print Info and above
  Dev = 6,  # Print development messages and above
  Debug = 7,  # Print debug messages and above
  All = 8  # Print ALL Messages


@unique
class LogLevel(IntEnum):
  """Available log levels."""
  All = 0,  # Log this one always
  Error = 1,  # An error message.
  SeriousWarning = 2,  # A serious warning message.
  Warning = 3,  # A warning message.
  Success = 4,  # A success message.
  Info = 5,  # An info message.
  Dev = 6,  # A development message.
  Debug = 7,  # A debug message.


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
    self.progress_bar = None
    self.prev_bar_template = None

    def create_log_message_function(value):
      """Helper to create a logging function with a captures verbosity `value`."""
      return lambda self, message: self.log_message(value, message)

    # Auto generate helper methods like
    # LogBackend.error("This is an error!") or LogBackend.warning() out of the LogVerbosity enum
    for name, value in LogLevel.__members__.items():
      setattr(LogBackend, name.lower(), create_log_message_function(value))

  def __call__(self, *args):
    self.info(*args)

  def addLogSink(self, sink):
    """
    Add a log sink that will be called when a logging event occurs.
    Can all the same sink multiple times.
    """
    self.sinks.append(sink)

  def removeLogSink(self, sink):
    """Remove a log sink so it won't receive logging events anymore."""
    self.sinks.remove(sink)

  def addLogBlock(self, block):
    """Add a log block to the current logging context."""
    self.blockStack.append(block)

  def removeLogBlock(self, block):
    """Remove a log block from the current logging context. if appropriate, the log block message will be printed."""
    if self.blockStack[-1] == block:
      if block.printed is True:  # Block was printed so we need to print out that we close this block now
        blockInfo = {
          "blockLevel": len(self.blockStack) - 1,  # Decrement by one so the first LogBlock is at indentation 0
          "name": block.name,
          "isOpening": False
        }
        for sink in self.sinks:
          sink.log_block(**blockInfo)
      self.blockStack.pop()
    else:
      raise ValueError("The given block is not the last Element in the stack!")

  def start_progress(self, expected_size, progress_char="=", bar_template=progress.BAR_TEMPLATE):
    """Creates a progress bar."""
    self.prev_bar_template = progress.BAR_TEMPLATE
    progress.BAR_TEMPLATE = bar_template
    self.progress_bar = progress.Bar(expected_size=expected_size, filled_char=progress_char)

  def set_progress(self, progressValue):
    """Sets the progress of the current progress bar if any."""
    if self.progress_bar:
      self.progress_bar.show(progressValue)

  def end_progress(self):
    """Completes the progress."""
    if self.progress_bar:
      self.progress_bar.done()
      self.progress_bar = None
      progress.BAR_TEMPLATE = self.prev_bar_template

  def log_message(self, verbosity, message):
    """Raise the logging event."""
    if not self.quiet and verbosity <= self.verbosity:
      logInfo = {
        "message": message,
        "verbosity": verbosity,
        "blockLevel": len(self.blockStack)
      }
      for block in reversed(self.blockStack):
        if block.printed is False:
          block.printed = True
          blockInfo = {
            "blockLevel": len(self.blockStack) - 1,  # Decrement by one so the first LogBlock is at indentation 0
            "name": block.name,
            "isOpening": True
          }
          for sink in self.sinks:
            sink.log_block(**blockInfo)
        else:
          break  # We reached the position in the stack where all messages are printed so stop
      for sink in self.sinks:
        sink.log_message(**logInfo)

# Create a global LogBackend
log = LogBackend()


class StdOutSink:
  """Standard log sink that prints to `stdout`."""

  def log_message(self, *, verbosity, message, blockLevel):
    """Handle the logging event."""
    output = sys.stdout
    if verbosity <= LogVerbosity.Warning:
      output = sys.stderr
    output.write("{0}{1}\n".format("  " * blockLevel, message))

  def log_block(self, *, blockLevel, name, isOpening):
    """Handle the log block event."""
    sys.stdout.write("{0}{1} {2}\n".format("  " * blockLevel, "+++" if isOpening else "---", name))


class LogBlock:
  """
  Create a log block in the current logging context.

  Example:
    with LogBlock("Hello"):
      log.info("World")

    With the StdOutSink, will print something like this:
    +++ Hello
      World
    --- Hello
  """

  def __init__(self, name, backend=log):
    self.printed = False
    self.name = name
    self.backend = log

  def __enter__(self):
    self.backend.addLogBlock(self)

  enter = __enter__

  def __exit__(self, *args):
    self.backend.removeLogBlock(self)

  exit = __exit__
