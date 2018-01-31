from __future__ import unicode_literals


def datatype(name, *keys):
    args = ', '.join(keys)
    values = ', '.join('u"{0[0]}":{0[0]}'.format((v,)) for v in keys)
    code = 'def {name}({args}): return {{ {values} }}'\
        .format(name=name.decode('ascii'), args=args, values=values)
    exec(code, {}, globals())


datatype(
    b'ImageClassificationData',
    'image', 'label', 'key',
)
datatype(
    b'ImageSegmentationData',
    'image', 'target_image', 'key', 'classes', 'class_weights',
)
datatype(
    b'MaskedImageSegmentationData',
    'image', 'label_image', 'mask', 'key', 'classes', 'class_weights',
)
datatype(
    b'SegmentationDisparityData',
    'image', 'disparity_map', 'label_image', 'key', 'classes', 'class_weights',
)
datatype(
    b'SaliencyData',
    'image', 'experiments', 'key',
)
datatype(
    b'SaliencyExperiment',
    'locations', 'map',
)
datatype(
    b'UnsupervisedImageData',
    'image', 'key',
)
