import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "infinisdk", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIERS = [
    "api_object_schema>=1.5.0",
    "arrow",
    "capacity",
    "colorama",
    "confetti>=2.1.0",
    "flux",
    "gossip>=0.8.0",
    "infi.dtypes.wwn>=0.0.2",
    "infi.pyutils",
    "logbook",
    "pact>=1.0.0",
    "python-dateutil", #  required to work around https://github.com/crsmithdev/arrow/issues/120
    "requests>=2.4.0",
    "sentinels",
    "storage_interfaces",
    "URLObject",
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
