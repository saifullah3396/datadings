"""Create FIGRIM Fixation data set files.

The data set is described here:
    http://figrim.mit.edu/index_eyetracking.html

This tool will look for the following files in the input directory
and download them if necessary:
    - Targets.zip
    - allImages_release.mat
    - Fillers.zip
    - allImages_fillers.mat
"""
import os.path as pt
import zipfile
import random

import numpy as np
import scipy.io

from ..writer import FileWriter
from . import SaliencyData
from . import SaliencyExperiment
from ..tools import download_if_not_found


def __load_mat_file(mat_file):
    mat = scipy.io.loadmat(mat_file)
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


def write_images(imagezip, names, locations, writer, shuffle):
    if shuffle:
        random.shuffle(names)
    for path in names:
        jpegdata = imagezip.read(path)
        try:
            experiments = __get_experiments(locations[path])
        except KeyError:
            # some images don't have fixation data
            # print(datapath, 'not found')
            continue
        item = SaliencyData(jpegdata, experiments, path)
        writer.write(item)


def write_sets(indir, outdir, shuffle=True):
    u = 'http://figrim.mit.edu/'
    g = 'https://github.com/cvzoya/figrim/raw/master/'
    target = 'Targets', 'release', g + 'targetData/allImages_release.mat'
    filler = 'Fillers', 'fillers', g + 'fillerData/allImages_fillers.mat'
    for name, mat_name, mat_url in (target, filler):
        print(name)
        imagepath = pt.join(indir, name + '.zip')
        dataname = 'allImages_%s.mat' % mat_name
        datapath = pt.join(indir, dataname)
        outpath = pt.join(outdir, name.lower() + '.msgpack')
        download_if_not_found(u + name + '.zip', imagepath)
        download_if_not_found(mat_url, datapath)
        locations = __load_mat_file(datapath)
        with zipfile.ZipFile(imagepath) as imagezip:
            names = [f for f in imagezip.namelist() if f.endswith('.jpg')]
            with FileWriter(outpath, total=len(names)) as writer:
                write_images(imagezip, names, locations, writer, shuffle)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains FIGRIM fixation files'
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
