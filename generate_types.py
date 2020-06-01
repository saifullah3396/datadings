import os.path as pt
from codecs import open
import json

from setuptools.command.build_py import build_py as _build_py


PACKAGE_DIR = pt.abspath(pt.dirname(__file__))


def __argify(key):
    return key if isinstance(key, str) else '_%r' % key


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
    args = ',\n        '.join(map(__argify, keys))
    values = ',\n'.join('        %r: %s' % (k, __argify(k)) for k in keys)
    return """
def {name}(
        {args}
):
    return {{
{values}
    }}
""".format(name=name, args=args, values=values)


def generate_types():
    types_json = pt.join(PACKAGE_DIR, 'generate_types.json')
    types_py = pt.join(PACKAGE_DIR, 'datadings', 'sets', '_types.py')
    with open(types_json) as f:
        typespec = json.load(f)
    with open(types_py, 'w') as f:
        f.write('# AUTO-GENERATED FILE! DO NOT EDIT!\n')
        for typename, keys in sorted(typespec.items()):
            f.write('\n')
            f.write(make_typefun(typename, keys))


class build_py(_build_py):
    def run(self):
        print('generating types')
        generate_types()
        # run the actual build command
        _build_py.run(self)


if __name__ == '__main__':
    generate_types()
