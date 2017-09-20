from collections import namedtuple

from datadings.reader import Reader


ANP460Data = namedtuple(
    'ANP460Data',
    ('sample', 'groundtruth', 'filename', 'anp', 'type')
)
ANP460Experiment = namedtuple(
    'ANP460Experiment',
    ('locations', 'map', 'answer', 'duration')
)


def convert_anp460(item):
    return ANP460Data(
            item[0],
            [ANP460Experiment(*experiment[:4]) for experiment in item[1]],
            item[2],
            item[3],
            item[4],
    )


class ANP460Reader(Reader):
    _convert = staticmethod(convert_anp460)
