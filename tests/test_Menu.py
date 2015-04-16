from tests import *

class MenuTests(TestCase):
  def test_LoadSaveEmpty(self):
    m = Menu()
    # Load nonexistant file.
    m.load()
    # Save 'empty' file.
    m.save()

  def test_AddRemove(self):
    m = Menu()
    p1 = PastryDesc(name="foo", version="v0.1.0")
    p2 = PastryDesc(name="bar", version="v1.33.7")
    self.assertFalse(m.exists(p1))
    self.assertFalse(m.exists(p2))
    m.add(p1)
    self.assertTrue(m.exists(p1))
    self.assertFalse(m.exists(p2))
    m.remove(p1)
    self.assertFalse(m.exists(p1))
    self.assertFalse(m.exists(p2))
    with self.assertRaises(AssertionError):
      m.add(42)
    with self.assertRaises(AssertionError):
      m.add(dict(p1))

  def test_LoadSave(self):
    m = Menu()
    p1 = PastryDesc(name="foo", version="v0.1.0")
    m.add(p1)
    m.save("MenuTests/test_LoadSave.json")
    m.clear()
    self.assertEqual(m.numEntries(), 0)
    m.load("MenuTests/test_LoadSave.json")
    self.assertEqual(m.numEntries(), 1)
    self.assertEqual(m.get(p1), p1)
