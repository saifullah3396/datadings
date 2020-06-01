"""Create iSUN data set files.

The data set is described here:
    http://lsun.cs.princeton.edu/2016/

This tool will look for the following files in the input directory
and download them if necessary:
    - image.zip
    - training.mat
    - validation.mat
    - testing.mat
"""
import os.path as pt
import zipfile
import random

import numpy as np

from ..writer import FileWriter
from .iSUN import iSUNData
from .iSUN import iSUNExperiment
from ..tools import download_if_not_found


def __convert_item(entry):
    filename = str(entry[0][0][0])
    if not filename.endswith('.jpg'):
        filename += '.jpg'
    scenecategory = str(entry[0][2][0])
    # resolution = tuple(entry[0][1][0].tolist()[::-1])
    try:
        experiments = [
            iSUNExperiment(
                subject[0].astype(np.float32).reshape((-1, 2)),  # locations
                None,
                subject[1].astype(np.float32).flatten(),  # timestamps
                subject[2].astype(np.float32).reshape((-1, 2)),  # fixations
            )
            for whatever_this_is in entry[0][3]
            for subject in whatever_this_is
        ]
    except IndexError:
        experiments = []
    return experiments, filename, scenecategory


def __yield_isun_metadata(matpath, shuffle):
    import scipy.io
    data = scipy.io.loadmat(matpath)
    valid = {k: v for k, v in data.items() if not k.startswith('__')}
    if len(valid) > 1:
        raise ValueError('too many keys: %s' % ', '.join(valid))
    images = list(valid.values())[0]
    if shuffle:
        images = list(images)
        random.shuffle(images)
    for entry in images:
        yield __convert_item(entry)


def __write_image(image, imagezip, writer):
    experiments, filename, scenecategory = image
    jpegdata = imagezip.read(pt.join('images', filename))
    item = iSUNData(jpegdata, experiments, filename, scenecategory)
    writer.write(item)


def write_sets(indir, outdir, shuffle=True):
    url_prefix = 'http://lsun.cs.princeton.edu/challenge/2015/eyetracking/data/'
    imagepath = pt.join(indir, 'image.zip')
    download_if_not_found(url_prefix + 'image.zip', imagepath)
    with zipfile.ZipFile(imagepath) as imagezip:
        for name in ('training', 'validation', 'testing'):
            datapath = pt.join(indir, name + '.mat')
            download_if_not_found(url_prefix + '%s.mat' % name, datapath)
            with FileWriter(pt.join(outdir, name + '.msgpack')) as writer:
                for image in __yield_isun_metadata(datapath, shuffle):
                    __write_image(image, imagezip, writer)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains iSUN files'
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
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
