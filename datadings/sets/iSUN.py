from collections import namedtuple

from datadings.reader import MsgpackReader


iSUNData = namedtuple(
    'iSUNData',
    ('image', 'groundtruth', 'filename', 'scenecategory')
)
iSUNExperiment = namedtuple(
    'iSUNExperiment',
    ('locations', 'map', 'timestamps', 'fixations')
)


def convert_isun(item):
    item = iSUNData(*item)
    for i, experiment in enumerate(item.groundtruth):
        item.groundtruth[i] = iSUNExperiment(*experiment)
    return item


class ISUNReader(MsgpackReader):
    _convert = staticmethod(convert_isun)
