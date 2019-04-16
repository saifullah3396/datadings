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

from six import text_type


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


def __argify(key):
    return key if isinstance(key, text_type) else '_%r' % key


def make_typefun(name, keys):
    """
    Returns a function that creates dictionaries with fixed keys
    from positional arguments.
    Example:

    Data = make_typefun('Data', 'image', 'label', 3)

    This generates the following code:

    def Data(image, label, _3): return {'image': image, 'label': label, 3: _3}

    Note that any non-string key like 3 is prepended with '_'
    to make it a valid parameter name.

    :param name: Name of the function. Appears in the docstring.
    :param keys: Arbitrary number of dictionary key names
    :return: callable function
    """
    args = ', '.join(map(__argify, keys))
    values = ', '.join('%r: %s' % (k, __argify(k)) for k in keys)
    return 'def {name}({args}): return {{{values}}}\n' \
        .format(name=name, args=args, values=values)


def generate_types():
    import os.path as pt
    import json

    types_json = pt.join(PACKAGE_DIR, 'datadings', 'sets', '_types.json')
    types_py = pt.join(PACKAGE_DIR, 'datadings', 'sets', '_types.py')
    with open(types_json) as f:
        typespec = json.load(f)
    with open(types_py, 'w') as f:
        f.write('# AUTO-GENERATED FILE! DO NOT EDIT!\n')
        f.write('from __future__ import unicode_literals\n')
        for typename, keys in sorted(typespec.items()):
            f.write('\n\n')
            f.write(make_typefun(typename, keys))


generate_types()


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
        '*.gz',
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
    'bin/datadings-split',
    'bin/datadings-cat'
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='datadings datasets data sets classification saliency',
    packages=packages,
    package_data=package_data,
    install_requires=dependencies,
    scripts=scripts,
)
