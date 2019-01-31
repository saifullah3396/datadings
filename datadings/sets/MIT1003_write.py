"""Create MIT1003 data set files.

The data set is described here:
    http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html

This tool will look for the following files in the input directory
and download them if necessary:
    - ALLSTIMULI.zip
    - DATA.zip
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import io
import os
import os.path as pt
import zipfile
import random
from collections import defaultdict

import scipy.io
import numpy as np

from ..writer import FileWriter
from ..tools import IntervalPrinter
from ..tools import download_if_not_found
from . import SaliencyData
from . import SaliencyExperiment


def __iter_fixpoints(datazip, mat_files, stimuluspath):
    stimulus = stimuluspath.split(os.sep)[1]
    for exp in mat_files[stimulus]:
        mat_data = datazip.read(exp)
        buf = io.BytesIO(mat_data)
        mat = [
            v for k, v in scipy.io.loadmat(buf).items()
            if not k.startswith('__')
        ][0]
        try:
            yield mat[0][0][4][0][0][2].astype(np.float32)
        except IndexError:
            yield mat[0][0][0][0][0][2].astype(np.float32)


def write_image(imagezip, datazip, mat_files, stimuluspath, writer):
    stimulusdata = imagezip.read(stimuluspath)
    experiments = [
        SaliencyExperiment(exp, None)
        for exp in __iter_fixpoints(datazip, mat_files, stimuluspath)
    ]
    filename = os.sep.join(stimuluspath.split(os.sep)[-2:])
    item = SaliencyData(
        stimulusdata,
        experiments,
        filename,
    )
    writer.write(item)


def __find_all_experiments(datazip):
    matfiles = [f for f in datazip.namelist() if f.endswith('.mat')]
    mapping = defaultdict(lambda: [])
    for mat in matfiles:
        parts = mat.split(os.sep)
        if len(parts) == 3:
            mapping[parts[2].split('.')[0] + '.jpeg'].append(mat)
    return mapping


def write_sets(indir, outdir, shuffle=True):
    imagepath = pt.join(indir, 'ALLSTIMULI.zip')
    download_if_not_found(
        'http://people.csail.mit.edu/tjudd/WherePeopleLook/ALLSTIMULI.zip',
        imagepath
    )
    datapath = pt.join(indir, 'DATA.zip')
    download_if_not_found(
        'http://people.csail.mit.edu/tjudd/WherePeopleLook/DATA.zip',
        datapath
    )
    printer = IntervalPrinter()
    with zipfile.ZipFile(imagepath) as imagezip:
        with zipfile.ZipFile(datapath) as datazip:
            experiments = __find_all_experiments(datazip)
            with FileWriter(pt.join(outdir, 'MIT1003.msgpack')) as writer:
                names = [f for f in imagezip.namelist() if f.endswith('.jpeg')]
                if shuffle:
                    random.shuffle(names)
                for path in names:
                    write_image(imagezip, datazip, experiments, path, writer)
                    printer.update()
    printer.print_total_updates()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        default='.',
        help='directory that contains MIT1003 archives'
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
