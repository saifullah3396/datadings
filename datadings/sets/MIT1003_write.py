"""Create MIT1003 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- ALLSTIMULI.zip
- DATA.zip

See also:
    http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html
"""
import io
import os
import os.path as pt
from zipfile import ZipFile
import random
from collections import defaultdict

import numpy as np

from ..writer import FileWriter
from ..tools.matlab import loadmat
from . import SaliencyData
from . import SaliencyExperiment
from ..tools import document_keys


__doc__ += document_keys(
    SaliencyData,
    postfix=document_keys(
        SaliencyExperiment,
        block='',
        prefix='Each experiment has the following keys:'
    )
)


BASE_URL = 'http://people.csail.mit.edu/tjudd/WherePeopleLook/'
FILES = {
    'stimuli': {
        'path': 'ALLSTIMULI.zip',
        'url': BASE_URL+'ALLSTIMULI.zip',
        'md5': '0d7df8b954ecba69b6796e77b9afe4b6',
    },
    'data': {
        'path': 'DATA.zip',
        'url': BASE_URL+'DATA.zip',
        'md5': 'ea19d74ad0a0144428c53e9d75c2d71c',
    }
}


def __iter_fixpoints(datazip, mat_files, stimuluspath):
    stimulus = stimuluspath.split(os.sep)[1]
    for exp in mat_files[stimulus]:
        mat_data = datazip.read(exp)
        buf = io.BytesIO(mat_data)
        mat = [
            v for k, v in loadmat(buf).items()
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
        filename,
        stimulusdata,
        experiments,
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


def write_sets(files, outdir, args):
    with ZipFile(files['stimuli']['path']) as imagezip, \
            ZipFile(files['data']['path']) as datazip:
        experiments = __find_all_experiments(datazip)
        names = [f for f in imagezip.namelist() if f.endswith('.jpeg')]
        with FileWriter(pt.join(outdir, 'MIT1003.msgpack'),
                        total=len(names), overwrite=args.no_confirm) as writer:
            if args.shuffle:
                random.shuffle(names)
            for path in names:
                write_image(imagezip, datazip, experiments, path, writer)


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    try:
        write_sets(files, outdir, args)
    except FileExistsError:
        pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
