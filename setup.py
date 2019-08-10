import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "mitba", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIRES = [
    "logbook",
    "flux",
]

setup(name="mitba",
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          ],
      description="Python library for caching results from functions and methods",
      license="BSD3",
      author="Infinidat Ltd.",
      author_email="info@infinidat.com",
      version=__version__, # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),

      url="https://github.com/Infinidat/mitba",

      install_requires=_INSTALL_REQUIRES,
      scripts=[],
      namespace_packages=[]
     )
