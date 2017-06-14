""" A collection of tools to prepare public datasets for
    machine learning, i.e., to convert them into easy to
    handle and quick to read messagepack files.
"""
from __future__ import print_function

from codecs import open
import os
import os.path as pt
import io
import re
from setuptools import setup, find_packages


PACKAGE_DIR = pt.abspath(pt.dirname(__file__))


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


# pip's single-source version method as described here:
# https://python-packaging-user-guide.readthedocs.io/single_source_version/
def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Use the README as the long description
with open(pt.join(PACKAGE_DIR, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


packages = find_packages(
    include=['datadings', 'datadings.*'],
)


package_data = {
    package: [
        '*.py',
        '*.json',
        '*.html',
        '*.txt',
        pt.join('assets', '*'),
        pt.join('data', '*')
    ]
    for package in packages
}


with open(pt.join(PACKAGE_DIR, 'requirements.txt')) as f:
    dependencies = [l.strip(' \n') for l in f]


scripts = [
    'bin/datadings-bench',
    'bin/datadings-merge',
    'bin/datadings-sample',
    'bin/datadings-show',
    'bin/datadings-shuffle',
    'bin/datadings-write',
]


setup(
    name='datadings',
    version=find_version('datadings', '__init__.py'),
    description=__doc__,
    long_description=long_description,
    url='https://git.opendfki.de/joachim.folz/datadings',
    author='Joachim Folz',
    author_email='joachim.folz@dfki.de',
    license='GPLv2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'License :: OSI Approved :: GPL v2 License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='datadings datasets data sets classification saliency',
    packages=packages,
    package_data=package_data,
    install_requires=dependencies,
    scripts=scripts,
)
