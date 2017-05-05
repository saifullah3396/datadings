from __future__ import print_function, division

import zipfile
import os.path as pt
from collections import namedtuple

from six import text_type
import numpy as np
import scipy.io as sio

from datadings import ImageWriter
from datadings import Reader


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


class ISUNWriter(ImageWriter):
    pass


def __convert_image(entry):
    image = text_type(entry[0][0][0])
    if not image.endswith('.jpg'):
        image += '.jpg'
    scenecategory = text_type(entry[0][2][0])
    resolution = tuple(entry[0][1][0].tolist()[::-1])
    try:
        experiments = [
            iSUNExperiment(
                subject[0].astype(np.float32).reshape((-1, 2)),  # locations
                subject[1].astype(np.float32).flatten(),  # timestamps
                subject[2].astype(np.float32).reshape((-1, 2)),  # fixations
            )
            for whatever_this_is_thx_iSUN in entry[0][3]
            for subject in whatever_this_is_thx_iSUN
        ]
    except IndexError:
        experiments = []
    return iSUNImage(experiments, resolution, image, scenecategory)


def yield_isun_metadata(matpath):
    data = sio.loadmat(matpath)
    valid = {k: v for k, v in data.items() if not k.startswith('__')}
    if len(valid) > 1:
        raise ValueError('too many keys: %s' % ', '.join(valid))
    images = list(valid.values())[0]
    for entry in images:
        yield __convert_image(entry)


def __write_image(image, imagezip, packer):
    jpegdata = imagezip.read(pt.join('images', image.filename))
    packer.write(jpegdata, image)


def write_isun(indir, outdir):
    import sys
    with zipfile.ZipFile(pt.join(indir, 'image.zip')) as imagezip:
        for name in ('training', 'validation', 'testing'):
            print('%s...' % name, end=' ')
            sys.stdout.flush()
            with ISUNWriter(pt.join(outdir, name + '.msgpack')) as packer:
                for image in yield_isun_metadata(pt.join(indir, name + '.mat')):
                    __write_image(image, imagezip, packer)
            print('done.')


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains iSUN mat and zip files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_isun(args.indir, outdir)


if __name__ == '__main__':
    main()
