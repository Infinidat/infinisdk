import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "infinisdk", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIERS = [
    "api_object_schema>=1.4.0",
    "arrow",
    "capacity",
    "colorama",
    "infi.pyutils",
    "logbook",
    "requests>=1.2.0",
    "sentinels",
    "gossip>=0.6.0",
    "URLObject",
    "confetti>=2.1.0",
    "infi.dtypes.wwn>=0.0.2",
    "storage_interfaces",
    "flux",
]

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

      install_requires=_INSTALL_REQUIERS,
      scripts=[],
      namespace_packages=[]
      )
