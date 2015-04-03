"""Setup configuration for PyBake
"""


from setuptools import setup, find_packages

from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "PyBake", "VERSION"), encoding="UTF-8") as f:
  versionString = f.read().strip()

setup(
  name="PyBake",
  version=versionString,
  description="Python implemented dependencies package management system. As easy as baking pie.",
  url="https://github.com/lab132/PyBake",
  author="lab132",
  author_email="nobody@nowhere.nevada",
  license="MIT",
  classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 3 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: MIT License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3.4',
  ],
  keywords="packaging package management distribution dependencies pie bake shop pastry oven stock menu shopping list",
  packages=['PyBake'],
  install_requires=[
    'flask',
    'argparse',
    'watchdog',
    'requests',
    'clint'
    ],
  package_data={
    "PyBake": ["VERSION"]
  }
  )
