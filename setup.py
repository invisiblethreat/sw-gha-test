# pylint: disable=missing-docstring,exec-used,undefined-variable
from pathlib import Path

from setuptools import setup, find_packages


with Path('ExtFs/__init__.py').open('r') as version_file:
    exec(version_file.read())

with Path('README.md').open('r') as long_description_file:
    LONG_DESCRIPTION = long_description_file.read()

setup(
    name='ExtFs',
    version=__version__,
    description='Pure python implementation to read ext2/3/4 filesystems',
    author='Terry Rodery',
    author_email='terry@coalitioninc.com',
    url='https://github.com/crucible-risk/extfs/',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'more_itertools',
    ],
    tests_requires=[
        'pytest',
        'pytest-cov',
        'pytest-ordering',
        'pytest-pylint',
    ],
)
