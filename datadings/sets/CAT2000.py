from collections import namedtuple

from datadings.reader import Reader


CAT2000Image = namedtuple(
    'CAT2000Image',
    ('locations', 'dimensions', 'filename')
)


def convert_cat2000(item):
    stimulus, response = item
    return stimulus, CAT2000Image(*response)


class CAT2000Reader(Reader):
    _convert = staticmethod(convert_cat2000)
