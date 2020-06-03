"""Create SALICON 2015 challenge data set files.

The data set is described here:
    http://salicon.net/challenge-2015/

This tool will look for the following files in the input directory
and download them if necessary:
    - image.zip
    - fixations.zip
"""
import os.path as pt
import zipfile
import random

import numpy as np

from ..writer import FileWriter
from . import SaliencyData
from . import SaliencyTimeseriesExperiment
from ..tools import download_if_not_found
from ..tools import yield_threaded
from ..matlab import loadmat


IMAGE_URL = 'https://drive.google.com/uc?id=1g8j-hTT-51IG1UFwP0xTGhLdgIUCW5e5&export=download'
FIXATIONS_URL = 'https://drive.google.com/uc?id=0B2hsWbciDVedWHFiMUVVWFRZTE0&export=download'


def get_keys(imagezip, split):
    keys = [name.replace('.jpg', '').replace('images/', '')
            for name in imagezip.namelist()
            if name.endswith('.jpg')]
    return [key for key in keys if key.startswith(split)]


def yield_samples(keys, imagezip, fixationzip):
    for key in keys:
        img = imagezip.read('images/' + key + '.jpg')
        mat = loadmat(fixationzip.read(key + '.mat'))
        if 'gaze' in mat:
            experiments = [
                SaliencyTimeseriesExperiment(
                    subject[0].astype(np.float32).reshape((-1, 2)),  # locations
                    None,
                    subject[1].astype(np.float32).flatten(),  # timestamps
                    subject[2].astype(np.float32).reshape((-1, 2)),  # fixations
                )
                for subject in mat['gaze'][0]
            ]
        else:
            experiments = []
        yield SaliencyData(img, experiments, key)


def write_set(split, gen, outdir, total):
    with FileWriter(pt.join(outdir, split + '.msgpack'), total=total) as writer:
        for sample in gen:
            writer.write(sample)


def write_sets(indir, outdir, shuffle=True):
    def z(path):
        return zipfile.ZipFile(path)
    imagepath = pt.join(indir, 'image.zip')
    fixationpath = pt.join(indir, 'fixations.zip')
    download_if_not_found(IMAGE_URL, imagepath)
    download_if_not_found(FIXATIONS_URL, fixationpath)
    with z(imagepath) as imagezip, z(fixationpath) as fixationzip:
        for split in ('train', 'val', 'test'):
            print(split)
            keys = get_keys(imagezip, split)
            if shuffle:
                random.shuffle(keys)
            gen = yield_threaded(yield_samples(keys, imagezip, fixationzip))
            write_set(split, gen, outdir, len(keys))


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains SALICON files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--no-shuffle',
        action='store_true',
        help='disable shuffling'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir, not args.no_shuffle)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
