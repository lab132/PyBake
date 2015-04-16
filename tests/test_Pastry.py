from tests import *

class PastryDescTests(TestCase):
  def test_toDict(self):
    name = "foo"
    version = "v0.1.0"
    data = {"name": name, "version": version}
    p1 = PastryDesc(data)
    self.assertDictEqual(dict(p1), data)
    p2 = PastryDesc(name=name, version=version)
    self.assertDictEqual(dict(p2), data)

  def test_strAndRepr(self):
    p = PastryDesc(name="foo", version="v0.1.0")
    self.assertEqual(str(p), "foo v0.1.0")
    self.assertEqual(repr(p), "PastryDesc(name='foo', version='v0.1.0')")

  def test_path(self):
    p = PastryDesc(name="foo", version="v0.1.0")
    self.assertEqual(p.path, Path("foo_v0.1.0.zip"))

  def test_eq(self):
    p1 = PastryDesc(name="foo", version="v0.1.0")
    p2 = PastryDesc(name="foo", version="v0.1.0")
    p3 = PastryDesc(name="bar", version="v0.1.0")
    self.assertEqual(p1, p2)
    self.assertEqual(p2, p1)
    self.assertNotEqual(p1, p3)
    self.assertNotEqual(p2, p3)

@notImplemented
class PastryTests(TestCase):
  def test_(self):
    pass
