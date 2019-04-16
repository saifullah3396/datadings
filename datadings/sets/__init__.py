from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os.path as pt
import json

from six import text_type


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


def __generate_types():
    root = pt.dirname(__file__)
    types_json = pt.join(root, '_types.json')
    types_py = pt.join(root, '_types.py')
    if (pt.exists(types_json) and not pt.exists(types_py)) \
    or pt.getmtime(types_json) >= pt.getmtime(types_py):
        with open(types_json) as f:
            typespec = json.load(f)
        with open(types_py, 'w') as f:
            f.write('from __future__ import unicode_literals\n')
            for typename, keys in typespec.items():
                f.write('\n\n')
                f.write(make_typefun(typename, keys))


__generate_types()
from ._types import *
