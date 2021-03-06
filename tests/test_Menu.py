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
    p1 = Pastry(name="foo", version="0.1.0")
    p2 = Pastry(name="bar", version="1.33.7")
    self.assertFalse(m.get(p1.name, p1.version))
    self.assertFalse(m.get(p2.name, p2.version))
    m.add(p1)
    self.assertTrue(m.get(p1.name, p1.version))
    self.assertFalse(m.get(p2.name, p2.version))
    m.remove(p1)
    self.assertFalse(m.get(p1.name, p1.version))
    self.assertFalse(m.get(p2.name, p2.version))
    with self.assertRaises(AssertionError):
      m.add(42)
    with self.assertRaises(AssertionError):
      m.add(dict(p1))

  def test_LoadSave(self):
    m = Menu("MenuTests/test_LoadSave.json")
    p1 = Pastry(name="foo", version="0.1.0")
    m.add(p1)
    m.save()
    m.clear()
    self.assertEqual(len(m), 0)
    m.load()
    self.assertEqual(len(m), 1)
    self.assertEqual(m.get(p1.name, p1.version), p1)
