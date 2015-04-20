from tests import *

class PastryTests(TestCase):
  def test_VersionValidity(self):
    with self.assertRaises(ValueError):
      Pastry(name="name", version="I am invalid")
    with self.assertRaises(ValueError):
      Pastry(name="name", version="v.0.1.0")
    with self.assertRaises(ValueError):
      Pastry(name="name", version="v1.0")
    with self.assertRaises(ValueError):
      Pastry(name="name", version="1.0")
  def test_toDict(self):
    name = "foo"
    version = "0.1.0"
    data = {"name": name, "version": version}
    p1 = Pastry(data)
    self.assertDictEqual(dict(p1), data)
    p2 = Pastry(name=name, version=version)
    self.assertDictEqual(dict(p2), data)

  def test_strAndRepr(self):
    p = Pastry(name="foo", version="0.1.0")
    self.assertEqual(str(p), "foo 0.1.0")
    self.assertEqual(repr(p), "Pastry(name='foo', version='0.1.0')")

  def test_path(self):
    p = Pastry(name="foo", version="0.1.0")
    self.assertEqual(p.path, Path("foo_0.1.0.zip"))

  def test_eq(self):
    p1 = Pastry(name="foo", version="0.1.0")
    p2 = Pastry(name="foo", version="0.1.0")
    p3 = Pastry(name="bar", version="0.1.0")
    self.assertEqual(p1, p2)
    self.assertEqual(p2, p1)
    self.assertNotEqual(p1, p3)
    self.assertNotEqual(p2, p3)
