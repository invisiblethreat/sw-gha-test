# pylint: disable=missing-docstring
from pathlib import Path

from setuptools import setup, find_packages

__version__ = "0.4.1"

with Path('README.md').open('r') as long_description_file:
    LONG_DESCRIPTION = long_description_file.read()

setup(
    name='api_key_detector',
    version=__version__,
    description='api key detector',
    author='Terry Rodery',
    author_email='terry@coalitioninc.com',
    url='https://github.com/cruicible-risk/ld-api-key-detector/',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.8',
    zip_safe=False,
    package_data={
        '': ['*.yml', '*.yaml', '*.txt', '*.pki', '*.pkl', '*.json'],
    },
    install_requires=[
        'rstr==2.2.6',
        'numpy==1.18.4',
        'scipy==1.4.1',
        'scikit_learn==0.22.2.post1',
        'PyYAML',
    ],
    tests_requires=[
        'pytest',
        'pytest-cov',
        'pytest-ordering',
        'pytest-pylint',
    ],
)
