from __future__ import unicode_literals
import inspect


def make_typefun(name, *keys):
    args = ', '.join(keys)
    values = ', '.join('u"{0[0]}":{0[0]}'.format((v,)) for v in keys)
    code = 'def {name}({args}): return {{ {values} }}'\
        .format(name=name.decode('ascii'), args=args, values=values)
    target = inspect.stack()[1][0].f_globals
    exec(code, {}, target)


make_typefun(
    b'ImageClassificationData',
    'image', 'label', 'key',
)
make_typefun(
    b'ImageSegmentationData',
    'image', 'target_image', 'key', 'classes', 'class_weights',
)
make_typefun(
    b'MaskedImageSegmentationData',
    'image', 'label_image', 'mask', 'key', 'classes', 'class_weights',
)
make_typefun(
    b'SegmentationDisparityData',
    'image', 'disparity_map', 'label_image', 'key', 'classes', 'class_weights',
)
make_typefun(
    b'SaliencyData',
    'image', 'experiments', 'key',
)
make_typefun(
    b'SaliencyExperiment',
    'locations', 'map',
)
make_typefun(
    b'UnsupervisedImageData',
    'image', 'key',
)
