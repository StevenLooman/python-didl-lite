import sys

import os.path

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '--strict',
            '--verbose',
            '--tb=long',
            '-vv',
            'tests']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    DESCRIPTION = f.readline().strip()


INSTALL_REQUIRES = [
    'defusedxml>=0.5.0',
]


TEST_REQUIRES = [
    'pytest',
    'flake8',
    'pylint',
    'pydocstyle',
]


setup(
    name='python-didl-lite',
    version='1.2.6',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    url='https://github.com/StevenLooman/python-didl-lite',
    author='Steven Looman',
    author_email='steven.looman@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=['didl_lite'],
    package_data={
        'didl_lite': ['py.typed'],
    },
    install_requires=INSTALL_REQUIRES,
    tests_require=TEST_REQUIRES,
    cmdclass={'test': PyTest},
)
