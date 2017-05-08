from collections import namedtuple

from datadings.reader import Reader


ClassificationData = namedtuple(
    'ClassificationData',
    ('image', 'groundtruth', 'filename')
)


class ClassificationReader(Reader):
    def _convert(self, item):
        return ClassificationData(*item[:4])


SegmentationData = namedtuple(
    'SegmentationData',
    ('image', 'groundtruth', 'filename')
)


class SegmentationReader(Reader):
    def _convert(self, item):
        return SegmentationData(*item[:4])


SaliencyData = namedtuple(
    'SaliencyData',
    ('image', 'groundtruth', 'filename')
)
SaliencyExperiment = namedtuple(
    'SaliencyExperiment',
    ('locations', 'map')
)


class SaliencyReader(Reader):
    def _convert(self, item):
        return SaliencyData(
            item[0],
            [SaliencyExperiment(experiment[:2]) for experiment in item[1]],
            item[2],
            item[3],
        )
