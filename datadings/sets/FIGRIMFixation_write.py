"""Create FIGRIM Fixation data set files.

For both target and filler sets, download images and location files:
    http://figrim.mit.edu/index_eyetracking.html

ZIP-files have to be left as-is."""
from __future__ import print_function

import os.path as pt
import zipfile
import random

import numpy as np
import scipy.io
from six import text_type

from datadings.writer import ImageWriter
from datadings.sets import SaliencyData
from datadings.sets import SaliencyExperiment
from datadings.tools import FrequencyPrinter


def __load_mat_file(mat_file):
    mat = scipy.io.loadmat(mat_file)
    valid = {k: v for k, v in mat.items() if not k.startswith('__')}
    if len(valid) > 1:
        raise ValueError('too many keys: %s' % ', '.join(valid))
    files = list(valid.values())[0][0]
    return {
        text_type(f[2][0]): f[3][0] for f in files
    }


def __get_experiments(subjects):
    experiments = []
    for subject in subjects:
        try:
            for locations in subject[4][0][0]:
                experiments.append(
                    SaliencyExperiment(locations.astype(np.float32), None)
                )
        except IndexError:
            pass
    return experiments


def write_images(imagezip, mat_file, writer, shuffle):
    printer = FrequencyPrinter()
    locs = __load_mat_file(mat_file)
    names = imagezip.namelist()
    if shuffle:
        random.shuffle(names)
    for path in names:
        if not path.endswith('.jpg'):
            continue
        jpegdata = imagezip.read(path)
        try:
            experiments = __get_experiments(locs[path])
        except KeyError:
            # some images don't have fixation data
            # print(datapath, 'not found')
            continue
        item = SaliencyData(jpegdata, experiments, path)
        writer.write(item)
        printer.update()


def write_sets(indir, outdir, shuffle=True):
    for name, mat_file in (
            ('Targets', 'allImages_release.mat'),
            ('Fillers', 'allImages_fillers.mat'),
    ):
        print(name)
        with zipfile.ZipFile(pt.join(indir, name + '.zip')) as imagezip:
            with ImageWriter(pt.join(outdir, name + '.msgpack')) as writer:
                mat_file = pt.join(indir, mat_file)
                write_images(imagezip, mat_file, writer, shuffle)
        print('\r%d samples written                       ' % writer.written)


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
