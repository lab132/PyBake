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
    self.printedBlocks = []
    self.newBlocks = []
    self.progressBar = None
    self.prevBarTemplate = None

    def create_log_message_function(value):
      """Helper to create a logging function with a captures verbosity `value`."""
      return lambda self, message: self.logMessage(value, message)

    # Auto generate helper methods like
    # LogBackend.error("This is an error!") or LogBackend.warning() out of the LogVerbosity enum
    for name, value in LogLevel.__members__.items():
      setattr(LogBackend, name.lower(), create_log_message_function(value))

  def __call__(self, *args):
    self.info(*args)

  @property
  def blockLevel(self):
      return len(self.printedBlocks) + len(self.newBlocks)

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
    self.newBlocks.append(block)

  def removeLogBlock(self, block):
    """Remove a log block from the current logging context. if appropriate, the log block message will be printed."""

    def doRemove(stack, *, broadcastTo):
      assert block is stack[-1], """Invalid stack order: Given block is not the last that was opened!
                                    You should always use `with LogBlock(...):` whenever possible.
                                 """
      # Pop the block from the stack.
      stack.pop()
      for sink in broadcastTo:
        sink.logBlock(block=block, isOpening=False)

    assert self.blockLevel > 0, "Cannot remove any log blocks: the block stack is empty!"

    if len(self.newBlocks) > 0:
      doRemove(self.newBlocks, broadcastTo=tuple())
    else:
      doRemove(self.printedBlocks, broadcastTo=self.sinks)

  def start_progress(self, expectedSize, progressChar="=", barTemplate=progress.BAR_TEMPLATE):
    """Creates a progress bar."""
    self.prevBarTemplate = progress.BAR_TEMPLATE
    progress.BAR_TEMPLATE = "  " * self.blockLevel + barTemplate
    self.progressBar = progress.Bar(expected_size=expectedSize, filled_char=progressChar)

  def set_progress(self, progressValue):
    """Sets the progress of the current progress bar if any."""
    if self.progressBar:
      self.progressBar.show(progressValue)

  def end_progress(self):
    """Completes the progress."""
    if self.progressBar:
      self.progressBar.done()
      self.progressBar = None
      progress.BAR_TEMPLATE = self.prevBarTemplate

  def logMessage(self, verbosity, message):
    """Raise the logging event."""
    if self.quiet or verbosity > self.verbosity:
      return

    # Log new blocks.
    for block in self.newBlocks:
      for sink in self.sinks:
        sink.logBlock(block=block, isOpening=True)
    # Add all new blocks to the list of printed blocks.
    self.printedBlocks += self.newBlocks
    # The current new blocks are no longer new; Clear it.
    self.newBlocks = []

    # Broadcast the actual log message.
    for sink in self.sinks:
      sink.logMessage(message=message,
                      verbosity=verbosity,
                      blockLevel=self.blockLevel)


# Create a global LogBackend
log = LogBackend()


class StdOutSink:
  """Standard log sink that prints to `stdout`."""

  def logMessage(self, *, verbosity, message, blockLevel):
    """Handle the logging event."""
    output = sys.stdout
    if verbosity <= LogVerbosity.Warning:
      output = sys.stderr
    output.write("{0}{1}\n".format("  " * blockLevel, message))

  def logBlock(self, *, block, isOpening):
    """Handle the log block event."""
    sys.stdout.write("{0}{1} {2}\n".format("  " * block.level, "+++" if isOpening else "---", block.name))


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

  def __init__(self, name, *, backend=log):
    self.name = name
    self.backend = backend
    self.level = self.backend.blockLevel

  def __enter__(self):
    self.backend.addLogBlock(self)

  enter = __enter__

  def __exit__(self, *args):
    self.backend.removeLogBlock(self)

  exit = __exit__
