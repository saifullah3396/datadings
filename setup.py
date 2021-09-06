"""
datadings is a collection of tools to prepare datasets for machine
learning.
It's easy to use, space-efficient, and blazingly fast.
"""
import os
import os.path as pt
import re
from setuptools import setup, find_packages

from generate_types import build_py


PACKAGE_DIR = pt.abspath(pt.dirname(__file__))


def read(*names, **kwargs):
    with open(
        pt.join(os.path.dirname(__file__), *names),
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
long_description = read(PACKAGE_DIR, 'README.rst')


packages = find_packages(
    include=['datadings', 'datadings.*'],
)


package_data = {
    package: [
        '*.gz',
        '*.html',
        '*.json',
        '*.msgpack',
        '*.py',
        '*.txt',
        '*.xz',
        pt.join('assets', '*'),
        pt.join('data', '*')
    ]
    for package in packages
}


dependencies = read(PACKAGE_DIR, 'requirements.txt').splitlines()


console_scripts = [
    'datadings-{cmd}=datadings.commands.{cmd}:entry'.format(cmd=cmd)
    for cmd in (
        'bench',
        'cat'
        'merge',
        'sample',
        'shuffle',
        'split',
        'write',
    )
]


setup(
    name='datadings',
    version=find_version('datadings', '__init__.py'),
    description=__doc__.replace('\n', ' '),
    long_description=long_description,
    long_description_content_type='text/x-rst; charset=UTF-8',
    author='Joachim Folz',
    author_email='joachim.folz@dfki.de',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='datadings datasets data sets image '
             'classification semantic segmentation saliency',
    packages=packages,
    package_data=package_data,
    install_requires=dependencies,
    extras_require={
        "geo": ["GDAL>=2.4.0"],
    },
    entry_points={
        'console_scripts': console_scripts,
    },
    cmdclass={
        'build_py': build_py,
    },
    project_urls={
        'Documentation': 'https://datadings.readthedocs.io',
        'Source': 'https://gitlab.com/jfolz/datadings',
        'Tracker': 'https://gitlab.com/jfolz/datadings/issues',
    },
)
