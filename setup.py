import os
import sys
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "infinisdk", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIRES = [
    "gadget-python>=0.1.5",
    "api_object_schema>=1.5.1",
    "arrow>=0.6.0",
    "capacity>=1.3.8",
    "colorama",
    "confetti>=2.1.0",
    "click",
    "flux",
    'gossip>=1.1.2',
    "infi.dtypes.wwn>=0.0.2",
    "infi.dtypes.iqn>=0.3.0",
    "logbook>=0.11.0",
    "munch",
    "mitba",
    "pact>=1.0.0",
    "requests>=2.4.0",
    "sentinels",
    "storage_interfaces",
    "URLObject",
    "vintage>=0.3.0",
]

if sys.version_info < (3, 0):
    _INSTALL_REQUIRES.append('contextlib2')

setup(name="infinisdk",
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          ],
      description="Infinidat API SDK",
      license="BSD-3",
      author="Infinidat",
      author_email="info@infinidat.com",
      version=__version__, # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),

      url="https://infinisdk.readthedocs.org",

      install_requires=_INSTALL_REQUIRES,
      scripts=[],
      namespace_packages=[],
      entry_points={
          "console_scripts": [
              "infinisdk-cli = infinisdk.entry_point:main_entry_point",
          ]}
     )
