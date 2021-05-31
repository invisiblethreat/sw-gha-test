# pylint: disable=missing-docstring,exec-used,undefined-variable
from pathlib import Path

from setuptools import setup, find_packages


__version__ = "0.7.1"

with Path('README.md').open('r') as long_description_file:
    LONG_DESCRIPTION = long_description_file.read()

setup(
    name='ContentAnalyzer',
    version=__version__,
    description='Source code and other file metadata analyzers',
    author='Terry Rodery',
    author_email='terry@coalitioninc.com',
    url='https://github.com/crucible-risk/content-analyzer',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.6',
    zip_safe=False,
    package_data={
        '': [
            '*.yml',
            '*.yaml',
            '*.txt',
            '*.pki',
            '*.pkl',
            '*.json',
            '*.jar',
            '*.lark',
            ],
    },
    install_requires=[
        'more_itertools',
        'attrs',
        'pygments',
        'PyYAML',
        'parso==0.4.0',
        'esprima==4.0.1',
        'javalang',
        'ply==3.11',
        'lark-parser',
    ],
    tests_requires=[
        'pytest',
        'pytest-cov',
        # 'pytest-ordering',
        'pytest-pylint',
    ],
)
