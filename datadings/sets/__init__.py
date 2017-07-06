from collections import namedtuple

from datadings.reader import MsgpackReader


ClassificationData = namedtuple(
    'ClassificationData',
    ('sample', 'groundtruth', 'filename')
)
SegmentationData = namedtuple(
    'SegmentationData',
    ('sample', 'groundtruth', 'filename', 'classes', 'class_weights')
)
SaliencyData = namedtuple(
    'SaliencyData',
    ('sample', 'groundtruth', 'filename')
)
SaliencyExperiment = namedtuple(
    'SaliencyExperiment',
    ('locations', 'map')
)
UnsupervisedData = namedtuple(
    'UnsupervisedData',
    ('sample', 'filename')
)


def convert_classification(item):
        return ClassificationData(*item[:4])


class ClassificationReader(MsgpackReader):
    _convert = staticmethod(convert_classification)


def convert_segementation(item):
    return SegmentationData(*item[:5])


class SegmentationReader(MsgpackReader):
    _convert = staticmethod(convert_segementation)


def convert_saliency(item):
    return SaliencyData(
            item[0],
            [SaliencyExperiment(*experiment[:2]) for experiment in item[1]],
            item[2],
    )


class SaliencyReader(MsgpackReader):
    _convert = staticmethod(convert_saliency)
