from collections import namedtuple

from datadings.reader import Reader


iSUNImage = namedtuple(
    'iSUNImage',
    ('experiments', 'dimensions', 'filename', 'scenecategory')
)
iSUNExperiment = namedtuple(
    'iSUNExperiment',
    ('locations', 'timestamps', 'fixations')
)


def convert_isun(item):
    jpegdata, image = item
    image = iSUNImage(*image)
    for i, experiment in enumerate(image.experiments):
        image.experiments[i] = iSUNExperiment(*experiment)
    return jpegdata, image


class ISUNReader(Reader):
    _convert = staticmethod(convert_isun)
