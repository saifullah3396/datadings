"""Create FIGRIM Fixation data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- Targets.zip
- allImages_release.mat
- Fillers.zip
- allImages_fillers.mat

See also:
    http://figrim.mit.edu/index_eyetracking.html
"""
import os.path as pt
import zipfile
import random

import numpy as np

from ..writer import FileWriter
from . import SaliencyData
from . import SaliencyExperiment
from ..tools.matlab import loadmat
from ..tools import document_keys


__doc__ += document_keys(
    SaliencyData,
    postfix=document_keys(
        SaliencyExperiment,
        block='',
        prefix='Each experiment has the following keys:'
    )
)


BASE_URL_MIT = 'http://figrim.mit.edu/'
BASE_URL_GIT = 'https://github.com/cvzoya/figrim/raw/master/'
FILES_TARGET = {
    'mat': {
        'path': 'allImages_release.mat',
        'url': BASE_URL_GIT+'targetData/allImages_release.mat',
        'md5': 'c72843b05e95ab27594c1d11c849c897',
    },
    'zip': {
        'path': 'Targets.zip',
        'url': BASE_URL_MIT+'Targets.zip',
        'md5': '2ad3a42ebc377efe4b39064405568201',
    }
}
FILES_FILLER = {
    'mat': {
        'path': 'allImages_fillers.mat',
        'url': BASE_URL_GIT+'fillerData/allImages_fillers.mat',
        'md5': 'ce4f8b4961005d62f7a21191a64cab5e',
    },
    'zip': {
        'path': 'Fillers.zip',
        'url': BASE_URL_MIT+'Fillers.zip',
        'md5': 'dc0bc9561b5bc90e158ec32074dd1060',
    }
}


def __load_mat_file(mat_file):
    mat = loadmat(mat_file)
    valid = {k: v for k, v in mat.items() if not k.startswith('__')}
    if len(valid) > 1:
        raise ValueError('too many keys: %s' % ', '.join(valid))
    files = list(valid.values())[0][0]
    return {str(f[2][0]): f[3][0] for f in files}


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


def write_set(split, files, outdir, args):
    locations = __load_mat_file(files['mat']['path'])
    with zipfile.ZipFile(files['zip']['path']) as imagezip:
        names = [f for f in imagezip.namelist() if f.endswith('.jpg')]
        if args.shuffle:
            random.shuffle(names)
        outfile = pt.join(outdir, split+'.msgpack')
        with FileWriter(outfile, total=len(names),
                        overwrite=args.no_confirm) as writer:
            for path in names:
                jpegdata = imagezip.read(path)
                try:
                    experiments = __get_experiments(locations[path])
                except KeyError:
                    # some images don't have fixation data
                    continue
                item = SaliencyData(path, jpegdata, experiments)
                writer.write(item)


def write_sets(files_target, files_filler, outdir, args):
    for split, files in (('target', files_target), ('filler', files_filler)):
        try:
            write_set(split, files, outdir, args)
        except FileExistsError:
            pass


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files_target = prepare_indir(FILES_TARGET, args)
    files_filler = prepare_indir(FILES_FILLER, args)

    write_sets(files_target, files_filler, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
