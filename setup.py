"""Setup."""

import os.path

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()
with open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    DESCRIPTION = f.readline().strip()


INSTALL_REQUIRES = [
    "defusedxml>=0.6.0",
]


TEST_REQUIRES = [
    "pytest~=7.4.3",
]


setup(
    name="python-didl-lite",
    version="1.4.1",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    url="https://github.com/StevenLooman/python-didl-lite",
    author="Steven Looman",
    author_email="steven.looman@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    packages=["didl_lite"],
    package_data={
        "didl_lite": ["py.typed"],
    },
    python_requires=">=3.8",
    install_requires=INSTALL_REQUIRES,
    tests_require=TEST_REQUIRES,
)
