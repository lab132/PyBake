from tests import *

class TestVersion(TestCase):
  def test_Version(self):
     v = Version("0.1.0")
     self.assertIs(Version(v), v)

  def test_VersionSpec(self):
    s = VersionSpec(">0.1.0")
    self.assertIs(s, VersionSpec(s))
