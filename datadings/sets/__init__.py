def datatype(name, *keys):
    args = ', '.join(keys)
    kwargs = ', '.join('{0[0]}={0[0]}'.format((v,)) for v in keys)
    code = 'def __init__(self, {args}): dict.__init__(self, {kwargs})'\
        .format(name=name, args=args, kwargs=kwargs)
    ns = {}
    exec(code, {}, ns)
    return type(name, (dict,), ns)


ImageClassificationData = datatype(
    'ImageClassificationData',
    'image', 'label', 'key',
)
ImageSegmentationData = datatype(
    'ImageSegmentationData',
    'image', 'target_image', 'key', 'classes', 'class_weights',
)
MaskedImageSegmentationData = datatype(
    'MaskedImageSegmentationData',
    'image', 'label_image', 'mask', 'key', 'classes', 'class_weights',
)
SegmentationDisparityData = datatype(
    'SegmentationDisparityData',
    'image', 'disparity_map', 'label_image', 'key', 'classes', 'class_weights',
)
SaliencyData = datatype(
    'SaliencyData',
    'image', 'experiments', 'key',
)
SaliencyExperiment = datatype(
    'SaliencyExperiment',
    'locations', 'map',
)
UnsupervisedImageData = datatype(
    'UnsupervisedImageData',
    'image', 'key',
)
