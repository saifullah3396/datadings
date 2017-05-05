from collections import namedtuple

from datadings.reader import Reader


ILSVRC2012Image = namedtuple(
    'ILSVRC2012Image',
    ('label', 'dimensions', 'filename')
)


def convert_ilsvrc2012(item):
    jpegdata, image = item
    image = ILSVRC2012Image(*image)
    return jpegdata, image


class ILSVRC2012Reader(Reader):
    _convert = staticmethod(convert_ilsvrc2012)
