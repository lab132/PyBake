from PyBake import *
import unittest
import os
import shutil


tempDir = Path(__file__).parent / "temp"


class TestCase(unittest.TestCase):
  """
  Custom TestCase implementation with standard setUp and tearDown methods.
  """

  def clearTempDir(self):
    """
    Clear the temp dir, i.e. delete all content. Does not delete the directory itself.
    This is also the working dir for all tests.
    """
    shutil.rmtree(tempDir.as_posix(), ignore_errors=True)

  def setUp(self):
    """
    Standard setUp makes sure the temp dir really exists and is the working dir.
    :return:
    """
    tempDir.safe_mkdir(parents=True)
    os.chdir(tempDir.as_posix())

  def tearDown(self):
    """
    Makes sure the temp dir is clean.
    """
    self.clearTempDir()

def skip(*, reason):
  """
  Like unittest.skip, except the reason is a required keyword argument.
  :param reason: The reason why a test was skipped.
  """
  return unittest.skip(reason)

# Use as a decorator on tests, similar to `skip`:
# @notImplemented
# def test_something(self): ...
notImplemented = skip(reason="Not implemented.")
