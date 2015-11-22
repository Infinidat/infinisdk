import os
import sys
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "infinisdk", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIRES = [
    "api_object_schema>=1.5.1",
    "arrow>=0.6.0",
    "capacity",
    "colorama",
    "confetti>=2.1.0",
    "flux",
    "gossip>=0.8.0",
    "infi.dtypes.wwn>=0.0.2",
    "infi.pyutils",
    "logbook>=0.10.0",
    "munch",
    "pact>=1.0.0",
    "requests>=2.4.0",
    "sentinels",
    "storage_interfaces",
    "URLObject",
]

if sys.version_info < (3, 0):
    _INSTALL_REQUIRES.append('contextlib2')

setup(name="infinisdk",
      classifiers = [
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          ],
      description="Infinidat API SDK",
      license="Proprietary",
      author="Infinidat",
      author_email="info@infinidat.com",
      version=__version__, # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),

      url="http://devdocs.infinidat.com/sphinx/infinisdk/",

      install_requires=_INSTALL_REQUIRES,
      scripts=[],
      namespace_packages=[]
      )
