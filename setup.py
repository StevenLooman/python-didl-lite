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
    DESCRIPTION = f.readline()
    print(DESCRIPTION)


TEST_REQUIRES = [
    'pytest',
    'flake8',
    'pylint',
    'pydocstyle',
]


setup(
    name='python-didl-lite',
    version='1.0.1',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='https://github.com/StevenLooman/python-didl-lite',
    author='Steven Looman',
    author_email='steven.looman@gmail.com',
    license='http://www.apache.org/licenses/LICENSE-2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    packages=['didl_lite'],
    tests_require=TEST_REQUIRES,
    cmdclass={'test': PyTest},
)
