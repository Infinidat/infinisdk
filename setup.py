import os
import sys
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "infinipy2", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIERS = [
    "api_object_schema>=1.3.0",
    "capacity",
    "infi.pyutils",
    "logbook",
    "requests>=1.2.0",
    "sentinels",
    "slash",
    "URLObject",
    "confetti>=2.1.0",
    "infi.dtypes.wwn>=0.0.2",
    "storage_interfaces",
    "infinisim",
    "flux",
]

setup(name="infinipy2",
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

      url="http://devdocs.infinidat.com/sphinx/infinipy2/",

      install_requires=_INSTALL_REQUIERS,
      scripts=[],
      namespace_packages=[]
      )
