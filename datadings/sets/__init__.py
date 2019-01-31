from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

from six import text_type


def __argify(key):
    return key if isinstance(key, text_type) else '_%r' % key


def make_typefun(name, *keys):
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
    values = ', '.join('%r:%s' % (k, __argify(k)) for k in keys)
    code = 'def {name}({args}): return {{ {values} }}' \
        .format(name=name, args=args, values=values)
    target = {}
    exec(code, {}, target)
    return target[name]


ImageClassificationData = make_typefun(
    'ImageClassificationData',
    'image', 'label', 'key'
)
ImageSegmentationData = make_typefun(
    'ImageSegmentationData',
    'image', 'target_image', 'key', 'classes', 'class_weights',
)
MaskedImageSegmentationData = make_typefun(
    'MaskedImageSegmentationData',
    'image', 'label_image', 'mask', 'key', 'classes', 'class_weights',
)
SegmentationDisparityData = make_typefun(
    'SegmentationDisparityData',
    'image', 'disparity_map', 'label_image', 'key', 'classes', 'class_weights',
)
SaliencyData = make_typefun(
    'SaliencyData',
    'image', 'experiments', 'key',
)
SaliencyExperiment = make_typefun(
    'SaliencyExperiment',
    'locations', 'map',
)
UnsupervisedImageData = make_typefun(
    'UnsupervisedImageData',
    'image', 'key',
)
