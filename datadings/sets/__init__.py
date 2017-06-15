from collections import namedtuple

from datadings.reader import Reader


ClassificationData = namedtuple(
    'ClassificationData',
    ('sample', 'groundtruth', 'filename')
)
SegmentationData = namedtuple(
    'SegmentationData',
    ('sample', 'groundtruth', 'filename')
)
SegmentationMap = namedtuple(
    'SegmentationMap',
    ('map', 'label')
)
SaliencyData = namedtuple(
    'SaliencyData',
    ('sample', 'groundtruth', 'filename')
)
SaliencyExperiment = namedtuple(
    'SaliencyExperiment',
    ('locations', 'map')
)
ANP460Data = namedtuple(
    'ANP460Data',
    ('sample', 'groundtruth', 'filename', 'anp', 'type')
)
ANP460Experiment = namedtuple(
    'ANP460Experiment',
    ('locations', 'map', 'answer')
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
