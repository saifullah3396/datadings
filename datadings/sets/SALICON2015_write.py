"""Create SALICON 2015 challenge data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- image.zip
- fixations.zip

See also:
    http://salicon.net/challenge-2015/
"""
import os.path as pt
from zipfile import ZipFile
import random

import numpy as np

from ..writer import FileWriter
from . import SaliencyData
from . import SaliencyTimeseriesExperiment
from ..tools import yield_threaded
from ..tools.matlab import loadmat
from ..tools import document_keys


__doc__ += document_keys(
    SaliencyData,
    postfix=document_keys(
        SaliencyTimeseriesExperiment,
        block='',
        prefix='Each experiment has the following keys:'
    )
)


BASE_URL = 'https://drive.google.com/uc?id='
FILES = {
    'images': {
        'path': 'image.zip',
        'url': BASE_URL+'1g8j-hTT-51IG1UFwP0xTGhLdgIUCW5e5&export=download',
        'md5': 'eb2a1bb706633d1b31fc2e01422c5757',
    },
    'fixations': {
        'path': 'fixations.zip',
        'url': BASE_URL+'0B2hsWbciDVedWHFiMUVVWFRZTE0&export=download',
        'md5': '9a22db9d718200fb90252e5010c004c4',
    }
}


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
        yield SaliencyData(key, img, experiments)


def write_set(split, gen, outdir, total):
    with FileWriter(pt.join(outdir, split + '.msgpack'), total=total) as writer:
        for sample in gen:
            writer.write(sample)


def write_sets(files, outdir, args):
    with ZipFile(files['images']['path']) as imagezip, \
            ZipFile(files['fixations']['path']) as fixationzip:
        for split in ('train', 'val', 'test'):
            keys = get_keys(imagezip, split)
            if args.shuffle:
                random.shuffle(keys)
            gen = yield_threaded(yield_samples(keys, imagezip, fixationzip))
            try:
                write_set(split, gen, outdir, len(keys))
            except FileExistsError:
                pass


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
