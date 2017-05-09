"""Create SALICON data set files.

Download training, validation, and testing set, and "All Images in JPG":
    http://lsun.cs.princeton.edu/2016/

Image ZIP-file has to be left as-is."""
from __future__ import print_function

import os.path as pt
import sys
import zipfile
import random

import numpy as np
import scipy.io
from six import text_type

from datadings.writer import ImageWriter
from datadings.sets.SALICON import SALICONData
from datadings.sets.SALICON import SALICONExperiment
from datadings.tools import FrequencyPrinter


def __convert_item(entry):
    filename = text_type(entry[0][0])
    if not filename.endswith('.jpg'):
        filename += '.jpg'
    # resolution = tuple(entry[0][1][0].tolist()[::-1])
    try:
        experiments = [
            SALICONExperiment(
                subject[0].astype(np.float32).reshape((-1, 2)),  # locations
                None,
                subject[1].astype(np.float32).flatten(),  # timestamps
                subject[2].astype(np.float32).reshape((-1, 2)),  # fixations
            )
            for whatever_this_is in entry[2]
            for subject in whatever_this_is
        ]
    except IndexError:
        experiments = []
    return experiments, filename


def _yield_salicon_metadata(matpath, shuffle):
    data = scipy.io.loadmat(matpath)
    valid = {k: v for k, v in data.items() if not k.startswith('__')}
    if len(valid) > 1:
        raise ValueError('too many keys: %s' % ', '.join(valid))
    images = list(valid.values())[0][0]
    if shuffle:
        images = list(images)
        random.shuffle(images)
    for entry in images:
        yield __convert_item(entry)


def write_sets(indir, outdir, shuffle=True):
    with zipfile.ZipFile(pt.join(indir, 'image.zip')) as imagezip:
        for name in ('training', 'validation', 'testing'):
            print(name)
            printer = FrequencyPrinter()
            sys.stdout.flush()
            with ImageWriter(pt.join(outdir, name + '.msgpack')) as packer:
                for image in _yield_salicon_metadata(
                        pt.join(indir, name + '.mat'),
                        shuffle,
                ):
                    experiments, filename = image
                    jpegdata = imagezip.read(pt.join('images', filename))
                    item = SALICONData(jpegdata, experiments, filename)
                    packer.write(item)
                    printer.update()
            print('\r%d samples written                       ' % packer.written)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains SALICON mat and zip files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir)


if __name__ == '__main__':
    main()
