from collections import namedtuple

from datadings.reader import Reader


SALICONData = namedtuple(
    'SALICONData',
    ('image', 'groundtruth', 'filename')
)
SALICONExperiment = namedtuple(
    'SALICONExperiment',
    ('locations', 'map', 'timestamps', 'fixations')
)


def convert_salicon(item):
    image = SALICONData(*item)
    for i, experiment in enumerate(image.groundtruth):
        image.groundtruth[i] = SALICONExperiment(*experiment)
    return image


class SALICONReader(Reader):
    _convert = staticmethod(convert_salicon)
