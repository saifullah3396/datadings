"""Create MIT1003 data set files.

Download "Stimuli" and "Eye Tracking Data" listed under "Eye tracking database":
    http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html

Image ZIP-files have to be left as-is."""
from __future__ import print_function, division

import io
import os
import os.path as pt
import zipfile
from collections import defaultdict

import scipy.io
import numpy as np
from PIL import Image

from datadings.writer import ImageWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import SaliencyData
from datadings.sets import SaliencyExperiment


def __load_fixpoints(datazip, mat_files, stimuluspath):
    stimulus = stimuluspath.split(os.sep)[1]
    experiments = []
    for exp in mat_files[stimulus]:
        mat_data = datazip.read(exp)
        buf = io.BytesIO(mat_data)
        mat = [
            v for k, v in scipy.io.loadmat(buf).items()
            if not k.startswith('__')
        ][0]
        try:
            experiments.append(mat[0][0][4][0][0][2].astype(np.float32))
        except IndexError:
            experiments.append(mat[0][0][0][0][0][2].astype(np.float32))
    return experiments


def write_image(imagezip, datazip, mat_files, stimuluspath, writer):
    with imagezip.open(stimuluspath) as f:
        stimulusdata = f.read()
    experiments = [
        SaliencyExperiment(exp, None)
        for exp in __load_fixpoints(datazip, mat_files, stimuluspath)
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


def write_mit1003(indir, outdir):
    printer = FrequencyPrinter()
    with zipfile.ZipFile(pt.join(indir, 'ALLSTIMULI.zip')) as imagezip:
        with zipfile.ZipFile(pt.join(indir, 'DATA.zip')) as datazip:
            experiments = __find_all_experiments(datazip)
            with ImageWriter(pt.join(outdir, 'MIT1003.msgpack')) as writer:
                for path in imagezip.namelist():
                    if path.endswith(os.sep):
                        continue
                    write_image(imagezip, datazip, experiments, path, writer)
                    printer.update()
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
        help='directory that contains CAT2000 archives'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    try:
        write_mit1003(args.indir, outdir)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
