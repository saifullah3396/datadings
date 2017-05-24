from collections import namedtuple

from datadings.reader import Reader


ClassificationData = namedtuple(
    'ClassificationData',
    ('image', 'groundtruth', 'filename')
)
SegmentationData = namedtuple(
    'SegmentationData',
    ('image', 'groundtruth', 'filename')
)
SaliencyData = namedtuple(
    'SaliencyData',
    ('image', 'groundtruth', 'filename')
)
SaliencyExperiment = namedtuple(
    'SaliencyExperiment',
    ('locations', 'map')
)


def convert_classification(item):
        return ClassificationData(*item[:4])


class ClassificationReader(Reader):
    _convert = staticmethod(convert_classification)


def convert_segementation(item):
    return SegmentationData(*item[:4])


class SegmentationReader(Reader):
    _convert = staticmethod(convert_segementation)


def convert_saliency(item):
    return SaliencyData(
            item[0],
            [SaliencyExperiment(*experiment[:2]) for experiment in item[1]],
            item[2],
    )


class SaliencyReader(Reader):
    _convert = staticmethod(convert_saliency)
